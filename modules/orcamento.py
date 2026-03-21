from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QTextBrowser, QMessageBox)
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from PyQt6.QtGui import QTextDocument
from PyQt6.QtCore import Qt
from datetime import date
from db.database import get_connection


def _html_orcamento(obra, cliente, oficina, com_iva=True):
    nome_emp   = oficina.get("nome", "") or ""
    nif_emp    = oficina.get("nif", "") or ""
    morada_emp = oficina.get("morada", "") or ""
    local_emp  = oficina.get("localidade", "") or ""
    tel_emp    = oficina.get("telefone", "") or oficina.get("telemovel", "") or ""
    email_emp  = oficina.get("email", "") or ""
    resp_emp   = oficina.get("responsavel", "") or nome_emp

    nome_cli   = (cliente.get("nome", "") if cliente else "") or "—"
    nif_cli    = (cliente.get("nif", "") if cliente else "") or ""
    morada_cli = (cliente.get("morada", "") if cliente else "") or ""
    local_cli  = (cliente.get("localidade", "") if cliente else "") or ""
    cp_cli     = (cliente.get("cp", "") if cliente else "") or ""
    tel_cli    = (cliente.get("telefone", "") or cliente.get("telemovel", "") if cliente else "") or ""
    email_cli  = (cliente.get("email", "") if cliente else "") or ""

    num        = obra.get("numero", "—") or "—"
    descricao  = obra.get("descricao", "—") or "—"
    morada_ob  = obra.get("morada_obra", "") or ""
    tipo_obra  = obra.get("tipo_obra", "") or ""
    notas      = obra.get("notas", "") or ""
    data_ent   = str(obra.get("data_entrada", date.today()))
    data_prev  = str(obra.get("data_prevista", "")) if obra.get("data_prevista") else ""
    valor_orc  = float(obra.get("valor_orcamento", 0) or 0)
    iva        = valor_orc * 0.23 if com_iva else 0.0
    total      = valor_orc + iva

    def _fmt(d):
        try:
            from datetime import datetime
            return datetime.strptime(str(d), "%Y-%m-%d").strftime("%d/%m/%Y")
        except:
            return str(d)

    # ── Linha de info da empresa (compacta, inline) ───────────────────────
    emp_info_parts = []
    if nif_emp:    emp_info_parts.append(f"NIF: {nif_emp}")
    if morada_emp: emp_info_parts.append(morada_emp)
    if local_emp:  emp_info_parts.append(local_emp)
    if tel_emp:    emp_info_parts.append(f"Tel: {tel_emp}")
    if email_emp:  emp_info_parts.append(email_emp)
    emp_info_inline = "  &middot;  ".join(emp_info_parts)

    cli_lines = f"<b>{nome_cli}</b><br/>"
    if nif_cli:    cli_lines += f"NIF: {nif_cli}<br/>"
    if morada_cli: cli_lines += f"{morada_cli}<br/>"
    if cp_cli or local_cli: cli_lines += f"{(cp_cli+' '+local_cli).strip()}<br/>"
    if tel_cli:    cli_lines += f"Tel: {tel_cli}<br/>"
    if email_cli:  cli_lines += f"{email_cli}"

    det_lines = ""
    if tipo_obra:  det_lines += f"<b>Tipo:</b> {tipo_obra.replace('_',' ').title()}<br/>"
    if morada_ob:  det_lines += f"<b>Local:</b> {morada_ob}<br/>"
    if data_prev:  det_lines += f"<b>Data prevista:</b> {_fmt(data_prev)}<br/>"
    if resp_emp:   det_lines += f"<b>Respons&aacute;vel:</b> {resp_emp}"

    notas_html = f"""<table width="100%" cellpadding="0" cellspacing="0" style="margin-top:10px;">
      <tr><td style="background:#f8fafc;border:1px solid #e8edf2;padding:10px 14px;font-size:10pt;color:#4a6080;">
        <b>Notas:</b><br/>{notas}
      </td></tr></table>""" if notas else ""

    footer_parts = nome_emp
    if nif_emp:   footer_parts += f" &middot; NIF: {nif_emp}"
    if tel_emp:   footer_parts += f" &middot; {tel_emp}"
    if email_emp: footer_parts += f" &middot; {email_emp}"

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/>
<style>
  body {{ font-family: Arial, sans-serif; font-size: 10pt; color: #1a2332; margin: 20px; }}
  h1 {{ font-size: 22pt; font-weight: bold; color: #1a2332; letter-spacing: 3px; margin: 0; }}
  .secao-titulo {{ font-size: 8pt; font-weight: bold; color: #d4560a; letter-spacing: 2px; }}
  .caixa {{ background: #f8fafc; border: 1px solid #e8edf2; padding: 10px 14px; font-size: 10pt; line-height: 1.8; }}
  .obra-caixa {{ background: #f0f4f8; border-left: 4px solid #d4560a; padding: 10px 14px; }}
  table.dados {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
  table.dados thead tr {{ background: #1a2332; color: white; }}
  table.dados thead td {{ padding: 8px 10px; font-weight: bold; font-size: 10pt; }}
  table.dados tbody tr {{ border-bottom: 1px solid #e8edf2; }}
  table.dados tbody td {{ padding: 8px 10px; font-size: 10pt; }}
  .total-linha td {{ padding: 5px 10px; font-size: 10pt; }}
  .total-final td {{ background: #d4560a; color: white; font-weight: bold; font-size: 12pt; padding: 7px 10px; }}
  .validade {{ background: #fff3cd; border: 1px solid #ffc107; padding: 8px 12px; font-size: 9pt; color: #856404; margin-top: 12px; }}
  .footer {{ border-top: 1px solid #e8edf2; padding-top: 8px; font-size: 8pt; color: #9aaabb; text-align: center; margin-top: 16px; }}
</style>
</head><body>

<!-- CABEÇALHO EMPRESA — destaque no topo, centrado -->
<table width="100%" cellpadding="0" cellspacing="0"
       style="background:#1a2332; border-radius:6px; margin-bottom:0; padding:18px 24px;">
  <tr>
    <td align="center">
      <div style="font-size:20pt; font-weight:800; color:#ffffff; letter-spacing:1px;">
        {nome_emp}
      </div>
      <div style="font-size:9pt; color:rgba(255,255,255,0.7); margin-top:5px; line-height:1.8;">
        {emp_info_inline}
      </div>
    </td>
  </tr>
</table>

<!-- LINHA SEPARADORA LARANJA -->
<div style="height:4px; background:#d4560a; margin-bottom:16px;"></div>

<!-- ORÇAMENTO Nº + DATAS -->
<table width="100%" cellpadding="0" cellspacing="0"
       style="border-bottom: 1px solid #e8edf2; padding-bottom: 12px; margin-bottom: 16px;">
  <tr>
    <td width="60%" valign="middle">
      &nbsp;
    </td>
    <td width="40%" valign="top" align="right">
      <h1>OR&Ccedil;AMENTO</h1>
      <div style="font-size:12pt;color:#d4560a;font-weight:bold;">N&ordm; {num}</div>
      <div style="font-size:9pt;color:#6b7c8e;">Data: {_fmt(data_ent)}</div>
      {"<div style='font-size:9pt;color:#6b7c8e;'>Validade: " + _fmt(data_prev) + "</div>" if data_prev else ""}
    </td>
  </tr>
</table>

<!-- CLIENTE + DETALHES -->
<table width="100%" cellpadding="6" cellspacing="0" style="margin-bottom:16px;">
  <tr>
    <td width="48%" valign="top">
      <div class="secao-titulo">CLIENTE</div>
      <div class="caixa" style="margin-top:4px;">{cli_lines}</div>
    </td>
    <td width="4%"></td>
    <td width="48%" valign="top">
      <div class="secao-titulo">DETALHES</div>
      <div class="caixa" style="margin-top:4px;">{det_lines if det_lines else "&nbsp;"}</div>
    </td>
  </tr>
</table>

<!-- DESCRIÇÃO DA OBRA -->
<div class="obra-caixa" style="margin-bottom:16px;">
  <b style="font-size:11pt;">{descricao}</b>
  {"<br/><span style='font-size:9pt;color:#6b7c8e;'>" + notas + "</span>" if notas else ""}
</div>

<!-- TABELA DE ITENS -->
<table class="dados" cellpadding="0" cellspacing="0">
  <thead>
    <tr>
      <td width="50%">Descri&ccedil;&atilde;o</td>
      <td width="15%" align="center">Qtd.</td>
      <td width="17%" align="right">Pre&ccedil;o Unit.</td>
      <td width="18%" align="right">Total</td>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>{descricao}{"<br/><small style='color:#6b7c8e;'>" + tipo_obra.replace("_"," ").title() + "</small>" if tipo_obra else ""}</td>
      <td align="center">1</td>
      <td align="right">{valor_orc:.2f} &euro;</td>
      <td align="right"><b>{valor_orc:.2f} &euro;</b></td>
    </tr>
  </tbody>
</table>

<!-- TOTAIS -->
<table width="260" cellpadding="0" cellspacing="0" align="right" style="margin-top:4px;margin-bottom:16px;">
  <tr class="total-linha"><td>Subtotal:</td><td align="right">{valor_orc:.2f} &euro;</td></tr>
  {"<tr class=\"total-linha\"><td>IVA (23%):</td><td align=\"right\">" + f"{iva:.2f} &euro;" + "</td></tr>" if com_iva else "<tr class=\"total-linha\"><td style=\"color:#1e7e44;\">Isento de IVA</td><td align=\"right\" style=\"color:#1e7e44;\">—</td></tr>"}
  <tr class="total-final"><td><b>TOTAL:</b></td><td align="right"><b>{total:.2f} &euro;</b></td></tr>
</table>

<br clear="all"/>

<!-- VALIDADE -->
<div class="validade">
  <b>Validade do or&ccedil;amento:</b> 30 dias a partir da data de emiss&atilde;o.
</div>

{notas_html}

<!-- ASSINATURAS -->
<table width="100%" cellpadding="0" cellspacing="0" style="margin-top:40px;margin-bottom:20px;">
  <tr>
    <td width="45%" align="center" valign="bottom">
      <div style="border-top:1px solid #1a2332;padding-top:6px;font-size:9pt;color:#4a6080;margin-top:50px;">
        O Cliente<br/>
        <span style="font-size:8pt;color:#9aaabb;">{nome_cli}</span>
      </div>
    </td>
    <td width="10%"></td>
    <td width="45%" align="center" valign="bottom">
      <div style="border-top:1px solid #1a2332;padding-top:6px;font-size:9pt;color:#4a6080;margin-top:50px;">
        Pela Empresa<br/>
        <span style="font-size:8pt;color:#9aaabb;">{resp_emp or nome_emp}</span>
      </div>
    </td>
  </tr>
  <tr>
    <td colspan="3" align="center" style="padding-top:6px;font-size:8pt;color:#9aaabb;">
      Data: _____ / _____ / _________
    </td>
  </tr>
</table>

<!-- RODAPÉ -->
<div class="footer">
  {footer_parts}<br/>
  Documento gerado em {date.today().strftime("%d/%m/%Y")} &middot; Alum&iacute;nios Manager by HCsoftware
</div>

</body></html>"""


class OrcamentoDialog(QDialog):
    def __init__(self, dao, obra, parent=None):
        super().__init__(parent)
        self.dao = dao
        self.obra = obra
        self.html = ""
        self.setWindowTitle(f"Orcamento — {obra['numero']}")
        self.setMinimumSize(720, 600)
        self.resize(760, 720)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        cliente = None
        oficina = {}
        try:
            if self.obra.get("cliente_id"):
                cliente = self.dao.get_cliente(self.obra["cliente_id"])
            conn = get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT chave,valor FROM oficina")
            oficina = {r["chave"]: r["valor"] for r in cur.fetchall()}
            cur.close()
            conn.close()
        except:
            pass

        self.com_iva = True
        self.html = _html_orcamento(self.obra, cliente, oficina, com_iva=True)

        self.browser = QTextBrowser()
        self.browser.setHtml(self.html)
        lay.addWidget(self.browser)

        bw = QWidget()
        bw.setStyleSheet("background:#f8fafc; border-top: 1px solid #c8d4de;")
        bl = QHBoxLayout(bw)
        bl.setContentsMargins(16, 10, 16, 10)
        bl.setSpacing(8)

        from PyQt6.QtWidgets import QCheckBox
        self.chk_iva = QCheckBox("Incluir IVA (23%)")
        self.chk_iva.setChecked(True)
        self.chk_iva.setStyleSheet("font-size:12px;color:#1a2332;font-weight:600;")
        self.chk_iva.stateChanged.connect(self._atualizar)
        bl.addWidget(self.chk_iva)
        bl.addSpacing(12)

        b_email = QPushButton("📧  Enviar por Email")
        b_email.setFixedHeight(36)
        b_email.setStyleSheet("background:#1e7e44;color:white;border:none;border-radius:8px;padding:0 20px;font-weight:600;")
        b_email.clicked.connect(self._enviar_email)
        email_cli = ""
        try:
            if self.obra.get("cliente_id"):
                c = self.dao.get_cliente(self.obra["cliente_id"])
                email_cli = c.get("email","") if c else ""
        except: pass
        if not email_cli:
            b_email.setEnabled(False)
            b_email.setToolTip("Cliente sem email registado")
        else:
            b_email.setToolTip(f"Enviar para {email_cli}")

        b_preview = QPushButton("👁️  Pré-visualizar")
        b_preview.setFixedHeight(36)
        b_preview.setStyleSheet("background:#607d8b;color:white;border:none;border-radius:8px;padding:0 20px;font-weight:600;")
        b_preview.clicked.connect(self._preview)

        b_print = QPushButton("🖨️  Imprimir")
        b_print.setFixedHeight(36)
        b_print.setStyleSheet("background:#d4560a;color:white;border:none;border-radius:8px;padding:0 20px;font-weight:600;")
        b_print.clicked.connect(self._imprimir)

        b_fechar = QPushButton("✕  Fechar")
        b_fechar.setFixedHeight(36)
        b_fechar.setStyleSheet("background:#e8edf2;color:#1a2332;border:none;border-radius:8px;padding:0 20px;font-weight:600;")
        b_fechar.clicked.connect(self.reject)

        bl.addWidget(b_email)
        bl.addWidget(b_preview)
        bl.addWidget(b_print)
        bl.addStretch()
        bl.addWidget(b_fechar)
        lay.addWidget(bw)

    def _atualizar(self):
        com_iva = self.chk_iva.isChecked()
        cliente = None
        oficina = {}
        try:
            if self.obra.get("cliente_id"):
                cliente = self.dao.get_cliente(self.obra["cliente_id"])
            conn = get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT chave,valor FROM oficina")
            oficina = {r["chave"]: r["valor"] for r in cur.fetchall()}
            cur.close(); conn.close()
        except: pass
        self.html = _html_orcamento(self.obra, cliente, oficina, com_iva=com_iva)
        self.browser.setHtml(self.html)

    def _imprimir(self):
        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            from PyQt6.QtGui import QPageLayout
            printer.setPageOrientation(QPageLayout.Orientation.Portrait)
            dlg = QPrintDialog(printer, self)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                doc = QTextDocument()
                doc.setHtml(self.html)
                doc.print(printer)
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def _enviar_email(self):
        try:
            cliente = None
            oficina = {}
            if self.obra.get("cliente_id"):
                cliente = self.dao.get_cliente(self.obra["cliente_id"])
            conn = get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT chave,valor FROM oficina")
            oficina = {r["chave"]: r["valor"] for r in cur.fetchall()}
            cur.close(); conn.close()

            if not oficina.get("smtp_host"):
                QMessageBox.warning(self, "SMTP não configurado",
                    "Configure o servidor de email em\n⚙️ Configurações → Configuração de Email (SMTP)")
                return

            email_cli = cliente.get("email","") if cliente else ""
            r = QMessageBox.question(self, "Enviar Orçamento",
                f"Enviar orçamento {self.obra['numero']} para:\n\n📧  {email_cli}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if r != QMessageBox.StandardButton.Yes: return

            from modules.email_sender import enviar_orcamento
            enviar_orcamento(self.obra, cliente, oficina, self.html)
            QMessageBox.information(self, "✅ Enviado!",
                f"Orçamento enviado com sucesso para:\n{email_cli}")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao enviar", str(e))

    def _preview(self):
        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            preview = QPrintPreviewDialog(printer, self)
            preview.setWindowTitle(f"Pre-visualizacao — {self.obra['numero']}")
            preview.resize(900, 700)

            def _render(p):
                doc = QTextDocument()
                doc.setHtml(self.html)
                doc.print(p)

            preview.paintRequested.connect(_render)
            preview.exec()
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))