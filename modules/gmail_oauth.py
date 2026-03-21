import os
import json
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "credentials.json")
TOKEN_FILE       = os.path.expanduser("~/.config/aluminio-manager/gmail_token.json")
SCOPES           = ["https://www.googleapis.com/auth/gmail.send", "https://www.googleapis.com/auth/userinfo.email", "openid"]

def _get_service():
    """Obtém serviço Gmail autenticado via OAuth2."""
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = None

    # Carregar token existente
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # Se não há token válido, fazer login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            # Abrir browser em modo incógnito para não mostrar contas do programador
        import webbrowser, subprocess, sys

        # Gerar URL de autorização
        flow.redirect_uri = "http://localhost:0"
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            login_hint=email_hint or "",
            prompt="select_account"
        )

        creds = flow.run_local_server(
            port=0,
            authorization_prompt_message="",
            open_browser=False,
            extra_authorize_kwargs={"login_hint": email_hint or "", "prompt": "select_account"}
        )

        # Guardar token para próxima vez
        os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)

def gmail_configurado():
    """Retorna True se já existe token OAuth2 válido."""
    if not os.path.exists(TOKEN_FILE):
        return False
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if creds and creds.valid:
            return True
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
            return True
    except:
        pass
    return False

def ligar_gmail(email_hint=None):
    """Abre browser para autorizar acesso ao Gmail. Retorna email autorizado."""
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        import json

        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        # Abrir browser em modo incógnito para não mostrar contas do programador
        import webbrowser, subprocess, sys

        # Gerar URL de autorização
        flow.redirect_uri = "http://localhost:0"
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            login_hint=email_hint or "",
            prompt="select_account"
        )

        creds = flow.run_local_server(
            port=0,
            authorization_prompt_message="",
            open_browser=False,
            extra_authorize_kwargs={"login_hint": email_hint or "", "prompt": "select_account"}
        )

        os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

        # Obter email do token
        token_data = json.loads(creds.to_json())
        email = token_data.get("id_token", {})
        # Tentar via userinfo
        import urllib.request, urllib.parse
        req = urllib.request.Request(
            "https://www.googleapis.com/oauth2/v1/userinfo?alt=json",
            headers={"Authorization": f"Bearer {creds.token}"}
        )
        with urllib.request.urlopen(req) as r:
            info = json.loads(r.read())
        return True, info.get("email", "")
    except Exception as e:
        return False, str(e)

def desligar_gmail():
    """Remove token OAuth2."""
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)

def enviar_email(para, assunto, corpo_html=None, corpo_texto=None, anexo_path=None):
    """
    Envia email via Gmail OAuth2.
    Retorna (True, "") ou (False, mensagem_erro)
    """
    try:
        service = _get_service()

        msg = MIMEMultipart("alternative")
        msg["To"]      = para
        msg["Subject"] = assunto

        if corpo_texto:
            msg.attach(MIMEText(corpo_texto, "plain", "utf-8"))
        if corpo_html:
            msg.attach(MIMEText(corpo_html, "html", "utf-8"))

        # Anexo opcional (ex: PDF do orçamento)
        if anexo_path and os.path.exists(anexo_path):
            with open(anexo_path, "rb") as f:
                parte = MIMEBase("application", "octet-stream")
                parte.set_payload(f.read())
            encoders.encode_base64(parte)
            nome_ficheiro = os.path.basename(anexo_path)
            parte.add_header("Content-Disposition", f"attachment; filename={nome_ficheiro}")
            msg.attach(parte)

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return True, ""

    except Exception as e:
        return False, str(e)

def get_email_configurado():
    """Retorna o email Gmail ligado ou None."""
    try:
        if not gmail_configurado():
            return None
        service = _get_service()
        perfil  = service.users().getProfile(userId="me").execute()
        return perfil.get("emailAddress")
    except:
        return None
