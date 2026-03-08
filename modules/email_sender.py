import smtplib
import tempfile
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import date


def _gerar_pdf_bytes(html):
    """Gera PDF a partir do HTML usando Qt"""
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtPrintSupport import QPrinter
    from PyQt6.QtGui import QTextDocument
    from PyQt6.QtCore import QMarginsF
    from PyQt6.QtGui import QPageLayout, QPageSize
    import tempfile

    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)

    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    printer.setOutputFileName(tmp.name)

    layout = QPageLayout(QPageSize(QPageSize.PageSizeId.A4),
                         QPageLayout.Orientation.Portrait,
                         QMarginsF(15, 15, 15, 15))
    printer.setPageLayout(layout)

    doc = QTextDocument()
    doc.setHtml(html)
    doc.print(printer)

    with open(tmp.name, "rb") as f:
        pdf_bytes = f.read()
    os.unlink(tmp.name)
    return pdf_bytes


def enviar_orcamento(obra, cliente, oficina, html_orcamento):
    """Envia orçamento por email ao cliente"""
    smtp_host = oficina.get("smtp_host", "")
    smtp_port = int(oficina.get("smtp_port", 587) or 587)
    smtp_user = oficina.get("smtp_user", "")
    smtp_pass = oficina.get("smtp_pass", "")
    nome_emp  = oficina.get("nome", "Empresa")
    email_emp = oficina.get("email", smtp_user)

    email_cli = cliente.get("email", "") if cliente else ""
    nome_cli  = cliente.get("nome", "") if cliente else ""
    num_obra  = obra.get("numero", "")
    descricao = obra.get("descricao", "")
    valor     = float(obra.get("valor_orcamento", 0) or 0)

    if not smtp_host or not smtp_user or not smtp_pass:
        raise ValueError("Configuração SMTP incompleta. Configure em ⚙️ Configurações.")
    if not email_cli:
        raise ValueError("O cliente não tem email registado.")

    # Gerar PDF assinado digitalmente
    try:
        from modules.pdf_signer import assinar_pdf
        pdf_bytes = assinar_pdf(html_orcamento, obra, oficina)
        print("[EMAIL] PDF assinado digitalmente!")
    except Exception as e:
        print(f"[EMAIL] Aviso: assinatura falhou ({e}), a usar PDF sem assinatura")
        pdf_bytes = _gerar_pdf_bytes(html_orcamento)

    # Corpo do email em HTML
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
    {email_emp}
    </p>
    <hr style="border:none;border-top:1px solid #e8edf2;margin:16px 0;"/>
    <p style="font-size:10px;color:#9aaabb;">
      Este email foi enviado automaticamente pelo Aluminios Manager by HCsoftware.<br/>
      Data: {date.today().strftime('%d/%m/%Y')}
    </p>
  </div>
</body></html>"""

    # Montar email
    msg = MIMEMultipart("mixed")
    msg["From"]    = f"{nome_emp} <{email_emp}>"
    msg["To"]      = f"{nome_cli} <{email_cli}>"
    msg["Subject"] = f"Orçamento {num_obra} — {descricao}"
    msg["Reply-To"] = email_emp

    # Parte HTML
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(corpo_html, "html", "utf-8"))
    msg.attach(alt)

    # PDF em anexo
    pdf_part = MIMEApplication(pdf_bytes, _subtype="pdf")
    pdf_part.add_header("Content-Disposition", "attachment",
                        filename=f"Orcamento_{num_obra}.pdf")
    msg.attach(pdf_part)

    # Enviar
    with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(email_emp, [email_cli], msg.as_string())

    return email_cli
