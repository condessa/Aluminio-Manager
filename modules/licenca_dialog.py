from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QWidget, QFrame, QMessageBox, QScrollArea)
from PyQt6.QtCore import Qt

CORES = {"aco":"#1a2332","laranja":"#d4560a","alum":"#e8edf2","branco":"#f8fafc","cinza":"#6b7c8e"}

def _lbl(texto, estilo):
    l = QLabel(texto); l.setStyleSheet(estilo); l.setWordWrap(True); return l

class LicencaDialog(QDialog):
    def __init__(self, estado, dias=0, parent=None):
        super().__init__(parent)
        self.estado = estado; self.dias = dias
        self.setWindowTitle("AluminioManager — Licença")
        self.setMinimumSize(490, 680)
        self.resize(490, 780)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint)
        self._carregar_oficina(); self._build()

    def _carregar_oficina(self):
        self.oficina = {}
        try:
            from db.database import get_connection
            conn = get_connection(); cur = conn.cursor(dictionary=True)
            cur.execute("SELECT chave,valor FROM oficina")
            self.oficina = {r["chave"]:r["valor"] for r in cur.fetchall()}
            cur.close(); conn.close()
        except: pass

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        # ── Cabeçalho fixo ─────────────────────────────────────────────────
        header = QFrame(); header.setFixedHeight(110)
        header.setStyleSheet(f"background:{CORES['aco']};")
        hl = QVBoxLayout(header); hl.setAlignment(Qt.AlignmentFlag.AlignCenter); hl.setSpacing(2)
        ico = QLabel("⚙️"); ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ico.setStyleSheet("font-size:26px;background:transparent;")
        t1 = QLabel("Aluminios Manager"); t1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t1.setStyleSheet("font-size:17px;font-weight:800;color:white;background:transparent;")
        t2 = QLabel("by HCsoftware"); t2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t2.setStyleSheet("font-size:10px;color:rgba(255,255,255,0.5);background:transparent;")
        hl.addWidget(ico); hl.addWidget(t1); hl.addWidget(t2)
        lay.addWidget(header)

        linha = QFrame(); linha.setFixedHeight(3)
        linha.setStyleSheet(f"background:{CORES['laranja']};")
        lay.addWidget(linha)

        # ── Área scrollável ────────────────────────────────────────────────
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"background:{CORES['branco']};border:none;")

        body = QWidget(); body.setStyleSheet(f"background:{CORES['branco']};")
        bl = QVBoxLayout(body); bl.setContentsMargins(28,20,28,16); bl.setSpacing(14)

        # ── Banner trial/expirado ──────────────────────────────────────────
        if self.estado == "expirado":
            aviso = QFrame()
            aviso.setStyleSheet("background:#fde8e0;border-radius:10px;border:1px solid #f0b090;")
            al = QVBoxLayout(aviso); al.setContentsMargins(14,10,14,10); al.setSpacing(4)
            al.addWidget(_lbl("⏰  Período de avaliação terminado",
                              f"font-size:13px;font-weight:800;color:{CORES['laranja']};"))
            al.addWidget(_lbl("Os seus 15 dias de avaliação gratuita terminaram.\nRegiste a aplicação para continuar.",
                              f"font-size:11px;color:{CORES['aco']};"))
        else:
            aviso = QFrame()
            aviso.setStyleSheet("background:#fff3cd;border-radius:10px;border:1px solid #ffd060;")
            al = QVBoxLayout(aviso); al.setContentsMargins(14,10,14,10); al.setSpacing(4)
            al.addWidget(_lbl(f"⏳  {self.dias} dias restantes de avaliação",
                              "font-size:13px;font-weight:800;color:#b8700a;"))
            al.addWidget(_lbl("Registe agora para acesso ilimitado e sem restrições.",
                              "font-size:11px;color:#7a5000;"))
        bl.addWidget(aviso)

        # ── Preço e pagamento ──────────────────────────────────────────────
        from modules.licenca import _get_dados_pagamento
        iban, telemovel = _get_dados_pagamento()

        preco = QFrame(); preco.setStyleSheet(f"background:{CORES['alum']};border-radius:10px;")
        pl = QVBoxLayout(preco); pl.setContentsMargins(14,12,14,12); pl.setSpacing(5)
        pl.addWidget(_lbl("💶  Registo — 50 €  (pagamento único)",
                          f"font-size:13px;font-weight:800;color:{CORES['aco']};"))
        pl.addWidget(_lbl(f"Transferência:  {iban}",
                          f"font-size:11px;color:{CORES['cinza']};"))
        pl.addWidget(_lbl(f"MBWay:  {telemovel}",
                          f"font-size:11px;color:{CORES['cinza']};"))
        pl.addWidget(_lbl("Após pagamento clique em 'Pedir Licença' abaixo.",
                          f"font-size:11px;color:{CORES['laranja']};font-weight:600;"))
        bl.addWidget(preco)

        # ── PASSO 1 ────────────────────────────────────────────────────────
        passo1 = QFrame()
        passo1.setStyleSheet("background:#f0f4f8;border:1.5px solid #c8d4de;border-radius:10px;")
        p1l = QVBoxLayout(passo1); p1l.setContentsMargins(16,14,16,14); p1l.setSpacing(10)

        p1l.addWidget(_lbl("① Pedir código de activação",
                           f"font-size:12px;font-weight:800;color:{CORES['aco']};"))
        p1l.addWidget(_lbl("Verifique os dados e clique 'Pedir Licença'.",
                           f"font-size:10px;color:{CORES['cinza']};"))

        email_auto = self.oficina.get("email","") or ""
        nome_auto  = self.oficina.get("responsavel","") or self.oficina.get("nome","") or ""

        self.inp_email = QLineEdit(); self.inp_email.setFixedHeight(38)
        self.inp_email.setPlaceholderText("Email de contacto")
        self.inp_email.setText(email_auto)

        self.inp_nome = QLineEdit(); self.inp_nome.setFixedHeight(38)
        self.inp_nome.setPlaceholderText("Nome / Empresa")
        self.inp_nome.setText(nome_auto)

        estilo_auto   = ("border:1.5px solid #1e7e44;border-radius:6px;padding:4px 10px;"
                         "background:#f4fff8;color:#1a2332;font-size:12px;")
        estilo_normal = ("border:1.5px solid #c8d4de;border-radius:6px;padding:4px 10px;"
                         "background:white;color:#1a2332;font-size:12px;")

        self.inp_email.setStyleSheet(estilo_auto if email_auto else estilo_normal)
        self.inp_nome.setStyleSheet(estilo_auto if nome_auto else estilo_normal)

        if email_auto or nome_auto:
            p1l.addWidget(_lbl("✅  Preenchido a partir da configuração da oficina.",
                               "font-size:10px;color:#1e7e44;"))

        p1l.addWidget(self.inp_email)
        p1l.addWidget(self.inp_nome)

        self.btn_pedir = QPushButton("📧  Pedir Licença"); btn_pedir = self.btn_pedir; btn_pedir.setFixedHeight(40)
        btn_pedir.setStyleSheet(
            f"background:{CORES['aco']};color:white;border:none;"
            f"border-radius:8px;font-weight:700;font-size:12px;")
        btn_pedir.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_pedir.clicked.connect(self._pedir_licenca)
        p1l.addWidget(btn_pedir)
        bl.addWidget(passo1)

        # ── PASSO 2 ────────────────────────────────────────────────────────
        passo2 = QFrame()
        passo2.setStyleSheet("background:#f0f4f8;border:1.5px solid #c8d4de;border-radius:10px;")
        p2l = QVBoxLayout(passo2); p2l.setContentsMargins(16,14,16,14); p2l.setSpacing(10)

        p2l.addWidget(_lbl("② Introduzir o código recebido por email",
                           f"font-size:12px;font-weight:800;color:{CORES['aco']};"))

        self.inp_chave = QLineEdit(); self.inp_chave.setFixedHeight(40)
        self.inp_chave.setPlaceholderText("XXXX-XXXX-XXXX-XXXX")
        self.inp_chave.setMaxLength(19)
        self.inp_chave.setStyleSheet(
            "border:1.5px solid #c8d4de;border-radius:6px;padding:4px 12px;"
            "font-size:14px;letter-spacing:3px;background:white;color:#1a2332;")
        self.inp_chave.returnPressed.connect(self._ativar)
        self.inp_chave.textChanged.connect(self._formatar_codigo)
        p2l.addWidget(self.inp_chave)
        bl.addWidget(passo2)

        # ── Mensagem estado ────────────────────────────────────────────────
        self.lbl_erro = QLabel("")
        self.lbl_erro.setStyleSheet("color:#c0392b;font-size:11px;font-weight:600;")
        self.lbl_erro.setWordWrap(True)
        self.lbl_erro.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bl.addWidget(self.lbl_erro)

        bl.addStretch()

        # ── Botões fixos no fundo ──────────────────────────────────────────
        scroll.setWidget(body)
        lay.addWidget(scroll)

        footer = QWidget()
        footer.setStyleSheet(f"background:{CORES['branco']};border-top:1px solid {CORES['alum']};")
        ftl = QHBoxLayout(footer); ftl.setContentsMargins(28,12,28,12); ftl.setSpacing(8)

        if self.estado != "expirado":
            btn_depois = QPushButton("Continuar avaliação"); btn_depois.setFixedHeight(40)
            btn_depois.setStyleSheet(
                f"background:{CORES['alum']};color:{CORES['aco']};"
                f"border:none;border-radius:8px;padding:0 16px;font-weight:600;")
            btn_depois.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_depois.clicked.connect(self.reject)
            ftl.addWidget(btn_depois)

        ftl.addStretch()
        btn_ativar = QPushButton("✔  Activar Licença"); btn_ativar.setFixedHeight(40)
        btn_ativar.setStyleSheet(
            f"background:{CORES['laranja']};color:white;border:none;"
            f"border-radius:8px;padding:0 20px;font-weight:700;font-size:13px;")
        btn_ativar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ativar.clicked.connect(self._ativar)
        ftl.addWidget(btn_ativar)
        lay.addWidget(footer)

    def _formatar_codigo(self, texto):
        """Formata automaticamente XXXX-XXXX-XXXX-XXXX enquanto escreve"""
        self.inp_chave.blockSignals(True)
        # Remover tudo que não seja alfanumérico e converter para maiúsculas
        limpo = "".join(c for c in texto.upper() if c.isalnum())
        # Inserir hífens nas posições correctas
        partes = [limpo[i:i+4] for i in range(0, min(len(limpo), 16), 4)]
        formatado = "-".join(partes)
        self.inp_chave.setText(formatado)
        # Mover cursor para o fim
        self.inp_chave.setCursorPosition(len(formatado))
        self.inp_chave.blockSignals(False)

    def _pedir_licenca(self):
        email = self.inp_email.text().strip(); nome = self.inp_nome.text().strip()
        if not email or "@" not in email:
            self._set_erro("⚠️  Introduza um email válido.", "#b8700a"); return
        # Feedback visual no botão
        self.btn_pedir.setEnabled(False)
        self.btn_pedir.setText("⏳  A enviar...")
        self.btn_pedir.setStyleSheet(
            "background:#6b7c8e;color:white;border:none;"
            "border-radius:8px;font-weight:700;font-size:12px;")
        self._set_erro("A contactar servidor de email...", CORES["cinza"])
        from PyQt6.QtWidgets import QApplication; QApplication.processEvents()
        from modules.licenca import enviar_pedido_licenca
        ok, msg = enviar_pedido_licenca(email, nome)
        if ok:
            self.btn_pedir.setText("✅  Pedido enviado!")
            self.btn_pedir.setStyleSheet(
                "background:#1e7e44;color:white;border:none;"
                "border-radius:8px;font-weight:700;font-size:12px;")
            self._set_erro("✅  Verifique o seu email para instruções de pagamento.", "#1e7e44")
        else:
            self.btn_pedir.setEnabled(True)
            self.btn_pedir.setText("📧  Pedir Licença")
            self.btn_pedir.setStyleSheet(
                f"background:{CORES['aco']};color:white;border:none;"
                f"border-radius:8px;font-weight:700;font-size:12px;")
            self._set_erro(f"⚠️  Pedido guardado localmente. Contacte condessasilva@gmail.com", "#b8700a")

    def _ativar(self):
        email = self.inp_email.text().strip(); chave = self.inp_chave.text().strip().upper()
        if not email or not chave:
            self._set_erro("⚠️  Preencha o email e o código de activação.", "#c0392b"); return
        self._set_erro("⏳  A verificar...", CORES['cinza'])
        from PyQt6.QtWidgets import QApplication; QApplication.processEvents()
        from modules.licenca import ativar
        resultado = ativar(email, chave)
        if resultado and resultado.get("ok"):
            QMessageBox.information(self, "✅ Licença Activada",
                "Licença activada com sucesso!\nObrigado por registar o AluminioManager.")
            self.accept()
        else:
            erro = resultado.get("erro","Código inválido ou email incorrecto.") if resultado else "Sem ligação ao servidor."
            self._set_erro(f"❌  {erro}", "#c0392b")

    def _set_erro(self, msg, cor):
        self.lbl_erro.setStyleSheet(f"color:{cor};font-size:11px;font-weight:600;")
        self.lbl_erro.setText(msg)
