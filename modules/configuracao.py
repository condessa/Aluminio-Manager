from modules.validacoes import aplicar_mascara_telefone, aplicar_mascara_nif, aplicar_mascara_iban, aplicar_validacao_email, validar_telefone
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFormLayout, QWidget, QFrame, QDialogButtonBox,
    QMessageBox, QScrollArea, QTabWidget)
from PyQt6.QtCore import Qt
from db.database import get_connection

CORES={"aco":"#1a2332","laranja":"#d4560a","alum":"#e8edf2","branco":"#f8fafc","cinza":"#6b7c8e"}

def oficina_configurada():
    """Verifica se a oficina já foi configurada pelo utilizador"""
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        
        # Verificar se existem campos preenchidos MANUALMENTE
        # (ignorar valores padrão como 'Alumínios')
        cur.execute("""
            SELECT COUNT(*) as total FROM oficina 
            WHERE chave IN ('nome', 'nif', 'morada', 'localidade', 'telefone', 'email')
            AND valor IS NOT NULL 
            AND valor != '' 
            AND valor != 'Alumínios'  # ← Ignorar valor padrão
        """)
        r = cur.fetchone()
        cur.close()
        conn.close()
        
        # Considera configurado se pelo menos 3 campos estiverem preenchidos
        return r and r["total"] >= 3
    except:
        return False

