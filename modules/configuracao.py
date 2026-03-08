from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFormLayout, QWidget, QFrame, QDialogButtonBox,
    QMessageBox, QScrollArea, QTabWidget)
from PyQt6.QtCore import Qt
from db.database import get_connection

CORES={"aco":"#1a2332","laranja":"#d4560a","alum":"#e8edf2","branco":"#f8fafc","cinza":"#6b7c8e"}

def oficina_configurada():
    try:
        conn=get_connection(); cur=conn.cursor(dictionary=True)
        cur.execute("SELECT valor FROM oficina WHERE chave='nome'")
        r=cur.fetchone(); cur.close(); conn.close()
        return bool(r and r["valor"] and r["valor"].strip())
    except: return False

def guardar_oficina(dados):
    conn=get_connection(); cur=conn.cursor()
    for chave,valor in dados.items():
        cur.execute("INSERT INTO oficina (chave,valor) VALUES(%s,%s) ON DUPLICATE KEY UPDATE valor=%s",
            (chave,valor,valor))
    conn.commit(); cur.close(); conn.close()

def gerar_certificado(nome_emp, email_emp):
    """Gera certificado digital auto-assinado para a empresa"""
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.serialization import pkcs12
        import datetime, os

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "PT"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Portugal"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, nome_emp[:63]),
            x509.NameAttribute(NameOID.COMMON_NAME, nome_emp[:63]),
            x509.NameAttribute(NameOID.EMAIL_ADDRESS, email_emp or "geral@empresa.pt"),
        ])
        cert = (x509.CertificateBuilder()
            .subject_name(subject).issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .sign(key, hashes.SHA256(), default_backend()))
        p12 = pkcs12.serialize_key_and_certificates(
            name=nome_emp.encode(),
            key=key, cert=cert, cas=None,
            encryption_algorithm=serialization.BestAvailableEncryption(b"aluminio2026"))
        cert_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cert", "empresa.p12")
        os.makedirs(os.path.dirname(cert_path), exist_ok=True)
        with open(cert_path, "wb") as f: f.write(p12)
        print(f"[CERT] Certificado gerado para: {nome_emp}")
        return True
    except Exception as e:
        print(f"[CERT] Erro ao gerar certificado: {e}")
        return False

def carregar_oficina():
    try:
        conn=get_connection(); cur=conn.cursor(dictionary=True)
        cur.execute("SELECT chave,valor FROM oficina")
        r={row["chave"]:row["valor"] for row in cur.fetchall()}
        cur.close(); conn.close(); return r
    except: return {}


class ConfiguracaoInicialDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AluminioManager — Configuração Inicial")
        self.setFixedSize(520, 560)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        header = QFrame(); header.setStyleSheet(f"background:{CORES['aco']};")
        header.setFixedHeight(130)
        hl = QVBoxLayout(header); hl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t1 = QLabel("⚙️  AluminioManager")
        t1.setStyleSheet("font-size:22px;font-weight:800;color:white;")
        t1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t2 = QLabel("Bem-vindo! Configure os dados da sua empresa.")
        t2.setStyleSheet("font-size:13px;color:rgba(255,255,255,0.7);margin-top:6px;")
        t2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t3 = QLabel("Estes dados aparecerão nos orçamentos impressos.")
        t3.setStyleSheet("font-size:11px;color:rgba(255,255,255,0.5);")
        t3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl.addWidget(t1); hl.addWidget(t2); hl.addWidget(t3)
        lay.addWidget(header)
        fw = QWidget(); fw.setStyleSheet(f"background:{CORES['branco']};")
        fl = QFormLayout(fw); fl.setContentsMargins(32,20,32,16); fl.setSpacing(10)
        self.inp_nome   = QLineEdit(); self.inp_nome.setPlaceholderText("ex: Alumínios Silva, Lda. ou João Silva"); self.inp_nome.setFixedHeight(34)
        self.inp_nif    = QLineEdit(); self.inp_nif.setPlaceholderText("ex: 123456789 (opcional)"); self.inp_nif.setFixedHeight(34)
        self.inp_morada = QLineEdit(); self.inp_morada.setPlaceholderText("ex: Rua Principal, 123"); self.inp_morada.setFixedHeight(34)
        self.inp_local  = QLineEdit(); self.inp_local.setPlaceholderText("ex: Lisboa"); self.inp_local.setFixedHeight(34)
        self.inp_tel    = QLineEdit(); self.inp_tel.setPlaceholderText("ex: 213 456 789"); self.inp_tel.setFixedHeight(34)
        self.inp_tlm    = QLineEdit(); self.inp_tlm.setPlaceholderText("ex: 912 345 678"); self.inp_tlm.setFixedHeight(34)
        self.inp_email  = QLineEdit(); self.inp_email.setPlaceholderText("ex: geral@empresa.pt"); self.inp_email.setFixedHeight(34)
        self.inp_resp   = QLineEdit(); self.inp_resp.setPlaceholderText("ex: João Silva"); self.inp_resp.setFixedHeight(34)
        for lbl,w in [("Nome / Empresa *",self.inp_nome),("NIF",self.inp_nif),
                      ("Morada",self.inp_morada),("Localidade",self.inp_local),
                      ("Telefone",self.inp_tel),("Telemóvel",self.inp_tlm),
                      ("Email",self.inp_email),("Responsável",self.inp_resp),("IBAN",self.inp_iban)]:
            fl.addRow(lbl, w)
        lay.addWidget(fw, stretch=1)
        bw = QWidget(); bw.setStyleSheet(f"background:{CORES['branco']};border-top:1px solid {CORES['alum']};")
        bl = QHBoxLayout(bw); bl.setContentsMargins(32,12,32,16)
        self.lbl_erro = QLabel(""); self.lbl_erro.setStyleSheet("color:red;font-size:12px;")
        btn = QPushButton("✔  Guardar e Continuar")
        btn.setFixedHeight(42)
        btn.setStyleSheet(f"background:{CORES['laranja']};color:white;border:none;border-radius:8px;padding:0 28px;font-weight:700;font-size:14px;")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._guardar)
        bl.addWidget(self.lbl_erro); bl.addStretch(); bl.addWidget(btn)
        lay.addWidget(bw)

    def _guardar(self):
        nome = self.inp_nome.text().strip()
        if not nome:
            self.lbl_erro.setText("⚠️  O nome é obrigatório."); return
        try:
            email = self.inp_email.text().strip()
            guardar_oficina({
                "nome":nome, "nif":self.inp_nif.text().strip(),
                "morada":self.inp_morada.text().strip(), "localidade":self.inp_local.text().strip(),
                "telefone":self.inp_tel.text().strip(), "telemovel":self.inp_tlm.text().strip(),
                "email":email, "responsavel":self.inp_resp.text().strip(), "iban":"",
            })
            gerar_certificado(nome, email)
            self.accept()
        except Exception as e:
            self.lbl_erro.setText(f"Erro: {e}")


class ConfiguracaoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações da Empresa")
        self.setMinimumWidth(520); self.resize(540, 620)
        self._build(); self._preencher()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(20,16,20,16); lay.setSpacing(12)
        titulo = QLabel("🏢  Dados da Empresa / Oficina")
        titulo.setStyleSheet(f"font-size:16px;font-weight:800;color:{CORES['aco']};")
        lay.addWidget(titulo)

        tabs = QTabWidget()

        # --- Tab 1: Empresa ---
        t1 = QWidget(); fl1 = QFormLayout(t1); fl1.setSpacing(10); fl1.setContentsMargins(16,16,16,16)
        self.inp_nome   = QLineEdit(); self.inp_nome.setFixedHeight(34)
        self.inp_nif    = QLineEdit(); self.inp_nif.setFixedHeight(34)
        self.inp_morada = QLineEdit(); self.inp_morada.setFixedHeight(34)
        self.inp_local  = QLineEdit(); self.inp_local.setFixedHeight(34)
        self.inp_tel    = QLineEdit(); self.inp_tel.setFixedHeight(34)
        self.inp_tlm    = QLineEdit(); self.inp_tlm.setFixedHeight(34)
        self.inp_email  = QLineEdit(); self.inp_email.setFixedHeight(34)
        self.inp_resp   = QLineEdit(); self.inp_resp.setFixedHeight(34)
        self.inp_iban   = QLineEdit(); self.inp_iban.setFixedHeight(34)
        self.inp_iban.setPlaceholderText("ex: PT50 0000 0000 0000 0000 0000 0")
        for lbl,w in [("Nome / Empresa *",self.inp_nome),("NIF",self.inp_nif),
                      ("Morada",self.inp_morada),("Localidade",self.inp_local),
                      ("Telefone",self.inp_tel),("Telemóvel",self.inp_tlm),
                      ("Email",self.inp_email),("Responsável",self.inp_resp),("IBAN",self.inp_iban)]:
            fl1.addRow(lbl, w)
        tabs.addTab(t1, "🏢  Empresa")

        # --- Tab 2: Email SMTP ---
        t2 = QWidget(); fl2 = QFormLayout(t2); fl2.setSpacing(10); fl2.setContentsMargins(16,16,16,16)
        info = QLabel("Configure o servidor de email para envio de orçamentos.")
        info.setStyleSheet(f"font-size:11px;color:{CORES['cinza']};")
        info.setWordWrap(True)
        fl2.addRow(info)

        self.inp_smtp_host = QLineEdit(); self.inp_smtp_host.setFixedHeight(34)
        self.inp_smtp_host.setPlaceholderText("ex: smtp.gmail.com")
        self.inp_smtp_port = QLineEdit(); self.inp_smtp_port.setFixedHeight(34)
        self.inp_smtp_port.setPlaceholderText("587")
        self.inp_smtp_user = QLineEdit(); self.inp_smtp_user.setFixedHeight(34)
        self.inp_smtp_user.setPlaceholderText("email@empresa.pt")
        self.inp_smtp_pass = QLineEdit(); self.inp_smtp_pass.setFixedHeight(34)
        self.inp_smtp_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_smtp_pass.setPlaceholderText("palavra-passe ou app password")

        for lbl,w in [("Servidor SMTP",self.inp_smtp_host),("Porta",self.inp_smtp_port),
                      ("Utilizador",self.inp_smtp_user),("Password",self.inp_smtp_pass)]:
            fl2.addRow(lbl, w)

        # Botões
        bts = QWidget(); btsl = QHBoxLayout(bts); btsl.setContentsMargins(0,0,0,0); btsl.setSpacing(8)
        btn_test = QPushButton("🔌  Testar Ligação"); btn_test.setFixedHeight(34)
        btn_test.setStyleSheet(f"background:#607d8b;color:white;border:none;border-radius:8px;padding:0 16px;font-weight:600;")
        btn_test.clicked.connect(self._testar_smtp)
        btn_edit = QPushButton("✏️  Editar campos"); btn_edit.setFixedHeight(34)
        btn_edit.setStyleSheet(f"background:#e8edf2;color:#1a2332;border:1px solid #c8d4de;border-radius:8px;padding:0 16px;font-weight:600;")
        btn_edit.clicked.connect(self._desbloquear_smtp)
        btsl.addWidget(btn_edit); btsl.addWidget(btn_test)
        fl2.addRow("", bts)

        lbl_gmail = QLabel("💡 Gmail: use smtp.gmail.com porta 587 e uma App Password\n    (myaccount.google.com/apppasswords)")
        lbl_gmail.setStyleSheet(f"font-size:10px;color:{CORES['cinza']};")
        fl2.addRow(lbl_gmail)
        tabs.addTab(t2, "📧  Email SMTP")

        lay.addWidget(tabs)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._guardar); bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def _preencher(self):
        d = carregar_oficina()
        self.inp_nome.setText(d.get("nome",""))
        self.inp_nif.setText(d.get("nif",""))
        self.inp_morada.setText(d.get("morada",""))
        self.inp_local.setText(d.get("localidade",""))
        self.inp_tel.setText(d.get("telefone",""))
        self.inp_tlm.setText(d.get("telemovel",""))
        self.inp_email.setText(d.get("email",""))
        self.inp_resp.setText(d.get("responsavel",""))
        self.inp_iban.setText(d.get("iban",""))
        # SMTP — pré-preencher com dados da empresa se não configurado
        smtp_host = d.get("smtp_host","")
        smtp_port = d.get("smtp_port","587")
        smtp_user = d.get("smtp_user","") or d.get("email","")
        smtp_pass = d.get("smtp_pass","")

        self.inp_smtp_host.setText(smtp_host or "smtp.gmail.com")
        self.inp_smtp_port.setText(smtp_port or "587")
        self.inp_smtp_user.setText(smtp_user)
        self.inp_smtp_pass.setText(smtp_pass)

        # Desabilitar campos que não precisam de edição frequente
        if smtp_host:
            self.inp_smtp_host.setEnabled(False)
            self.inp_smtp_host.setStyleSheet("background:#f0f4f8;color:#6b7c8e;")
        if smtp_user:
            self.inp_smtp_user.setEnabled(False)
            self.inp_smtp_user.setStyleSheet("background:#f0f4f8;color:#6b7c8e;")
        if smtp_port:
            self.inp_smtp_port.setEnabled(False)
            self.inp_smtp_port.setStyleSheet("background:#f0f4f8;color:#6b7c8e;")
        # Foco na password
        if not smtp_pass:
            self.inp_smtp_pass.setFocus()

    def _desbloquear_smtp(self):
        estilo_normal = ""
        for w in [self.inp_smtp_host, self.inp_smtp_port, self.inp_smtp_user]:
            w.setEnabled(True)
            w.setStyleSheet(estilo_normal)
        self.inp_smtp_host.setFocus()

    def _testar_smtp(self):
        host = self.inp_smtp_host.text().strip()
        port = int(self.inp_smtp_port.text().strip() or 587)
        user = self.inp_smtp_user.text().strip()
        pwd  = self.inp_smtp_pass.text().strip()
        if not host or not user or not pwd:
            QMessageBox.warning(self,"Erro","Preencha servidor, utilizador e password."); return
        try:
            import smtplib
            with smtplib.SMTP(host, port, timeout=10) as s:
                s.ehlo(); s.starttls(); s.login(user, pwd)
            QMessageBox.information(self,"✅ Sucesso","Ligação SMTP testada com sucesso!")
        except Exception as e:
            QMessageBox.critical(self,"❌ Erro SMTP", str(e))

    def _guardar(self):
        if not self.inp_nome.text().strip():
            QMessageBox.warning(self,"Erro","O nome é obrigatório."); return
        nome = self.inp_nome.text().strip()
        email = self.inp_email.text().strip()
        guardar_oficina({
            "nome":nome, "nif":self.inp_nif.text().strip(),
            "morada":self.inp_morada.text().strip(), "localidade":self.inp_local.text().strip(),
            "telefone":self.inp_tel.text().strip(), "telemovel":self.inp_tlm.text().strip(),
            "email":email, "responsavel":self.inp_resp.text().strip(),
            "smtp_host":self.inp_smtp_host.text().strip(), "smtp_port":self.inp_smtp_port.text().strip(),
            "smtp_user":self.inp_smtp_user.text().strip(), "smtp_pass":self.inp_smtp_pass.text().strip(),
        })
        gerar_certificado(nome, email)
        self.accept()
