from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QWidget, QFrame, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

CORES = {"aco":"#1a2332","laranja":"#d4560a","alum":"#e8edf2","branco":"#f8fafc","cinza":"#6b7c8e"}

class LicencaDialog(QDialog):
    """Diálogo mostrado quando trial expirou ou para activar"""
    def __init__(self, estado, dias=0, parent=None):
        super().__init__(parent)
        self.estado = estado
        self.dias   = dias
        self.setWindowTitle("AluminioManager — Licença")
        self.setFixedSize(480, 560)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        # Cabeçalho
        header = QFrame(); header.setFixedHeight(120)
        header.setStyleSheet(f"background:{CORES['aco']};")
        hl = QVBoxLayout(header); hl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ico = QLabel("⚙️"); ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ico.setStyleSheet("font-size:28px;background:transparent;")
        t1 = QLabel("Aluminios Manager"); t1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t1.setStyleSheet("font-size:18px;font-weight:800;color:white;background:transparent;")
        t2 = QLabel("by HCsoftware"); t2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t2.setStyleSheet("font-size:11px;color:rgba(255,255,255,0.5);background:transparent;")
        hl.addWidget(ico); hl.addWidget(t1); hl.addWidget(t2)
        lay.addWidget(header)

        body = QWidget(); body.setStyleSheet(f"background:{CORES['branco']};")
        bl = QVBoxLayout(body); bl.setContentsMargins(32,24,32,24); bl.setSpacing(14)

        if self.estado == "expirado":
            # Mensagem de expiração
            aviso = QFrame()
            aviso.setStyleSheet("background:#fde8e0;border-radius:10px;border:1px solid #f0b090;")
            al = QVBoxLayout(aviso); al.setContentsMargins(16,12,16,12)
            a1 = QLabel("⏰  Período de avaliação terminado")
            a1.setStyleSheet(f"font-size:14px;font-weight:800;color:{CORES['laranja']};")
            a2 = QLabel("Os seus 15 dias de avaliação gratuita terminaram.\nRegiste a aplicação para continuar a utilizá-la.")
            a2.setWordWrap(True)
            a2.setStyleSheet(f"font-size:12px;color:{CORES['aco']};line-height:1.5;")
            al.addWidget(a1); al.addWidget(a2)
            bl.addWidget(aviso)
        else:
            # Banner trial
            aviso = QFrame()
            aviso.setStyleSheet("background:#fff3cd;border-radius:10px;border:1px solid #ffd060;")
            al = QVBoxLayout(aviso); al.setContentsMargins(16,12,16,12)
            a1 = QLabel(f"⏳  {self.dias} dias restantes de avaliação")
            a1.setStyleSheet("font-size:14px;font-weight:800;color:#b8700a;")
            a2 = QLabel("Registe agora para acesso ilimitado e sem restrições.")
            a2.setStyleSheet("font-size:12px;color:#7a5000;")
            al.addWidget(a1); al.addWidget(a2)
            bl.addWidget(aviso)

        # Preço e pagamento
        # Carregar dados da empresa
        try:
            from db.database import get_connection
            conn = get_connection(); cur = conn.cursor(dictionary=True)
            cur.execute("SELECT chave,valor FROM oficina")
            oficina = {r["chave"]:r["valor"] for r in cur.fetchall()}
            cur.close(); conn.close()
        except: oficina = {}

        telemovel  = oficina.get("telemovel","") or oficina.get("telefone","")
        email_emp  = oficina.get("email","")
        responsavel = oficina.get("responsavel","")
        iban       = oficina.get("iban","PT50 0000 0000 0000 0000 0000 0")

        preco = QFrame()
        preco.setStyleSheet(f"background:{CORES['alum']};border-radius:10px;")
        pl = QVBoxLayout(preco); pl.setContentsMargins(16,14,16,14); pl.setSpacing(6)
        p1 = QLabel("💶  Registo — 20 €  (pagamento único)")
        p1.setStyleSheet(f"font-size:14px;font-weight:800;color:{CORES['aco']};")
        p2 = QLabel(f"Transferência bancária:  {iban}")
        p2.setStyleSheet(f"font-size:11px;color:{CORES['cinza']};")
        p3 = QLabel(f"MBWay:  {telemovel}  —  {responsavel}")
        p3.setStyleSheet(f"font-size:11px;color:{CORES['cinza']};")
        p4 = QLabel(f"Após pagamento envie comprovativo para:  {email_emp}")
        p4.setStyleSheet(f"font-size:11px;color:{CORES['laranja']};font-weight:600;")
        p4.setWordWrap(True)
        pl.addWidget(p1); pl.addWidget(p2); pl.addWidget(p3); pl.addWidget(p4)
        bl.addWidget(preco)

        # Formulário de activação
        fl = QLabel("🔑  Introduza o código de activação recebido por email:")
        fl.setStyleSheet(f"font-size:12px;font-weight:600;color:{CORES['aco']};margin-top:4px;")
        bl.addWidget(fl)

        self.inp_email = QLineEdit(); self.inp_email.setFixedHeight(36)
        self.inp_email.setPlaceholderText("O seu email")
        self.inp_chave = QLineEdit(); self.inp_chave.setFixedHeight(36)
        self.inp_chave.setPlaceholderText("Código de activação (ex: A1B2C3D4...)")
        bl.addWidget(self.inp_email)
        bl.addWidget(self.inp_chave)

        self.lbl_erro = QLabel("")
        self.lbl_erro.setStyleSheet("color:#c0392b;font-size:11px;font-weight:600;")
        bl.addWidget(self.lbl_erro)

        # Botões
        bw = QWidget(); bw.setStyleSheet("background:transparent;")
        btl = QHBoxLayout(bw); btl.setContentsMargins(0,0,0,0); btl.setSpacing(8)

        if self.estado != "expirado":
            btn_depois = QPushButton("Continuar avaliação")
            btn_depois.setFixedHeight(38)
            btn_depois.setStyleSheet(f"background:{CORES['alum']};color:{CORES['aco']};border:none;border-radius:8px;padding:0 16px;font-weight:600;")
            btn_depois.clicked.connect(self.reject)
            btl.addWidget(btn_depois)

        btl.addStretch()
        btn_ativar = QPushButton("✔  Activar Licença")
        btn_ativar.setFixedHeight(38)
        btn_ativar.setStyleSheet(f"background:{CORES['laranja']};color:white;border:none;border-radius:8px;padding:0 20px;font-weight:700;")
        btn_ativar.clicked.connect(self._ativar)
        btl.addWidget(btn_ativar)
        bl.addWidget(bw)

        lay.addWidget(body)

    def _ativar(self):
        email = self.inp_email.text().strip()
        chave = self.inp_chave.text().strip().upper()
        if not email or not chave:
            self.lbl_erro.setText("⚠️  Preencha o email e o código de activação."); return
        self.lbl_erro.setText("⏳  A verificar...")
        from modules.licenca import ativar
        resultado = ativar(email, chave)
        if resultado and resultado.get("ok"):
            QMessageBox.information(self, "✅ Licença Activada",
                "Licença activada com sucesso!\nObrigado por registar o AluminioManager.")
            self.accept()
        else:
            erro = resultado.get("erro","Código inválido ou email incorrecto.") if resultado else "Sem ligação ao servidor."
            self.lbl_erro.setText(f"❌  {erro}")
