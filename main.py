"""AluminioManager — Programa principal"""
import sys
import importlib
from PyQt6.QtWidgets import QApplication, QMessageBox, QDialog
from PyQt6.QtGui import QIcon
from db.database import get_connection as conectar, caminho_bd, garantir_schema
import traceback

from modules import registo


def _caminho_icone():
    """Ícone da janela: o da aplicação (janela AM), com o HC como alternativa."""
    from pathlib import Path

    bases = []
    if getattr(sys, "_MEIPASS", None):
        bases.append(Path(sys._MEIPASS))
    aqui = Path(__file__).resolve().parent
    bases += [aqui, aqui / "packaging", aqui / "icons"]
    for nome in ("aluminio_256.png", "aluminio.ico", "hcsoftware.ico", "hcsoftware.png"):
        for base in bases:
            caminho = base / nome
            if caminho.exists():
                return str(caminho)
    return ""


def _erro_global(tipo, valor, tb):
    registo.registar("ERRO NÃO TRATADO:\n" + "".join(traceback.format_exception(tipo, valor, tb)))
    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox
        if QApplication.instance():
            QMessageBox.critical(
                None, "Erro inesperado",
                f"Ocorreu um erro:\n\n{valor}\n\nDetalhes guardados em:\n{registo.ficheiro()}")
    except Exception:
        pass

def inicializar_bd():
    """Cria/verifica o ficheiro SQLite e o schema."""
    print("[DB] A verificar base de dados…")
    caminho = garantir_schema()
    print(f"[DB] Base de dados pronta: {caminho}")


def _verificar_aniversarios(parent):
    from datetime import date, timedelta
    from PyQt6.QtWidgets import QMessageBox
    try:
        from modules.dao import listar_utilizadores
        hoje = date.today()
        amanha = hoje + timedelta(days=1)
        msgs_hoje = []
        msgs_amanha = []
        for f in listar_utilizadores():
            dn = f.get("data_nascimento")
            if not dn or str(dn) == "None": continue
            dn = str(dn)[:10]
            if len(dn) < 10: continue
            try:
                mes, dia = int(dn[5:7]), int(dn[8:10])
                idade = hoje.year - int(dn[:4])
                nome = f.get("nome","")
                if mes == hoje.month and dia == hoje.day:
                    msgs_hoje.append(f"🎂 <b>{nome}</b> faz hoje <b>{idade} anos</b>!")
                elif mes == amanha.month and dia == amanha.day:
                    msgs_amanha.append(f"🎂 <b>{nome}</b> faz amanhã <b>{idade} anos</b>.")
            except: continue
        if msgs_hoje or msgs_amanha:
            texto = ""
            if msgs_hoje:
                texto += "<h3 style='color:#d4560a;'>🎉 Hoje</h3>" + "<br>".join(msgs_hoje)
            if msgs_amanha:
                if texto: texto += "<br><br>"
                texto += "<h3 style='color:#1a56db;'>📅 Amanhã</h3>" + "<br>".join(msgs_amanha)
            msg = QMessageBox(parent)
            msg.setWindowTitle("🎂 Lembretes de Aniversário")
            from PyQt6.QtCore import Qt
            msg.setTextFormat(Qt.TextFormat.RichText)
            msg.setText(texto)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.exec()
    except Exception as e:
        print(f"[Aniversários] Erro: {e}")


def _tem_utilizadores():
    """True se já existe pelo menos uma conta; False numa instalação nova."""
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM utilizadores")
        total = cur.fetchone()[0]
        cur.close(); conn.close()
        return total > 0
    except Exception:
        return True


def _obter_utilizador(username):
    """Vai buscar o utilizador criado no assistente inicial."""
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM utilizadores WHERE username=%s AND ativo=1", (username,))
        user = cur.fetchone()
        cur.close(); conn.close()
        return user
    except Exception:
        return None


