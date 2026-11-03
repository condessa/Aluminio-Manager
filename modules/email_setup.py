"""Configuração do envio de email.

Três formas de enviar:
- conta da aplicação (por omissão, já funciona);
- SMTP da oficina (qualquer fornecedor: Outlook, SAPO, domínio próprio…);
- conta Google da oficina (OAuth), quando o cliente OAuth está incluído.
"""

from email.mime.text import MIMEText

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from modules import gmail_oauth, smtp_config
from modules.configuracao import carregar_oficina

LARANJA = "#d4560a"


class DialogoSMTP(QDialog):
    """Configura o servidor de email da oficina."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Email da oficina (SMTP)")
        self.setMinimumWidth(540)
        self._construir()

    def _construir(self):
        cfg = smtp_config.valores(carregar_oficina())

        lay = QVBoxLayout(self)
        lay.setSpacing(12)

        titulo = QLabel("Enviar com o email da oficina")
        titulo.setStyleSheet("font-size:16px; font-weight:700;")
        lay.addWidget(titulo)

        ajuda = QLabel(
            "Preencha com os dados do fornecedor do email da oficina. Muitos serviços "
            "(Outlook, SAPO, etc.) exigem uma «palavra-passe de aplicação», que se cria "
            "nas definições de segurança da conta."
        )
        ajuda.setWordWrap(True)
        ajuda.setStyleSheet("color:#5b6b7a; font-size:12px;")
        lay.addWidget(ajuda)

        grupo = QGroupBox("Servidor de saída")
        form = QFormLayout(grupo)
        form.setSpacing(8)

        self.inp_host = QLineEdit(cfg["host"])
        self.inp_host.setPlaceholderText("ex.: smtp.office365.com")

        self.inp_porta = QSpinBox()
        self.inp_porta.setRange(1, 65535)
        self.inp_porta.setValue(cfg["port"])

        self.inp_user = QLineEdit(cfg["user"])
        self.inp_user.setPlaceholderText("ex.: geral@oficina.pt")

        self.inp_pass = QLineEdit(cfg["password"])
        self.inp_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_pass.setPlaceholderText("palavra-passe ou palavra-passe de aplicação")

        self.inp_email = QLineEdit(cfg["email"])
        self.inp_email.setPlaceholderText("email que aparece no «De:»")

        self.cmb_seg = QComboBox()
        for chave, texto in smtp_config.SEGURANCA.items():
            self.cmb_seg.addItem(texto, chave)
        indice = self.cmb_seg.findData(cfg["security"])
        if indice >= 0:
            self.cmb_seg.setCurrentIndex(indice)

        form.addRow("Servidor:", self.inp_host)
        form.addRow("Porta:", self.inp_porta)
        form.addRow("Utilizador:", self.inp_user)
        form.addRow("Palavra-passe:", self.inp_pass)
        form.addRow("Email (De:):", self.inp_email)
        form.addRow("Segurança:", self.cmb_seg)
        lay.addWidget(grupo)

        self.lbl_estado = QLabel()
        self.lbl_estado.setWordWrap(True)
        self.lbl_estado.setVisible(False)
        lay.addWidget(self.lbl_estado)

        botoes = QHBoxLayout()
        self.btn_testar = QPushButton("Testar ligação")
        self.btn_testar.clicked.connect(self._testar)
        botoes.addWidget(self.btn_testar)

        self.btn_teste_email = QPushButton("Enviar email de teste")
        self.btn_teste_email.clicked.connect(self._enviar_teste)
        botoes.addWidget(self.btn_teste_email)
        botoes.addStretch(1)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        botoes.addWidget(btn_cancelar)

        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.setStyleSheet(
            f"background:{LARANJA}; color:#ffffff; font-weight:600; padding:8px 18px; border-radius:6px;")
        self.btn_guardar.clicked.connect(self._guardar)
        botoes.addWidget(self.btn_guardar)
        lay.addLayout(botoes)

    def _recolher(self):
        return {
            "host": self.inp_host.text().strip(),
            "port": int(self.inp_porta.value()),
            "user": self.inp_user.text().strip(),
            "password": self.inp_pass.text(),
            "security": self.cmb_seg.currentData(),
            "email": self.inp_email.text().strip(),
        }

    def _estado(self, texto, ok):
        cor, fundo = ("#1e6b32", "#e8f5e9") if ok else ("#8a2b06", "#fdece3")
        self.lbl_estado.setText(("✔ " if ok else "✖ ") + texto)
        self.lbl_estado.setStyleSheet(
            f"color:{cor}; background:{fundo}; border-radius:6px; padding:8px;")
        self.lbl_estado.setVisible(True)

    def _testar(self):
        cfg = self._recolher()
        if not cfg["host"] or not cfg["user"]:
            self._estado("Preencha o servidor e o utilizador.", False)
            return False
        self.btn_testar.setEnabled(False)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            ok, mensagem = smtp_config.testar(cfg)
        finally:
            QApplication.restoreOverrideCursor()
            self.btn_testar.setEnabled(True)
        self._estado(mensagem, ok)
        return ok

    def _enviar_teste(self):
        cfg = self._recolher()
        destino = cfg["email"] or cfg["user"]
        if not destino:
            self._estado("Indique o email da oficina.", False)
            return
        if not self._testar():
            return

        mensagem = MIMEText(
            "Este é um email de teste enviado pelo AluminioManager.\n\n"
            "Se o recebeu, o servidor de email da oficina está configurado corretamente.",
            "plain", "utf-8")
        mensagem["Subject"] = "AluminioManager — teste de envio"
        mensagem["From"] = destino
        mensagem["To"] = destino

        self.btn_teste_email.setEnabled(False)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            smtp_config.enviar(mensagem, cfg)
            self._estado(f"Email de teste enviado para {destino}.", True)
        except Exception as erro:
            self._estado(smtp_config._mensagem(erro), False)
        finally:
            QApplication.restoreOverrideCursor()
            self.btn_teste_email.setEnabled(True)

    def _guardar(self):
        cfg = self._recolher()
        if not (cfg["host"] and cfg["user"] and cfg["password"]):
            self._estado("Preencha o servidor, o utilizador e a palavra-passe.", False)
            return
        if not self._testar():
            return
        smtp_config.guardar(cfg)
        self.accept()


class DialogoEmail(QDialog):
    """Mostra por que conta os emails saem e permite mudar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📧  Envio de email")
        self.setMinimumWidth(560)
        self._construir()

    def _construir(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(12)

        titulo = QLabel("Envio de orçamentos por email")
        titulo.setStyleSheet("font-size:16px; font-weight:700;")
        lay.addWidget(titulo)

        self.lbl_estado = QLabel()
        self.lbl_estado.setWordWrap(True)
        lay.addWidget(self.lbl_estado)

        self.lbl_detalhe = QLabel()
        self.lbl_detalhe.setWordWrap(True)
        self.lbl_detalhe.setStyleSheet("color:#5b6b7a; font-size:12px;")
        lay.addWidget(self.lbl_detalhe)

        botoes = QHBoxLayout()

        self.btn_smtp = QPushButton("Configurar email da oficina (SMTP)")
        self.btn_smtp.setStyleSheet(
            f"background:{LARANJA}; color:#ffffff; font-weight:600; padding:9px 16px; border-radius:6px;")
        self.btn_smtp.clicked.connect(self._configurar_smtp)
        botoes.addWidget(self.btn_smtp)

        self.btn_ligar = QPushButton("Ligar conta Google")
        self.btn_ligar.clicked.connect(self._ligar_google)
        botoes.addWidget(self.btn_ligar)

        self.btn_desligar = QPushButton("Usar conta da aplicação")
        self.btn_desligar.clicked.connect(self._desligar)
        botoes.addWidget(self.btn_desligar)
        botoes.addStretch(1)

        btn_fechar = QPushButton("Fechar")
        btn_fechar.clicked.connect(self.accept)
        botoes.addWidget(btn_fechar)
        lay.addLayout(botoes)

        self._actualizar()

    def _actualizar(self):
        oficina = carregar_oficina()
        tem_smtp = smtp_config.configurado(oficina)
        tem_google = gmail_oauth.configurado()

        if tem_smtp:
            conta = oficina.get("smtp_user") or oficina.get("email") or "oficina"
            self.lbl_estado.setText(f"✔  Emails enviados pela conta da oficina: <b>{conta}</b>")
            self.lbl_estado.setStyleSheet(
                "color:#1e6b32; background:#e8f5e9; border-radius:6px; padding:8px;")
        elif tem_google:
            conta = gmail_oauth.conta() or "conta Google"
            self.lbl_estado.setText(f"✔  Emails enviados pela conta Google: <b>{conta}</b>")
            self.lbl_estado.setStyleSheet(
                "color:#1e6b32; background:#e8f5e9; border-radius:6px; padding:8px;")
        else:
            self.lbl_estado.setText(
                "✔  Emails enviados pela conta da aplicação "
                "(aluminiomanager@gmail.com).")
            self.lbl_estado.setStyleSheet(
                "color:#8a5a06; background:#fff8e1; border-radius:6px; padding:8px;")

        self.btn_desligar.setVisible(tem_smtp or tem_google)
        self.btn_ligar.setVisible(gmail_oauth.disponivel())

        if tem_smtp:
            self.lbl_detalhe.setText(
                "Está a usar o servidor SMTP da oficina. Para alterar os dados, "
                "carregue em «Configurar email da oficina (SMTP)».")
        else:
            self.lbl_detalhe.setText(
                "Pode enviar pela conta da aplicação (já funciona) ou configurar o "
                "servidor SMTP da oficina — Outlook, SAPO, domínio próprio, etc.")

    def _configurar_smtp(self):
        dialogo = DialogoSMTP(self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self._actualizar()

    def _ligar_google(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            email = gmail_oauth.autorizar()
        except Exception as exc:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self, "Não foi possível ligar", str(exc))
            return
        QApplication.restoreOverrideCursor()
        QMessageBox.information(
            self, "Conta ligada",
            "Os orçamentos passam a ser enviados por:\n" + (email or "conta Google"))
        self._actualizar()

    def _desligar(self):
        smtp_config.desligar()
        gmail_oauth.desligar()
        self._actualizar()
