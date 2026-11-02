"""Assistente de configuração da ligação à base de dados.

Aparece quando o programa não consegue ligar-se ao MySQL/MariaDB — por exemplo
numa instalação nova, onde a base de dados e o utilizador ainda não existem.
"""

import getpass
import os
import shutil
import subprocess

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from db.database import (
    COMANDOS_SQL,
    caminho_config,
    criar_base_dados,
    descrever_erro,
    load_config,
    save_config,
    test_connection,
)

LARANJA = "#d4560a"
SCRIPT_SISTEMA = "/usr/share/aluminio-manager/configurar_bd.sh"


class DialogoBaseDados(QDialog):
    """Configura a ligação: automática (pkexec) ou manualmente."""

    def __init__(self, erro=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar base de dados")
        self.setMinimumWidth(600)
        self._cfg = load_config()
        self._automatico_disponivel = (
            os.name == "posix"
            and shutil.which("pkexec") is not None
            and os.path.isfile(SCRIPT_SISTEMA)
        )
        self._construir(erro)

    # ── construção ────────────────────────────────────────────────────────

    def _construir(self, erro):
        exterior = QVBoxLayout(self)
        exterior.setSpacing(12)

        titulo = QLabel("Não foi possível ligar à base de dados")
        titulo.setStyleSheet("font-size: 16px; font-weight: 700;")
        exterior.addWidget(titulo)

        self.lbl_erro = QLabel(descrever_erro(erro) if erro else "")
        self.lbl_erro.setWordWrap(True)
        self.lbl_erro.setStyleSheet(
            "color:#8a2b06; background:#fdece3; border:1px solid #f3c9b3;"
            "border-radius:6px; padding:10px;"
        )
        self.lbl_erro.setVisible(bool(erro))
        exterior.addWidget(self.lbl_erro)

        self.btn_auto = QPushButton("Configurar automaticamente")
        self.btn_auto.setStyleSheet(
            f"background:{LARANJA}; color:#ffffff; font-weight:700;"
            "font-size:14px; padding:12px 18px; border-radius:8px;"
        )
        self.btn_auto.clicked.connect(self._automatico)
        self.btn_auto.setVisible(self._automatico_disponivel)
        exterior.addWidget(self.btn_auto)

        self.lbl_dica = QLabel(
            "Pede a palavra-passe do sistema, cria a base de dados e guarda a "
            "configuração. Não é preciso terminal nem conhecimentos de SQL."
        )
        self.lbl_dica.setWordWrap(True)
        self.lbl_dica.setStyleSheet("color:#5b6b7a; font-size:12px;")
        self.lbl_dica.setVisible(self._automatico_disponivel)
        exterior.addWidget(self.lbl_dica)

        self.chk_manual = QCheckBox("Prefiro introduzir os dados de ligação manualmente")
        self.chk_manual.toggled.connect(self._alternar_manual)
        exterior.addWidget(self.chk_manual)

        self.grupo = QGroupBox("Dados de ligação")
        formulario = QFormLayout(self.grupo)
        formulario.setSpacing(8)

        self.inp_host = QLineEdit(self._cfg.get("host", "localhost"))
        self.inp_host.setPlaceholderText("localhost")

        self.inp_porta = QSpinBox()
        self.inp_porta.setRange(1, 65535)
        self.inp_porta.setValue(int(self._cfg.get("port", 3306)))

        self.inp_bd = QLineEdit(self._cfg.get("database", "aluminio_manager"))
        self.inp_user = QLineEdit(self._cfg.get("user", "aluminio_user"))

        self.inp_pass = QLineEdit(self._cfg.get("password", ""))
        self.inp_pass.setEchoMode(QLineEdit.EchoMode.Password)

        self.chk_mostrar = QCheckBox("Mostrar palavra-passe")
        self.chk_mostrar.toggled.connect(self._alternar_password)

        formulario.addRow("Servidor:", self.inp_host)
        formulario.addRow("Porta:", self.inp_porta)
        formulario.addRow("Base de dados:", self.inp_bd)
        formulario.addRow("Utilizador:", self.inp_user)
        formulario.addRow("Palavra-passe:", self.inp_pass)
        formulario.addRow("", self.chk_mostrar)
        self.grupo.setVisible(False)
        exterior.addWidget(self.grupo)

        self.lbl_estado = QLabel()
        self.lbl_estado.setWordWrap(True)
        self.lbl_estado.setVisible(False)
        exterior.addWidget(self.lbl_estado)

        self.chk_ajuda = QCheckBox("Ver os comandos SQL (para administradores)")
        self.chk_ajuda.toggled.connect(self._alternar_ajuda)
        exterior.addWidget(self.chk_ajuda)

        self.ajuda = QPlainTextEdit(COMANDOS_SQL)
        self.ajuda.setReadOnly(True)
        self.ajuda.setFixedHeight(132)
        self.ajuda.setVisible(False)
        self.ajuda.setStyleSheet(
            "font-family: 'DejaVu Sans Mono', monospace; font-size: 11px;"
        )
        exterior.addWidget(self.ajuda)

        self.lbl_ficheiro = QLabel(f"Configuração: {caminho_config()}")
        self.lbl_ficheiro.setStyleSheet("color:#5b6b7a; font-size: 11px;")
        self.lbl_ficheiro.setWordWrap(True)
        exterior.addWidget(self.lbl_ficheiro)

        botoes = QHBoxLayout()

        self.btn_testar = QPushButton("Testar ligação")
        self.btn_testar.clicked.connect(self._testar)
        self.btn_testar.setVisible(False)
        botoes.addWidget(self.btn_testar)

        self.btn_copiar = QPushButton("Copiar comandos SQL")
        self.btn_copiar.clicked.connect(self._copiar)
        self.btn_copiar.setVisible(False)
        botoes.addWidget(self.btn_copiar)
        botoes.addStretch(1)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)
        botoes.addWidget(self.btn_cancelar)

        self.btn_guardar = QPushButton("Guardar e continuar")
        self.btn_guardar.setDefault(True)
        self.btn_guardar.setStyleSheet(
            f"background:{LARANJA}; color:#ffffff; font-weight:600; padding:8px 18px; border-radius:6px;"
        )
        self.btn_guardar.clicked.connect(self._guardar)
        self.btn_guardar.setVisible(False)
        botoes.addWidget(self.btn_guardar)
        exterior.addLayout(botoes)

        if not self._automatico_disponivel:
            self.chk_manual.setChecked(True)

    # ── acções ────────────────────────────────────────────────────────────

    def _alternar_manual(self, ativo):
        self.grupo.setVisible(ativo)
        self.btn_testar.setVisible(ativo)
        self.btn_guardar.setVisible(ativo)
        if ativo:
            self.inp_host.setFocus()

    def _alternar_password(self, ativo):
        self.inp_pass.setEchoMode(
            QLineEdit.EchoMode.Normal if ativo else QLineEdit.EchoMode.Password
        )

    def _alternar_ajuda(self, ativo):
        self.ajuda.setVisible(ativo)
        self.btn_copiar.setVisible(ativo)

    def _recolher(self):
        return {
            "host": self.inp_host.text().strip() or "localhost",
            "port": int(self.inp_porta.value()),
            "database": self.inp_bd.text().strip() or "aluminio_manager",
            "user": self.inp_user.text().strip() or "aluminio_user",
            "password": self.inp_pass.text(),
        }

    def _mostrar_estado(self, texto, ok):
        cor, fundo = ("#1e6b32", "#e8f5e9") if ok else ("#8a2b06", "#fdece3")
        self.lbl_estado.setText(("✔ " if ok else "✖ ") + texto)
        self.lbl_estado.setStyleSheet(
            f"color:{cor}; background:{fundo}; border-radius:6px; padding:8px;"
        )
        self.lbl_estado.setVisible(True)

    def _automatico(self):
        self.btn_auto.setEnabled(False)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            resultado = subprocess.run(
                ["pkexec", SCRIPT_SISTEMA, getpass.getuser()],
                capture_output=True,
                text=True,
                timeout=180,
            )
        except Exception as exc:
            self._mostrar_estado(f"Não foi possível executar a configuração: {exc}", False)
            return
        finally:
            QApplication.restoreOverrideCursor()
            self.btn_auto.setEnabled(True)

        if resultado.returncode == 0:
            ok, mensagem = test_connection(load_config())
            if ok:
                self._mostrar_estado("Base de dados configurada. A abrir o programa…", True)
                self.accept()
            else:
                self._mostrar_estado(mensagem, False)
            return

        detalhe = (resultado.stderr or resultado.stdout or "").strip().splitlines()
        motivo = detalhe[-1] if detalhe else f"código {resultado.returncode}"
        self._mostrar_estado(f"A configuração automática falhou: {motivo}", False)
        self.chk_manual.setChecked(True)

    def _testar(self):
        ok, mensagem = test_connection(self._recolher())
        self._mostrar_estado(mensagem, ok)
        return ok

    def _copiar(self):
        QApplication.clipboard().setText(COMANDOS_SQL)
        self._mostrar_estado(
            "Comandos copiados. Cola-os num terminal e volta a tentar.", True
        )

    def _guardar(self):
        from modules import registo
        try:
            cfg = self._recolher()
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                ok, mensagem = test_connection(cfg)
                if not ok:
                    try:
                        criar_base_dados(cfg)
                        ok, mensagem = test_connection(cfg)
                    except Exception as exc:
                        self._mostrar_estado(descrever_erro(exc), False)
                        return
            finally:
                QApplication.restoreOverrideCursor()

            if not ok:
                self._mostrar_estado(mensagem, False)
                return

            destino = save_config(cfg)
            registo.registar(f"Configuração da base de dados guardada em {destino}")
            self._mostrar_estado("Configuração guardada. A abrir o programa…", True)
            self.accept()
        except Exception as exc:
            registo.registar_excecao()
            try:
                QApplication.restoreOverrideCursor()
            except Exception:
                pass
            self._mostrar_estado(f"Erro inesperado ao guardar: {exc}", False)
