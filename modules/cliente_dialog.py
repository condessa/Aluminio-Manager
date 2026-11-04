from modules.validacoes import aplicar_mascara_cp, aplicar_mascara_telefone, aplicar_mascara_nif, aplicar_validacao_email, validar_cp, validar_telefone
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QFrame, QWidget, QMessageBox)
from PyQt6.QtCore import Qt

from modules.temas import PALETA as CORES
def _inp(ph="", max_len=100):
    w = QLineEdit(); w.setPlaceholderText(ph); w.setFixedHeight(34)
    if max_len: w.setMaxLength(max_len)
    w.setStyleSheet(f"background:{CORES['cartao']};color:{CORES['aco']};border:1.5px solid {CORES['alum_mid']};border-radius:6px;padding:2px 8px;font-size:12px;")
    return w

def _lbl(t, bold=False):
    l = QLabel(t)
    l.setStyleSheet(f"font-size:11px;color:{CORES['cinza']};{'font-weight:700;' if bold else ''}")
    return l

class ClienteDialog(QDialog):
    def __init__(self, dao, cliente=None, parent=None):
        super().__init__(parent)
        self.dao     = dao
        self.cliente = cliente
        self.setWindowTitle("Novo Cliente" if not cliente else "Editar Cliente")
        self.setFixedWidth(480)
        self.setModal(True)
        self._build()
        if cliente:
            self._preencher()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        # Cabeçalho
        header = QFrame(); header.setFixedHeight(60)
        header.setStyleSheet("background:#1a2332;")
        hl = QHBoxLayout(header); hl.setContentsMargins(20,0,20,0)
        t = QLabel("👤  " + ("Novo Cliente" if not self.cliente else "Editar Cliente"))
        t.setStyleSheet("font-size:14px;font-weight:800;color:white;background:transparent;")
        hl.addWidget(t)
        lay.addWidget(header)

        sep = QFrame(); sep.setFixedHeight(3)
        sep.setStyleSheet(f"background:{CORES['laranja']};")
        lay.addWidget(sep)

        # Body
        body = QWidget(); body.setStyleSheet(f"background:{CORES['branco']};")
        bl = QVBoxLayout(body); bl.setContentsMargins(24,18,24,18); bl.setSpacing(10)

        frm = QFormLayout(); frm.setSpacing(8); frm.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.inp_nome     = _inp("Nome completo ou empresa")
        self.inp_nif      = _inp("NIF / NIPC", 20)
        self.inp_morada   = _inp("Rua, número...")
        self.inp_local    = _inp("Localidade")
        self.inp_cp       = _inp("0000-000", 8)
        self.inp_tel      = _inp("Telefone fixo", 20)
        self.inp_tlm      = _inp("Telemóvel", 20)
        self.inp_email    = _inp("email@exemplo.pt", 100)
        aplicar_mascara_cp(self.inp_cp)
        aplicar_mascara_telefone(self.inp_tel)
        aplicar_mascara_telefone(self.inp_tlm)
        aplicar_mascara_nif(self.inp_nif)
        aplicar_validacao_email(self.inp_email)

        for lbl, w in [
            ("Nome *",     self.inp_nome),
            ("NIF",        self.inp_nif),
            ("Morada",     self.inp_morada),
            ("Localidade", self.inp_local),
            ("Cód. Postal",self.inp_cp),
            ("Telefone",   self.inp_tel),
            ("Telemóvel",  self.inp_tlm),
            ("Email",      self.inp_email),
        ]:
            frm.addRow(_lbl(lbl, bold=True), w)

        self.inp_notas = QTextEdit()
        self.inp_notas.setPlaceholderText("Observações...")
        self.inp_notas.setFixedHeight(70)
        self.inp_notas.setStyleSheet(
            f"background:{CORES['cartao']};color:{CORES['aco']};border:1.5px solid {CORES['alum_mid']};border-radius:6px;padding:4px 8px;font-size:12px;")
        frm.addRow(_lbl("Notas", bold=True), self.inp_notas)

        bl.addLayout(frm)

        self.lbl_erro = QLabel("")
        self.lbl_erro.setStyleSheet("color:#c0392b;font-size:11px;font-weight:600;")
        self.lbl_erro.setWordWrap(True)
        bl.addWidget(self.lbl_erro)

        lay.addWidget(body)

        # Rodapé
        footer = QFrame()
        footer.setStyleSheet(f"background:{CORES['branco']};border-top:1px solid {CORES['alum']};")
        fl = QHBoxLayout(footer); fl.setContentsMargins(24,12,24,12); fl.setSpacing(10)
        fl.addStretch()

        btn_cancelar = QPushButton("Cancelar"); btn_cancelar.setFixedHeight(36)
        btn_cancelar.setStyleSheet(
            f"background:{CORES['alum']};color:{CORES['aco']};border:none;"
            f"border-radius:6px;padding:0 18px;font-size:12px;font-weight:600;")
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.clicked.connect(self.reject)

        btn_guardar = QPushButton("💾  Guardar"); btn_guardar.setFixedHeight(36)
        btn_guardar.setStyleSheet(
            f"background:{CORES['laranja']};color:white;border:none;"
            f"border-radius:6px;padding:0 18px;font-size:12px;font-weight:700;")
        btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_guardar.clicked.connect(self._guardar)

        fl.addWidget(btn_cancelar); fl.addWidget(btn_guardar)
        lay.addWidget(footer)

    def _preencher(self):
        c = self.cliente
        self.inp_nome.setText(c.get("nome",""))
        self.inp_nif.setText(c.get("nif",""))
        self.inp_morada.setText(c.get("morada",""))
        self.inp_local.setText(c.get("localidade",""))
        self.inp_cp.setText(c.get("cp",""))
        self.inp_tel.setText(c.get("telefone",""))
        self.inp_tlm.setText(c.get("telemovel",""))
        self.inp_email.setText(c.get("email",""))
        self.inp_notas.setPlainText(c.get("notas",""))

    def _guardar(self):
        nome = self.inp_nome.text().strip()
        if not nome:
            self.lbl_erro.setText("⚠️  O nome é obrigatório."); return
        email = self.inp_email.text().strip()
        if email and "@" not in email:
            self.lbl_erro.setText("⚠️  O email não é válido."); return
        tel = self.inp_tel.text().strip()
        if tel and (len(tel) != 9 or not tel.isdigit()):
            self.lbl_erro.setText("⚠️  O telefone deve ter 9 dígitos."); return
        tlm = self.inp_tlm.text().strip()
        if tlm and (len(tlm) != 9 or not tlm.isdigit()):
            self.lbl_erro.setText("⚠️  O telemóvel deve ter 9 dígitos."); return
        cp = self.inp_cp.text().strip()
        if cp and not (len(cp) == 8 and cp[4] == '-'):
            self.lbl_erro.setText("⚠️  O código postal deve ter o formato 0000-000."); return
        d = {
            "nome":      nome,
            "nif":       self.inp_nif.text().strip(),
            "morada":    self.inp_morada.text().strip(),
            "localidade":self.inp_local.text().strip(),
            "cp":        self.inp_cp.text().strip(),
            "telefone":  self.inp_tel.text().strip(),
            "telemovel": self.inp_tlm.text().strip(),
            "email":     self.inp_email.text().strip(),
            "notas":     self.inp_notas.toPlainText().strip(),
        }
        if self.cliente:
            d["id"] = self.cliente["id"]
        try:
            self.dao.salvar_cliente(d)
            self.accept()
        except Exception as e:
            self.lbl_erro.setText(f"❌  Erro ao guardar: {e}")