def main():
    sys.excepthook = _erro_global
    registo.registar(f"=== Arranque (Python {sys.version.split()[0]}) ===")
    # Configura backup automático silenciosamente
    try:
        from modules.backup_manager import configurar_backup_automatico
        configurar_backup_automatico()
    except Exception:
        pass

    app = QApplication(sys.argv)
    from modules.temas import aplicar_paleta_clara
    aplicar_paleta_clara(app)
    app.setApplicationName("Aluminios Manager by HCsoftware")
    icone = _caminho_icone()
    if icone:
        app.setWindowIcon(QIcon(icone))
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "HCsoftware.AluminioManager")
        except Exception:
            pass
    app.setStyle("Fusion")
    app.setStyleSheet("""
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit {
            background-color: #ffffff; color: #1a2332;
            border: 1px solid #c8d4de; border-radius: 4px;
            padding: 4px 8px; min-height: 26px;
        }
        QLineEdit:focus, QTextEdit:focus, QDateEdit:focus { border-color: #d4560a; }
        QComboBox {
            background-color: #ffffff; color: #1a2332;
            border: 1px solid #c8d4de; border-radius: 4px;
            padding: 4px 8px; min-height: 26px;
        }
        QComboBox:hover { border-color: #d4560a; }
        QComboBox::drop-down { border: none; width: 20px; }
        QComboBox QAbstractItemView {
            background-color: #ffffff; color: #1a2332;
            selection-background-color: #d4560a; selection-color: #ffffff;
            border: 1px solid #c8d4de;
        }
        QTableWidget { gridline-color: #e8edf2; }
        QHeaderView::section {
            background-color: #f0f4f8; color: #1a2332;
            font-weight: 600; padding: 6px;
            border: none; border-bottom: 2px solid #c8d4de;
        }
    """)

    # Inicializar BD
    try:
        inicializar_bd()
    except Exception as e:
        registo.registar_excecao()
        QMessageBox.critical(
            None, "Erro na base de dados",
            f"Não foi possível abrir a base de dados:\n\n{e}\n\nFicheiro:\n{caminho_bd()}")
        sys.exit(1)

    registo.registar("Base de dados ligada")




    # Forçar reload do dao
    import modules.dao as dao
    importlib.reload(dao)

    # Configuração da oficina (primeira execução)
    from modules.configuracao import oficina_configurada, ConfiguracaoInicialDialog
    
    # Verificar se a oficina precisa de configuração
    # Sem contas criadas, é sempre primeira utilização — mesmo que a base de
    # dados já tenha dados da empresa de uma instalação anterior.
    precisa_config = not oficina_configurada() or not _tem_utilizadores()
    registo.registar(f"Primeira configuração necessária: {precisa_config}")
    utilizador_inicial = None

    if precisa_config:
        print("[CONFIG] Primeira execução — a mostrar wizard...")
        cfg = ConfiguracaoInicialDialog()
        if cfg.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)
        # A conta foi criada agora: entrar sem pedir login outra vez.
        utilizador_inicial = getattr(cfg, "utilizador_criado", None)
        registo.registar(f"Configuração inicial concluída (utilizador: {utilizador_inicial})")
        print("[CONFIG] Configuração guardada com sucesso!")
    
    from modules.login import LoginDialog
    from modules.main_window import MainWindow

    while True:
        if utilizador_inicial:
            utilizador = _obter_utilizador(utilizador_inicial)
            utilizador_inicial = None
            if utilizador is None:
                continue  # conta não encontrada: volta ao login normal
        else:
            dlg = LoginDialog()
            if dlg.exec() != QDialog.DialogCode.Accepted:
                break
            utilizador = dlg.utilizador

        # Janela principal
        registo.registar(f"A abrir janela principal (utilizador: {utilizador.get('username','?')})")
        win = MainWindow(utilizador)
        win.show()
        registo.registar("Janela principal aberta")

        # Lembretes de aniversário
        _verificar_aniversarios(win)

        app.exec()

        # Se fechou por logout volta ao login, se fechou normalmente sai
        if not getattr(win, "logout_signal", False):
            break

    sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        _erro_global(*sys.exc_info())
        raise
