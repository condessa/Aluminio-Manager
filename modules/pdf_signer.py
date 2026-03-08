import os
import tempfile
from pyhanko.sign import signers, fields
from pyhanko.sign.fields import SigFieldSpec
from pyhanko import stamp
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign.signers.pdf_signer import PdfSignatureMetadata
from pyhanko_certvalidator import CertificateValidator
import io

CERT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cert", "empresa.p12")
CERT_PASS = b"aluminio2026"


def _gerar_pdf_bytes(html):
    """Gera PDF a partir do HTML usando Qt"""
    from PyQt6.QtPrintSupport import QPrinter
    from PyQt6.QtGui import QTextDocument, QPageLayout, QPageSize
    from PyQt6.QtCore import QMarginsF
    import tempfile, os

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


def assinar_pdf(html, obra, oficina):
    """Gera PDF a partir do HTML e assina digitalmente"""
    if not os.path.exists(CERT_PATH):
        raise FileNotFoundError(f"Certificado não encontrado: {CERT_PATH}")

    # Gerar PDF
    pdf_bytes = _gerar_pdf_bytes(html)

    # Carregar certificado
    with open(CERT_PATH, "rb") as f:
        p12_data = f.read()

    signer = signers.SimpleSigner.load_pkcs12(
        pfx_file=CERT_PATH,
        passphrase=CERT_PASS
    )

    # Metadados da assinatura
    nome_emp = oficina.get("nome", "Empresa")
    resp     = oficina.get("responsavel", nome_emp)
    num_obra = obra.get("numero", "")

    # Escrever PDF com campo de assinatura
    pdf_in = io.BytesIO(pdf_bytes)
    pdf_out = io.BytesIO()

    w = IncrementalPdfFileWriter(pdf_in)

    # Adicionar campo de assinatura invisível
    fields.append_signature_field(
        w,
        SigFieldSpec(
            sig_field_name="Assinatura",
            on_page=0,
            box=(36, 36, 250, 70)  # posição no PDF
        )
    )

    meta = PdfSignatureMetadata(
        field_name="Assinatura",
        name=resp,
        reason=f"Orçamento {num_obra} — {nome_emp}",
        location="Portugal",
        certify=True,
    )

    pdf_signer = signers.PdfSigner(
        meta,
        signer=signer,
        stamp_style=stamp.TextStampStyle(
            stamp_text=f"Assinado digitalmente por\n{resp}\n{nome_emp}",
            background_opacity=0.05,
        )
    )

    pdf_signer.sign_pdf(w, output=pdf_out)
    return pdf_out.getvalue()
