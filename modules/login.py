from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt
from db.database import get_connection, hash_password

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.utilizador = None
        self.setWindowTitle("AluminioManager — Login")
        self.setFixedSize(360, 280)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 36, 40, 36)
        lay.setSpacing(14)

        titulo = QLabel("⚙️  AluminioManager")
        titulo.setStyleSheet("font-size:18px;font-weight:800;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub = QLabel("Gestão de Oficina de Alumínios")
        sub.setStyleSheet("font-size:11px;color:#6b7c8e;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.inp_user = QLineEdit()
        self.inp_user.setPlaceholderText("Utilizador")

        self.inp_pass = QLineEdit()
        self.inp_pass.setPlaceholderText("Palavra-passe")
        self.inp_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_pass.returnPressed.connect(self._login)

        self.lbl_erro = QLabel("")
        self.lbl_erro.setStyleSheet("color:red;font-size:12px;")
        self.lbl_erro.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn = QPushButton("Entrar")
        btn.setFixedHeight(38)
        btn.clicked.connect(self._login)

        for w in [titulo, sub, self.inp_user, self.inp_pass, self.lbl_erro, btn]:
            lay.addWidget(w)

    def _login(self):
        u = self.inp_user.text().strip()
        p = self.inp_pass.text()
        if not u or not p:
            self.lbl_erro.setText("Preencha todos os campos.")
            return
        try:
            conn = get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT * FROM utilizadores WHERE username=%s AND password_hash=%s AND ativo=1",
                (u, hash_password(p))
            )
            user = cur.fetchone()
            cur.close(); conn.close()
            if user:
                self.utilizador = user
                self.accept()
            else:
                self.lbl_erro.setText("Utilizador ou palavra-passe incorrectos.")
        except Exception as e:
            self.lbl_erro.setText(f"Erro: {e}")
