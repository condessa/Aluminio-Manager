"""Configuração do envio de email: conta da oficina (Google) ou da aplicação."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from modules import gmail_oauth


class DialogoEmail(QDialog):
    """Liga a conta Google da oficina para o envio dos orçamentos."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📧  Envio de email")
        self.setMinimumWidth(540)
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
        self.btn_ligar = QPushButton("Ligar conta Google da oficina")
        self.btn_ligar.setStyleSheet(
            "background:#d4560a; color:#ffffff; font-weight:600;"
            "padding:9px 16px; border-radius:6px;"
        )
        self.btn_ligar.clicked.connect(self._ligar)
        botoes.addWidget(self.btn_ligar)

        self.btn_desligar = QPushButton("Desligar conta")
        self.btn_desligar.clicked.connect(self._desligar)
        botoes.addWidget(self.btn_desligar)
        botoes.addStretch(1)

        btn_fechar = QPushButton("Fechar")
        btn_fechar.clicked.connect(self.accept)
        botoes.addWidget(btn_fechar)
        lay.addLayout(botoes)

        self._actualizar()

    def _actualizar(self):
        disponivel = gmail_oauth.disponivel()
        ligado = gmail_oauth.configurado()

        if ligado:
            conta = gmail_oauth.conta() or "conta Google"
            self.lbl_estado.setText(
                f"✔  Emails enviados pela conta da oficina: <b>{conta}</b>"
            )
            self.lbl_estado.setStyleSheet(
                "color:#1e6b32; background:#e8f5e9; border-radius:6px; padding:8px;"
            )
        else:
            self.lbl_estado.setText(
                "✔  Emails enviados pela conta da aplicação "
                "(aluminiomanager@gmail.com)."
            )
            self.lbl_estado.setStyleSheet(
                "color:#8a5a06; background:#fff8e1; border-radius:6px; padding:8px;"
            )

        self.btn_ligar.setVisible(disponivel)
        self.btn_ligar.setEnabled(disponivel)
        self.btn_desligar.setVisible(ligado)

        if disponivel:
            self.lbl_detalhe.setText(
                "Carregue em «Ligar conta Google da oficina» e autorize com o email "
                "da oficina. O browser abre-se sozinho e só é preciso fazer isto uma vez."
            )
        else:
            self.lbl_detalhe.setText(
                "O envio está a funcionar pela conta da aplicação. A ligação à conta "
                "Google da oficina não está disponível nesta versão."
            )

    def _ligar(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            email = gmail_oauth.autorizar()
        except Exception as exc:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self, "Não foi possível ligar", str(exc))
            return
        QApplication.restoreOverrideCursor()
        QMessageBox.information(
            self,
            "Conta ligada",
            "Os orçamentos passam a ser enviados por:\n" + (email or "conta Google"),
        )
        self._actualizar()

    def _desligar(self):
        gmail_oauth.desligar()
        self._actualizar()