def guardar_oficina(dados):
    conn=get_connection(); cur=conn.cursor()
    for chave,valor in dados.items():
        cur.execute("INSERT INTO oficina (chave,valor) VALUES(%s,%s) "
                    "ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor",
            (chave,valor))
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
        from db.database import pasta_certificado
        cert_path = os.path.join(str(pasta_certificado()), "empresa.p12")
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
        self.utilizador_criado = None
        self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        # ── Cabeçalho ──────────────────────────────────────────────────────
        header = QFrame(); header.setStyleSheet(f"background:{CORES['aco']};")
        header.setFixedHeight(110)
        hl = QVBoxLayout(header); hl.setAlignment(Qt.AlignmentFlag.AlignCenter); hl.setSpacing(2)
        t1 = QLabel("⚙️  AluminioManager")
        t1.setStyleSheet("font-size:20px;font-weight:800;color:white;background:transparent;")
        t1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t2 = QLabel("Bem-vindo! Configure os dados da sua empresa.")
        t2.setStyleSheet("font-size:12px;color:rgba(255,255,255,0.7);background:transparent;")
        t2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl.addWidget(t1); hl.addWidget(t2)
        lay.addWidget(header)

        linha = QFrame(); linha.setFixedHeight(3)
        linha.setStyleSheet(f"background:{CORES['laranja']};")
        lay.addWidget(linha)

        # ── Área scrollável ─────────────────────────────────────────────────
        from PyQt6.QtWidgets import QScrollArea
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"background:{CORES['branco']};border:none;")

        body = QWidget(); body.setStyleSheet(f"background:{CORES['branco']};")
        bl = QVBoxLayout(body); bl.setContentsMargins(28,20,28,16); bl.setSpacing(16)

        # ── Secção 1: Dados da empresa ──────────────────────────────────────
        sec1 = QFrame()
        sec1.setStyleSheet(f"background:{CORES['alum']};border-radius:10px;")
        s1l = QFormLayout(sec1); s1l.setContentsMargins(16,14,16,14); s1l.setSpacing(10)
        lbl_sec1 = QLabel("🏢  Dados da Empresa")
        lbl_sec1.setStyleSheet(f"font-size:12px;font-weight:800;color:{CORES['aco']};")
        s1l.addRow(lbl_sec1)

        def inp(placeholder, h=34):
            w = QLineEdit(); w.setPlaceholderText(placeholder); w.setFixedHeight(h)
            w.setStyleSheet("background:white;border:1.5px solid #c8d4de;border-radius:6px;padding:2px 8px;")
            return w

        self.inp_nome   = inp("ex: Alumínios Silva, Lda.")
        self.inp_nif    = inp("ex: 123456789 (opcional)")
        self.inp_morada = inp("ex: Rua Principal, 123")
        self.inp_local  = inp("ex: Lisboa")
        self.inp_tel    = inp("ex: 282031456")
        self.inp_tlm    = inp("ex: 936258741")
        self.inp_email  = inp("ex: geral@empresa.pt")
        self.inp_resp   = inp("ex: João Silva")
        self.inp_iban   = inp("ex: PT50 0000 0000 0000 0000 0000 0")
        aplicar_validacao_email(self.inp_email)
        aplicar_mascara_telefone(self.inp_tel)
        aplicar_mascara_telefone(self.inp_tlm)
        aplicar_mascara_nif(self.inp_nif)
        aplicar_mascara_iban(self.inp_iban)

        for lbl, w in [("Nome / Empresa *", self.inp_nome), ("NIF", self.inp_nif),
                       ("Morada", self.inp_morada), ("Localidade", self.inp_local),
                       ("Telefone", self.inp_tel), ("Telemóvel", self.inp_tlm),
                       ("Email *", self.inp_email), ("Responsável", self.inp_resp),
                       ("IBAN", self.inp_iban)]:
            lbl_w = QLabel(lbl); lbl_w.setStyleSheet(f"font-size:11px;color:{CORES['aco']};font-weight:600;")
            s1l.addRow(lbl_w, w)
        bl.addWidget(sec1)

        # ── Secção 2: Ligação Gmail OAuth2 ──────────────────────────────
        sec2 = QFrame()
        sec2.setStyleSheet("background:#f0f4f8;border:1.5px solid #c8d4de;border-radius:10px;")
        s2l = QVBoxLayout(sec2); s2l.setContentsMargins(16,14,16,14); s2l.setSpacing(12)

        lbl_sec2 = QLabel("📧  Ligação ao Email da Oficina")
        lbl_sec2.setStyleSheet(f"font-size:12px;font-weight:800;color:{CORES['aco']};")
        s2l.addWidget(lbl_sec2)

        info = QLabel(
            "Para enviar orçamentos e avisos de obras directamente aos seus clientes, "
            "ligue a conta de email da oficina.\n\n"
            "Clique em 'Ligar conta Gmail' — vai abrir o browser para fazer login "
            "na conta Gmail da oficina. Não precisa de passwords nem configurações técnicas.\n\n"
            "⚠️  Pode fazer isto mais tarde em Definições → Configurações."
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            "background:#e8f4fd;border:1px solid #b8d4e8;border-radius:8px;"
            f"padding:10px;font-size:11px;color:{CORES['aco']};")
        s2l.addWidget(info)

        # Estado actual
        from modules.gmail_oauth import gmail_configurado, get_email_configurado
        email_ligado = get_email_configurado()

        self.lbl_gmail_estado = QLabel("")
        self.lbl_gmail_estado.setStyleSheet("font-size:11px;font-weight:600;")
        self.lbl_gmail_estado.setWordWrap(True)

        if email_ligado:
            self.lbl_gmail_estado.setText(f"✅  Conta ligada: {email_ligado}")
            self.lbl_gmail_estado.setStyleSheet("font-size:11px;font-weight:600;color:#1e7e44;")

        btn_row = QWidget(); btn_row.setStyleSheet("background:transparent;")
        btn_lay = QHBoxLayout(btn_row); btn_lay.setContentsMargins(0,0,0,0); btn_lay.setSpacing(8)

        self.btn_ligar_gmail = QPushButton("🔗  Ligar conta Gmail")
        self.btn_ligar_gmail.setFixedHeight(38)
        self.btn_ligar_gmail.setStyleSheet(
            f"background:{CORES['aco']};color:white;border:none;"
            f"border-radius:8px;padding:0 16px;font-weight:700;font-size:12px;")
        self.btn_ligar_gmail.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ligar_gmail.clicked.connect(self._ligar_gmail)

        self.btn_desligar_gmail = QPushButton("✖  Desligar")
        self.btn_desligar_gmail.setFixedHeight(38)
        self.btn_desligar_gmail.setStyleSheet(
            f"background:{CORES['alum']};color:{CORES['aco']};border:none;"
            f"border-radius:8px;padding:0 16px;font-weight:600;font-size:12px;")
        self.btn_desligar_gmail.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_desligar_gmail.setVisible(bool(email_ligado))
        self.btn_desligar_gmail.clicked.connect(self._desligar_gmail)

        btn_lay.addWidget(self.btn_ligar_gmail)
        btn_lay.addWidget(self.btn_desligar_gmail)
        btn_lay.addStretch()
        s2l.addWidget(btn_row)
        s2l.addWidget(self.lbl_gmail_estado)
        bl.addWidget(sec2)
        # ── Secção 3: Utilizador Administrador ─────────────────────────────
        sec3 = QFrame()
        sec3.setStyleSheet(f"background:{CORES['alum']};border-radius:10px;")
        s3l = QFormLayout(sec3); s3l.setContentsMargins(16,14,16,14); s3l.setSpacing(10)
        lbl_sec3 = QLabel("👤  Conta de Administrador")
        lbl_sec3.setStyleSheet(f"font-size:12px;font-weight:800;color:{CORES['aco']};")
        s3l.addRow(lbl_sec3)
        self.inp_admin_nome = inp("Nome completo do administrador")
        self.inp_admin_user = inp("Nome de utilizador (ex: admin)")
        self.inp_admin_pass = inp("Palavra-passe")
        self.inp_admin_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_admin_pass2 = inp("Confirmar palavra-passe")
        self.inp_admin_pass2.setEchoMode(QLineEdit.EchoMode.Password)
        for lbl, w in [("Nome *", self.inp_admin_nome),
                       ("Utilizador *", self.inp_admin_user),
                       ("Palavra-passe *", self.inp_admin_pass),
                       ("Confirmar *", self.inp_admin_pass2)]:
            lbl_w = QLabel(lbl); lbl_w.setStyleSheet(f"font-size:11px;color:{CORES['aco']};font-weight:600;")
            s3l.addRow(lbl_w, w)
        bl.addWidget(sec3)
        bl.addStretch()

        scroll.setWidget(body)

        scroll.setWidget(body)
        lay.addWidget(scroll)

        # ── Rodapé fixo ─────────────────────────────────────────────────────
        footer = QWidget()
        footer.setStyleSheet(f"background:{CORES['branco']};border-top:1px solid {CORES['alum']};")
        fl2 = QHBoxLayout(footer); fl2.setContentsMargins(28,12,28,12)
        self.lbl_erro = QLabel(""); self.lbl_erro.setStyleSheet("color:red;font-size:11px;")
        btn = QPushButton("✔  Guardar e Continuar"); btn.setFixedHeight(42)
        btn.setStyleSheet(
            f"background:{CORES['laranja']};color:white;border:none;"
            f"border-radius:8px;padding:0 28px;font-weight:700;font-size:13px;")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._guardar)
        fl2.addWidget(self.lbl_erro); fl2.addStretch(); fl2.addWidget(btn)
        lay.addWidget(footer)


    def _ligar_gmail(self):
        self.btn_ligar_gmail.setEnabled(False)
        self.btn_ligar_gmail.setText("⏳  A abrir browser...")
        from PyQt6.QtWidgets import QApplication; QApplication.processEvents()
        from modules.gmail_oauth import ligar_gmail
        email_oficina = self.inp_email.text().strip()
        ok, email = ligar_gmail(email_hint=email_oficina)
        if ok:
            self.lbl_gmail_estado.setText(f"✅  Conta ligada: {email}")
            self.lbl_gmail_estado.setStyleSheet("font-size:11px;font-weight:600;color:#1e7e44;")
            self.btn_ligar_gmail.setText("✅  Gmail ligado")
            self.btn_ligar_gmail.setStyleSheet("background:#1e7e44;color:white;border:none;border-radius:8px;padding:0 16px;font-weight:700;font-size:12px;")
            self.btn_desligar_gmail.setVisible(True)
        else:
            self.lbl_gmail_estado.setText("⚠️  Não foi possível ligar. Pode fazê-lo mais tarde em Definições.")
            self.lbl_gmail_estado.setStyleSheet("font-size:11px;font-weight:600;color:#b8700a;")
            self.btn_ligar_gmail.setEnabled(True)
            self.btn_ligar_gmail.setText("🔗  Ligar conta Gmail")

    def _desligar_gmail(self):
        from modules.gmail_oauth import desligar_gmail
        desligar_gmail()
        self.lbl_gmail_estado.setText("⚠️  Conta desligada.")
        self.lbl_gmail_estado.setStyleSheet("font-size:11px;font-weight:600;color:#b8700a;")
        self.btn_ligar_gmail.setEnabled(True)
        self.btn_ligar_gmail.setText("🔗  Ligar conta Gmail")
        self.btn_desligar_gmail.setVisible(False)

    def _ligar_gmail(self):
        self.btn_ligar_gmail.setEnabled(False)
        self.btn_ligar_gmail.setText("⏳  A abrir browser...")
        from PyQt6.QtWidgets import QApplication; QApplication.processEvents()
        from modules.gmail_oauth import ligar_gmail
        email_oficina = self.inp_email.text().strip()
        ok, email = ligar_gmail(email_hint=email_oficina)
        if ok:
            self.lbl_gmail_estado.setText(f"✅  Conta ligada: {email}")
            self.lbl_gmail_estado.setStyleSheet("font-size:11px;font-weight:600;color:#1e7e44;")
            self.btn_ligar_gmail.setText("✅  Gmail ligado")
            self.btn_ligar_gmail.setStyleSheet("background:#1e7e44;color:white;border:none;border-radius:8px;padding:0 16px;font-weight:700;font-size:12px;")
            self.btn_desligar_gmail.setVisible(True)
        else:
            self.lbl_gmail_estado.setText("⚠️  Não foi possível ligar. Pode fazê-lo mais tarde em Definições.")
            self.lbl_gmail_estado.setStyleSheet("font-size:11px;font-weight:600;color:#b8700a;")
            self.btn_ligar_gmail.setEnabled(True)
            self.btn_ligar_gmail.setText("🔗  Ligar conta Gmail")

    def _desligar_gmail(self):
        from modules.gmail_oauth import desligar_gmail
        desligar_gmail()
        self.lbl_gmail_estado.setText("⚠️  Conta desligada.")
        self.lbl_gmail_estado.setStyleSheet("font-size:11px;font-weight:600;color:#b8700a;")
        self.btn_ligar_gmail.setEnabled(True)
        self.btn_ligar_gmail.setText("🔗  Ligar conta Gmail")
        self.btn_desligar_gmail.setVisible(False)

    def _testar_smtp(self):
        email = self.inp_smtp_user.text().strip()
        passwd = self.inp_smtp_pass.text().strip()
        if not email or not passwd:
            self.lbl_smtp_estado.setText("⚠️  Preencha email e password."); 
            self.lbl_smtp_estado.setStyleSheet("color:#b8700a;font-size:11px;font-weight:600;"); return
        self.lbl_smtp_estado.setText("⏳  A testar...")
        self.lbl_smtp_estado.setStyleSheet(f"color:{CORES['cinza']};font-size:11px;")
        from PyQt6.QtWidgets import QApplication; QApplication.processEvents()
        try:
            import smtplib
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as s:
                s.starttls()
                s.login(email, passwd)
            self.lbl_smtp_estado.setText("✅  Ligação OK!")
            self.lbl_smtp_estado.setStyleSheet("color:#1e7e44;font-size:11px;font-weight:600;")
        except Exception as e:
            self.lbl_smtp_estado.setText(f"❌  Erro: {str(e)[:50]}")
            self.lbl_smtp_estado.setStyleSheet("color:#c0392b;font-size:11px;font-weight:600;")

    def _guardar(self):
        nome = self.inp_nome.text().strip()
        if not nome:
            self.lbl_erro.setText("⚠️  O nome da empresa é obrigatório."); return
        email = self.inp_email.text().strip()
        if not email:
            self.lbl_erro.setText("⚠️  O email é obrigatório."); return
        if "@" not in email:
            self.lbl_erro.setText("⚠️  O email não é válido."); return
        tel = self.inp_tel.text().strip()
        if tel and (len(tel) != 9 or not tel.isdigit()):
            self.lbl_erro.setText("⚠️  O telefone deve ter 9 dígitos."); return
        tlm = self.inp_tlm.text().strip()
        if tlm and (len(tlm) != 9 or not tlm.isdigit()):
            self.lbl_erro.setText("⚠️  O telemóvel deve ter 9 dígitos."); return
        # Validar admin
        admin_nome = self.inp_admin_nome.text().strip()
        admin_user = self.inp_admin_user.text().strip()
        admin_pass = self.inp_admin_pass.text()
        admin_pass2 = self.inp_admin_pass2.text()
        if not admin_nome or not admin_user or not admin_pass:
            self.lbl_erro.setText("⚠️  Preencha todos os campos do administrador."); return
        if admin_pass != admin_pass2:
            self.lbl_erro.setText("⚠️  As palavras-passe não coincidem."); return
        if len(admin_pass) < 6:
            self.lbl_erro.setText("⚠️  A palavra-passe deve ter pelo menos 6 caracteres."); return
        try:
            email = self.inp_email.text().strip()
            guardar_oficina({
                "nome":nome, "nif":self.inp_nif.text().strip(),
                "morada":self.inp_morada.text().strip(), "localidade":self.inp_local.text().strip(),
                "telefone":self.inp_tel.text().strip(), "telemovel":self.inp_tlm.text().strip(),
                "email":email, "responsavel":self.inp_resp.text().strip(), "iban":self.inp_iban.text().strip(),
                "smtp_host":"smtp.gmail.com", "smtp_port":"587",
            })
            # Criar utilizador administrador definido pelo utilizador
            from db.database import get_connection, hash_password
            conn2 = get_connection(); cur2 = conn2.cursor()
            cur2.execute("SELECT COUNT(*) FROM utilizadores")
            if cur2.fetchone()[0] == 0:
                cur2.execute("INSERT INTO utilizadores (nome, username, password_hash, perfil, ativo) VALUES (%s,%s,%s,%s,%s)",
                    (admin_nome, admin_user, hash_password(admin_pass), "admin", 1))
                conn2.commit()
                self.utilizador_criado = admin_user
            cur2.close(); conn2.close()
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

    def _desbloquear_smtp(self):
        estilo_normal = ""
        for w in [self.inp_smtp_host, self.inp_smtp_port, self.inp_smtp_user]:
            w.setEnabled(True)
            w.setStyleSheet(estilo_normal)
        self.inp_smtp_host.setFocus()

    def _testar_smtp(self):
        host  = self.inp_smtp_host.text().strip() if hasattr(self, "inp_smtp_host") else "smtp.gmail.com"
        port  = int(self.inp_smtp_port.text().strip() or 587) if hasattr(self, "inp_smtp_port") else 587
        email = self.inp_smtp_user.text().strip()
        passwd = self.inp_smtp_pass.text().strip()
        if not email or not passwd:
            QMessageBox.warning(self, "Aviso", "Preencha o email e a password."); return
        try:
            import smtplib
            from PyQt6.QtWidgets import QApplication; QApplication.processEvents()
            with smtplib.SMTP(host, port, timeout=10) as s:
                s.ehlo(); s.starttls(); s.login(email, passwd)
            QMessageBox.information(self, "✅ Sucesso", "Ligação SMTP testada com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "❌ Erro SMTP", str(e))

    def _guardar(self):
        if not self.inp_nome.text().strip():
            QMessageBox.warning(self,"Erro","O nome é obrigatório."); return
        nome = self.inp_nome.text().strip()
        email = self.inp_email.text().strip()
        if email and "@" not in email:
            QMessageBox.warning(self,"Erro","O email não é válido."); return
        tel = self.inp_tel.text().strip()
        if tel and (len(tel) != 9 or not tel.isdigit()):
            QMessageBox.warning(self,"Erro","O telefone deve ter 9 dígitos."); return
        tlm = self.inp_tlm.text().strip()
        if tlm and (len(tlm) != 9 or not tlm.isdigit()):
            QMessageBox.warning(self,"Erro","O telemóvel deve ter 9 dígitos."); return
        guardar_oficina({
            "nome":nome, "nif":self.inp_nif.text().strip(),
            "morada":self.inp_morada.text().strip(), "localidade":self.inp_local.text().strip(),
            "telefone":self.inp_tel.text().strip(), "telemovel":self.inp_tlm.text().strip(),
            "email":email, "responsavel":self.inp_resp.text().strip(),
            "iban":self.inp_iban.text().strip() if hasattr(self,"inp_iban") else "",
        })
        gerar_certificado(nome, email)
        self.accept()
