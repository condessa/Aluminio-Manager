"""
backup_manager.py — Backup automático da BD antes de desligar
Configura-se automaticamente no primeiro arranque (Linux e Windows)
"""
import os
import sys
import platform
import subprocess
from datetime import datetime
from pathlib import Path

BACKUP_DIR = Path.home() / "Backups" / "aluminio-auto"
LOG_FILE   = BACKUP_DIR / "backup.log"
SCRIPT_DIR = Path(__file__).parent.parent  # raiz do projeto

DB_USER = "aluminio_user"
DB_PASS = "aluminio_pass"
DB_NAME = "aluminio_manager"

def _log(msg):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

def fazer_backup():
    """Executa o backup da BD. Chamado no shutdown ou manualmente."""
    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        data = datetime.now().strftime("%Y%m%d-%H%M%S")
        destino = BACKUP_DIR / f"db-{data}.sql"

        if platform.system() == "Windows":
            cmd = f'mysqldump -u {DB_USER} -p{DB_PASS} {DB_NAME} > "{destino}"'
            subprocess.run(cmd, shell=True, check=True)
        else:
            with open(destino, "w") as f:
                subprocess.run(
                    ["mysqldump", f"-u{DB_USER}", f"-p{DB_PASS}", DB_NAME],
                    stdout=f, check=True, stderr=subprocess.DEVNULL)

        # Manter só os últimos 30 backups
        backups = sorted(BACKUP_DIR.glob("db-*.sql"))
        for antigo in backups[:-30]:
            antigo.unlink()

        _log(f"OK — {destino.name}")
        return True
    except Exception as e:
        _log(f"ERRO — {e}")
        return False

# ── LINUX — systemd ────────────────────────────────────────────────────────

def _script_linux():
    return SCRIPT_DIR / "backup_shutdown.sh"

def _instalar_linux():
    script = _script_linux()
    script.write_text(f"""#!/bin/bash
cd "{SCRIPT_DIR}"
source venv/bin/activate 2>/dev/null || true
python3 -c "from modules.backup_manager import fazer_backup; fazer_backup()"
""")
    script.chmod(0o755)

    service = f"""[Unit]
Description=Aluminio Manager — Backup antes de desligar
DefaultDependencies=no
Before=shutdown.target reboot.target halt.target

[Service]
Type=oneshot
User={os.environ.get('USER', 'herculano')}
ExecStart={script}
TimeoutStartSec=30

[Install]
WantedBy=shutdown.target reboot.target halt.target
"""
    service_path = Path("/etc/systemd/system/aluminio-backup.service")
    try:
        service_path.write_text(service)
        subprocess.run(["systemctl", "enable", "aluminio-backup.service"],
                       check=True, capture_output=True)
        _log("Serviço systemd instalado com sucesso")
        return True
    except PermissionError:
        # Tenta com pkexec (GUI sudo)
        try:
            tmp = Path("/tmp/aluminio-backup.service")
            tmp.write_text(service)
            subprocess.run(["pkexec", "bash", "-c",
                f"cp {tmp} {service_path} && systemctl enable aluminio-backup.service"],
                check=True)
            _log("Serviço systemd instalado via pkexec")
            return True
        except Exception as e:
            _log(f"Não foi possível instalar serviço systemd: {e}")
            return False

def _linux_instalado():
    return Path("/etc/systemd/system/aluminio-backup.service").exists()

# ── WINDOWS — Task Scheduler ───────────────────────────────────────────────

def _instalar_windows():
    try:
        python_exe = sys.executable
        script = SCRIPT_DIR / "backup_shutdown.py"
        script.write_text(f"""import sys
sys.path.insert(0, r"{SCRIPT_DIR}")
from modules.backup_manager import fazer_backup
fazer_backup()
""")
        # Cria tarefa agendada no evento de logoff/shutdown
        cmd = [
            "schtasks", "/create", "/f",
            "/tn", "AluminioManagerBackup",
            "/tr", f'"{python_exe}" "{script}"',
            "/sc", "ONEVENT",
            "/ec", "System",
            "/mo", "*[System[EventID=1074]]",  # evento de shutdown
            "/ru", os.environ.get("USERNAME", ""),
            "/rl", "HIGHEST"
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        _log("Tarefa Windows Task Scheduler instalada")
        return True
    except Exception as e:
        _log(f"Erro ao instalar tarefa Windows: {e}")
        return False

def _windows_instalado():
    try:
        r = subprocess.run(["schtasks", "/query", "/tn", "AluminioManagerBackup"],
                           capture_output=True)
        return r.returncode == 0
    except:
        return False

# ── PONTO DE ENTRADA — chamado no arranque da aplicação ───────────────────

def configurar_backup_automatico():
    """
    Chamado uma vez no arranque. Instala o serviço se ainda não estiver instalado.
    Silencioso — não incomoda o utilizador.
    """
    sistema = platform.system()
    try:
        if sistema == "Linux":
            if not _linux_instalado():
                _instalar_linux()
        elif sistema == "Windows":
            if not _windows_instalado():
                _instalar_windows()
    except Exception as e:
        _log(f"configurar_backup_automatico: {e}")
