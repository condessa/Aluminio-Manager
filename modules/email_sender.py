import tempfile, os, base64, hashlib, smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def _credenciais():
    from cryptography.fernet import Fernet
    chave = base64.urlsafe_b64encode(
        hashlib.sha256(b"HCsoftware-AluminioManager-2026-SECRET").digest()
    )
    f = Fernet(chave)
    EMAIL_ENC = 'gAAAAABpsq-YDW-NsN4rYDzPIaBOYukq49w4gIdfKptFhQkaLvlqYMkZKl6No2PxIcL0d4MW518ibCHioY43eoSQbk9O17w7lBNupqHzC-z9F47uVy57ozU='
    SENHA_ENC = 'gAAAAABpsq-YEJdhqO2Srg33taPuR3Uj1NmbqeVh3raQtKHGZ_QelrEjdYcZvCytVn6lGxHErk1anhh_Pzo-PKebgjeoxAX5m8op9k8wZgv80AO-q1H6IPY='
    return f.decrypt(EMAIL_ENC.encode()).decode(), f.decrypt(SENHA_ENC.encode()).decode()

def _transporte(oficina):
    """Escolhe o envio: SMTP da oficina > Google > conta da aplicação."""
    try:
        from modules import smtp_config
        if smtp_config.configurado(oficina):
            return "smtp", smtp_config, smtp_config.valores(oficina)
    except Exception:
        pass
    try:
        from modules import gmail_oauth
        if gmail_oauth.configurado() and gmail_oauth.bibliotecas_instaladas():
            return "google", gmail_oauth, None
    except Exception:
        pass
    user, password = _credenciais()
    return "conta", None, (user, password)


def remetente(oficina):
    modo, modulo, dados = _transporte(oficina)
    if modo == "smtp":
        return (oficina.get("email") or "").strip() or dados["user"]
    if modo == "google":
        return modulo.conta() or (oficina.get("email") or "").strip()
    return dados[0]


def enviar_mensagem(msg, oficina):
    """Envia uma mensagem MIME pelo transporte configurado."""
    modo, modulo, dados = _transporte(oficina)
    if modo == "smtp":
        modulo.enviar(msg, dados)
    elif modo == "google":
        modulo.enviar_mensagem(msg)
    else:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as servidor:
            servidor.login(dados[0], dados[1])
            servidor.send_message(msg)


def _gerar_pdf_bytes(html):
    from PyQt6.QtPrintSupport import QPrinter
    from PyQt6.QtGui import QTextDocument, QPageLayout, QPageSize
    from PyQt6.QtCore import QMarginsF
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    printer.setOutputFileName(tmp.name)
    printer.setPageLayout(QPageLayout(QPageSize(QPageSize.PageSizeId.A4),
                         QPageLayout.Orientation.Portrait, QMarginsF(15,15,15,15)))
    doc = QTextDocument(); doc.setHtml(html); doc.print(printer)
    with open(tmp.name, "rb") as f: pdf_bytes = f.read()
    os.unlink(tmp.name)
    return pdf_bytes

def enviar_orcamento(obra, cliente, oficina, html_orcamento):
    """Envia orçamento por email ao cliente usando conta dedicada da app."""

    email_cli = cliente.get("email","") if cliente else ""
    nome_cli  = cliente.get("nome","")  if cliente else ""
    if not email_cli:
        raise ValueError("O cliente não tem email registado.")

    nome_emp  = oficina.get("nome","Empresa")
    num_obra  = obra.get("numero","")
    descricao = obra.get("descricao","")
    valor     = float(obra.get("valor_orcamento",0) or 0)

    remetente_msg = remetente(oficina)

    # Gerar PDF
    try:
        from modules.pdf_signer import assinar_pdf
        pdf_bytes = assinar_pdf(html_orcamento, obra, oficina)
        print("[EMAIL] PDF assinado digitalmente!")
    except Exception as e:
        print(f"[EMAIL] PDF sem assinatura: {e}")
        pdf_bytes = _gerar_pdf_bytes(html_orcamento)

    corpo_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/></head>
<body style="font-family:Arial,sans-serif;font-size:13px;color:#1a2332;max-width:600px;margin:0 auto;padding:20px;">
  <div style="background:#1a2332;padding:20px 24px;border-radius:8px 8px 0 0;">
    <h2 style="color:#d4560a;margin:0;">⚙️  {nome_emp}</h2>
    <p style="color:rgba(255,255,255,0.6);margin:4px 0 0;font-size:11px;">Orçamento enviado electronicamente</p>
  </div>
  <div style="border:1px solid #e8edf2;border-top:none;padding:24px;border-radius:0 0 8px 8px;">
    <p>Exmo(a). Sr(a). <b>{nome_cli}</b>,</p>
    <p>Conforme combinado, enviamos em anexo o orçamento referente a:</p>
    <div style="background:#f0f4f8;border-left:4px solid #d4560a;padding:12px 16px;margin:16px 0;border-radius:4px;">
      <b style="font-size:14px;">{descricao}</b><br/>
      <span style="color:#6b7c8e;font-size:12px;">Ref: {num_obra}</span><br/>
      <span style="font-size:13px;font-weight:600;color:#1a2332;">Valor: {valor:.2f} €</span>
    </div>
    <p>O orçamento tem validade de <b>30 dias</b> a partir da data de emissão.</p>
    <p>Para qualquer esclarecimento, não hesite em contactar-nos.</p>
    <p>Com os melhores cumprimentos,<br/>
    <b>{oficina.get('responsavel', nome_emp)}</b><br/>
    <span style="color:#6b7c8e;">{nome_emp}</span><br/>
    {"Tel: " + oficina.get('telefone','') + "<br/>" if oficina.get('telefone') else ""}
    </p>
    <hr style="border:none;border-top:1px solid #e8edf2;margin:16px 0;"/>
    <p style="font-size:10px;color:#9aaabb;">
      Este email foi enviado automaticamente pelo AluminioManager by HCsoftware.<br/>
      Data: {date.today().strftime('%d/%m/%Y')}
    </p>
  </div>
</body></html>"""

    msg = MIMEMultipart("mixed")
    msg["From"]    = f"{nome_emp} <{remetente_msg}>"
    msg["To"]      = f"{nome_cli} <{email_cli}>"
    msg["Subject"] = f"Orçamento {num_obra} — {descricao}"
    msg["Reply-To"] = oficina.get("email", smtp_user)

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(corpo_html, "html", "utf-8"))
    msg.attach(alt)

    pdf_part = MIMEApplication(pdf_bytes, _subtype="pdf")
    pdf_part.add_header("Content-Disposition","attachment",
                        filename=f"Orcamento_{num_obra}.pdf")
    msg.attach(pdf_part)

    try:
        enviar_mensagem(msg, oficina)
        print(f"[EMAIL] Orçamento enviado para {email_cli}")
    except smtplib.SMTPAuthenticationError as e:
        raise ValueError("Falha na autenticação do email. Contacte o suporte.") from e
    except Exception as e:
        raise ValueError(f"Erro ao enviar email: {e}") from e

    return email_cli
