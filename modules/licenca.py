import os
import json
import hashlib
import urllib.request
import urllib.error
import uuid
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

SERVIDOR = "https://condessa.pythonanywhere.com"
LICENCA_FILE = os.path.expanduser("~/.config/aluminio-manager/licenca.json")

# ── Dados do programador ──────────────────────────────────────────────────────
EMAIL_PROGRAMADOR = "condessasilva@gmail.com"
SMTP_PROGRAMADOR  = {
    "host": "smtp.gmail.com",
    "port": 587,
    "user": "condessasilva@gmail.com",
    "pass": "kplt lfnc fwen hcaz",
}

def _get_dados_pagamento():
    """Carrega dados de pagamento encriptados"""
    try:
        from cryptography.fernet import Fernet
        base = os.path.dirname(__file__)
        with open(os.path.join(base, ".pagamento.key"), "rb") as fk:
            key = fk.read()
        with open(os.path.join(base, ".pagamento.dat"), "rb") as fd:
            dados_enc = fd.read()
        dados = json.loads(Fernet(key).decrypt(dados_enc))
        return dados.get("iban", "—"), dados.get("mbway", "—")
    except:
        return "—", "—"

def get_machine_id():
    """ID único da máquina"""
    try:
        with open("/etc/machine-id") as f:
            return f.read().strip()
    except:
        return str(uuid.getnode())

