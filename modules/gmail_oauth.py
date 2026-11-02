"""Envio de email pela conta Google da oficina (OAuth 2.0).

O utilizador liga a conta uma vez, no browser, e o programa guarda um token
local. A partir daí os orçamentos saem do email da oficina, sem palavras-passe
nem configuração de SMTP.
"""

import base64
import json
import os
from pathlib import Path

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config")) / "aluminio-manager"
TOKEN_FILE = CONFIG_DIR / "gmail_token.json"
INFO_FILE = CONFIG_DIR / "gmail_conta.json"
CREDENCIAIS = Path(__file__).resolve().parent.parent / "credentials.json"


def bibliotecas_instaladas():
    """As bibliotecas Google só são precisas quando o OAuth é usado."""
    try:
        import google.oauth2.credentials  # noqa: F401
        import google_auth_oauthlib.flow  # noqa: F401
        import googleapiclient.discovery  # noqa: F401
        return True
    except Exception:
        return False


def disponivel():
    """True se o pacote traz o cliente OAuth e as bibliotecas necessárias."""
    return CREDENCIAIS.exists() and bibliotecas_instaladas()


def configurado():
    return TOKEN_FILE.exists()


def conta():
    """Email da conta Google ligada (ou vazio)."""
    try:
        return json.loads(INFO_FILE.read_text(encoding="utf-8")).get("email", "")
    except Exception:
        return ""


def _guardar(creds):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    os.chmod(TOKEN_FILE, 0o600)


def _credenciais():
    if not TOKEN_FILE.exists():
        return None
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    try:
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            _guardar(creds)
        return creds if creds and creds.valid else None
    except Exception:
        return None


def _obter_email(creds):
    try:
        import urllib.request

        pedido = urllib.request.Request(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": "Bearer " + creds.token},
        )
        with urllib.request.urlopen(pedido, timeout=10) as resposta:
            return json.loads(resposta.read()).get("email", "")
    except Exception:
        return ""


def autorizar():
    """Abre o browser para a oficina autorizar a sua conta Google."""
    if not disponivel():
        raise RuntimeError(
            "O cliente OAuth não está incluído neste pacote (credentials.json) "
            "ou faltam as bibliotecas Google."
        )
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENCIAIS), SCOPES)
    creds = flow.run_local_server(
        port=0,
        prompt="consent",
        authorization_prompt_message="",
        success_message="Conta ligada ao AluminioManager. Pode fechar esta janela.",
    )
    _guardar(creds)
    email = _obter_email(creds)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    INFO_FILE.write_text(json.dumps({"email": email}), encoding="utf-8")
    return email


def desligar():
    for ficheiro in (TOKEN_FILE, INFO_FILE):
        try:
            ficheiro.unlink()
        except OSError:
            pass


def enviar_mensagem(msg):
    """Envia uma mensagem MIME pela Gmail API, com a conta ligada."""
    creds = _credenciais()
    if creds is None:
        raise RuntimeError("A conta Google da oficina não está ligada.")
    from googleapiclient.discovery import build

    bruto = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    servico = build("gmail", "v1", credentials=creds, cache_discovery=False)
    servico.users().messages().send(userId="me", body={"raw": bruto}).execute()


# ── compatibilidade com a interface usada nas Configurações ──────────────

def gmail_configurado():
    return configurado()


def get_email_configurado():
    return conta()


def ligar_gmail(email_hint=""):
    """Assinatura antiga: devolve (ok, email)."""
    try:
        return True, autorizar()
    except Exception as exc:
        return False, str(exc)


def desligar_gmail():
    desligar()