def _post(endpoint, dados):
    """Faz POST ao servidor de licenças"""
    url = f"{SERVIDOR}{endpoint}"
    body = json.dumps(dados).encode()
    req = urllib.request.Request(url, data=body,
          headers={"Content-Type":"application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read())
    except:
        return None

def _carregar_local():
    try:
        with open(LICENCA_FILE) as f:
            return json.load(f)
    except:
        return {}

def _guardar_local(dados):
    os.makedirs(os.path.dirname(LICENCA_FILE), exist_ok=True)
    with open(LICENCA_FILE, "w") as f:
        json.dump(dados, f, indent=2)

def inicializar():
    """Regista trial no servidor se for primeira execução"""
    machine_id = get_machine_id()
    resultado = _post("/api/trial", {"machine_id": machine_id})
    if resultado and resultado.get("ok"):
        _guardar_local({
            "machine_id": machine_id,
            "estado": resultado["estado"],
            "dias_restantes": resultado["dias_restantes"],
            "expira": resultado.get("expira",""),
            "ultima_verificacao": datetime.utcnow().isoformat()
        })
        return resultado
    from datetime import timedelta
    expira = (datetime.utcnow() + timedelta(days=15)).isoformat()
    _guardar_local({
        "machine_id": machine_id,
        "estado": "trial",
        "dias_restantes": 15,
        "expira": expira,
        "ultima_verificacao": datetime.utcnow().isoformat()
    })
    return {"ok": True, "estado": "trial", "dias_restantes": 15}

def verificar():
    """Verifica estado da licença — online ou local"""
    machine_id = get_machine_id()
    local = _carregar_local()

    # Se já está activado localmente, não contactar servidor
    if local.get("estado") == "ativo":
        return local

    resultado = _post("/api/verificar", {"machine_id": machine_id})
    if resultado:
        if local.get("estado") == "ativo":
            return local
        dados = {
            "machine_id": machine_id,
            "estado": resultado.get("estado","desconhecido"),
            "dias_restantes": resultado.get("dias_restantes", 0),
            "expira": local.get("expira",""),
            "ultima_verificacao": datetime.utcnow().isoformat()
        }
        _guardar_local(dados)
        return dados

    # Sem internet — usar cache local
    if local:
        try:
            if local.get("estado") != "ativo":
                expira = datetime.fromisoformat(local["expira"])
                dias = max(0, (expira - datetime.utcnow()).days)
                local["dias_restantes"] = dias
                if dias == 0 and local.get("estado") == "trial":
                    local["estado"] = "expirado"
        except:
            pass
        local["offline"] = True
        return local

    return {"estado": "nao_registado", "dias_restantes": 0}

def ativar(email, chave):
    """Activa licença com email e chave"""
    machine_id = get_machine_id()

    resultado = _post("/api/ativar", {
        "machine_id": machine_id,
        "email": email,
        "chave": chave
    })
    if resultado and resultado.get("ok"):
        local = _carregar_local()
        local["estado"] = "ativo"
        local["email"] = email
        _guardar_local(local)
        return resultado

    codigo_esperado = gerar_codigo_activacao(machine_id, email)
    if chave.upper().strip() == codigo_esperado:
        local = _carregar_local()
        local["estado"] = "ativo"
        local["email"] = email
        local["dias_restantes"] = 99999
        _guardar_local(local)
        return {"ok": True}

    return {"ok": False, "erro": "Código inválido ou email incorrecto."}

def gerar_codigo_activacao(machine_id, email):
    """Gera código de activação para uma máquina + email."""
    CHAVE_SECRETA = "HCsoftware-AluminioManager-2026-SECRET"
    raw = f"{machine_id}:{email.lower().strip()}:{CHAVE_SECRETA}"
    h = hashlib.sha256(raw.encode()).hexdigest().upper()
    return f"{h[0:4]}-{h[4:8]}-{h[8:12]}-{h[12:16]}"

def enviar_pedido_licenca(email_cliente, nome_cliente=""):
    """
    Envia email ao programador com Machine ID.
    Envia email ao cliente com instruções de pagamento.
    """
    machine_id = get_machine_id()

    # Obter dados de pagamento encriptados
    iban, mbway = _get_dados_pagamento()

    # Configurar SMTP
    smtp_cfg = None
    try:
        from db.database import get_connection
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT chave,valor FROM oficina")
        oficina = {r["chave"]: r["valor"] for r in cur.fetchall()}
        cur.close(); conn.close()
        if oficina.get("smtp_host") and oficina.get("smtp_user") and oficina.get("smtp_pass"):
            smtp_cfg = {
                "host": oficina["smtp_host"],
                "port": int(oficina.get("smtp_port", 587)),
                "user": oficina["smtp_user"],
                "pass": oficina["smtp_pass"],
            }
    except:
        pass

    if not smtp_cfg:
        smtp_cfg = SMTP_PROGRAMADOR

    data_pedido = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Email ao programador
    corpo_prog = f"""=== PEDIDO DE LICENÇA — AluminioManager ===
Cliente email : {email_cliente}
Nome          : {nome_cliente or "(não fornecido)"}
Machine ID    : {machine_id}
Data pedido   : {data_pedido}
───────────────────────────────────────────
Após confirmação de pagamento, use o gerar_licenca.py:
  python3 gerar_licenca.py {machine_id} {email_cliente}
───────────────────────────────────────────"""

    msg_prog = MIMEText(corpo_prog, "plain", "utf-8")
    msg_prog["Subject"] = f"[AluminioManager] Pedido de Licença — {email_cliente}"
    msg_prog["From"]    = smtp_cfg["user"]
    msg_prog["To"]      = EMAIL_PROGRAMADOR

    # Email ao cliente
    corpo_cli = f"""Olá{" " + nome_cliente if nome_cliente else ""},

Recebemos o seu pedido de licença do AluminioManager.

Para activar a sua licença efectue o pagamento de 50€ por um dos seguintes meios:

  Transferência bancária : {iban}
  MBWay                  : {mbway}

IMPORTANTE: Após o pagamento envie o comprovativo para:
  {EMAIL_PROGRAMADOR}

Após confirmação do pagamento receberá o código de activação por email.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AluminioManager by HCsoftware
Pedido registado em: {data_pedido}
"""

    msg_cli = MIMEText(corpo_cli, "plain", "utf-8")
    msg_cli["Subject"] = "AluminioManager — Instruções de pagamento"
    msg_cli["From"]    = smtp_cfg["user"]
    msg_cli["To"]      = email_cliente

    try:
        with smtplib.SMTP(smtp_cfg["host"], smtp_cfg["port"], timeout=10) as s:
            s.starttls()
            s.login(smtp_cfg["user"], smtp_cfg["pass"])
            s.send_message(msg_prog)
            s.send_message(msg_cli)
        return True, "Pedido enviado! Verifique o seu email para instruções de pagamento."
    except Exception as e:
        pedido = {
            "email":      email_cliente,
            "nome":       nome_cliente,
            "machine_id": machine_id,
            "data":       datetime.now().isoformat()
        }
        pedidos_file = os.path.expanduser("~/.config/aluminio-manager/pedidos_licenca.json")
        try:
            pedidos = []
            if os.path.exists(pedidos_file):
                with open(pedidos_file) as f:
                    pedidos = json.load(f)
            pedidos.append(pedido)
            os.makedirs(os.path.dirname(pedidos_file), exist_ok=True)
            with open(pedidos_file, "w") as f:
                json.dump(pedidos, f, indent=2, ensure_ascii=False)
        except:
            pass
        return False, str(e)

def licenca_valida():
    """Retorna True se pode usar a app (trial válido ou activo)"""
    estado = verificar()
    return estado.get("estado") in ("trial","ativo") and estado.get("dias_restantes",0) > 0
