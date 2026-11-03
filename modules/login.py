from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QHBoxLayout, QFrame)
from PyQt6.QtCore import Qt
from db.database import get_connection, hash_password

CORES = {"aco":"#1a2332","laranja":"#d4560a","cinza":"#6b7c8e",
         "alum":"#e8edf2","branco":"#f8fafc","danger":"#c0392b","success":"#1e7e44"}

SENHA_PADRAO = "admin123"


def _is_senha_padrao(username):
    """Verifica se o utilizador ainda tem a senha padrão de fábrica."""
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT id FROM utilizadores WHERE username=%s AND password_hash=%s",
            (username, hash_password(SENHA_PADRAO))
        )
        row = cur.fetchone()
        cur.close(); conn.close()
        return row is not None
    except:
        return False


class AlterarSenhaDialog(QDialog):
    """Diálogo obrigatório para alterar a senha padrão."""

    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("🔐  Definir Nova Palavra-passe")
        self.setFixedSize(420, 390)
        # impede fechar sem alterar
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint
        )
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(36, 28, 36, 28)
        lay.setSpacing(14)

        # Ícone central
        ico = QLabel("🔐")
        ico.setStyleSheet("font-size:40px;background:transparent;")
        ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(ico)

        # Título
        tit = QLabel("Primeira utilização detectada")
        tit.setStyleSheet(f"font-size:15px;font-weight:800;color:{CORES['aco']};")
        tit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(tit)

        # Aviso
        aviso = QFrame()
        aviso.setStyleSheet(
            "background:#fff8e1;border:1px solid #ffc107;"
            "border-radius:8px;padding:4px;")
        av_lay = QVBoxLayout(aviso)
        av_lay.setContentsMargins(14, 10, 14, 10)
        av_lay.setSpacing(4)
        msg = QLabel(
            "Por segurança, defina uma nova palavra-passe\n"
            "antes de aceder à aplicação.")
        msg.setStyleSheet(f"font-size:12px;color:{CORES['aco']};background:transparent;")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av_lay.addWidget(msg)
        lay.addWidget(aviso)

        lbl_user = QLabel(f"Utilizador:  <b>{self.user['username']}</b>")
        lbl_user.setStyleSheet(f"font-size:12px;color:{CORES['cinza']};")
        lbl_user.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(lbl_user)

        # Campos
        self.inp_nova = QLineEdit()
        self.inp_nova.setPlaceholderText("🔑  Nova palavra-passe")
        self.inp_nova.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_nova.setMinimumHeight(38)

        self.inp_conf = QLineEdit()
        self.inp_conf.setPlaceholderText("🔑  Confirmar palavra-passe")
        self.inp_conf.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_conf.setMinimumHeight(38)
        self.inp_conf.returnPressed.connect(self._guardar)

        # Requisitos
        req = QLabel("Mínimo 6 caracteres  ·  Não pode ser 'admin123'")
        req.setStyleSheet(f"font-size:10px;color:{CORES['cinza']};")
        req.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_erro = QLabel("")
        self.lbl_erro.setStyleSheet(
            f"color:{CORES['danger']};font-size:12px;font-weight:600;")
        self.lbl_erro.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_erro.setWordWrap(True)

        btn = QPushButton("✔  Definir Nova Palavra-passe")
        btn.setMinimumHeight(42)
        btn.setStyleSheet(
            f"background:{CORES['laranja']};color:white;border:none;"
            f"border-radius:10px;font-weight:700;font-size:13px;")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._guardar)

        for w in [self.inp_nova, self.inp_conf, req, self.lbl_erro, btn]:
            lay.addWidget(w)

    def _guardar(self):
        nova = self.inp_nova.text()
        conf = self.inp_conf.text()

        if len(nova) < 6:
            self.lbl_erro.setText("A palavra-passe deve ter pelo menos 6 caracteres.")
            return
        if nova == SENHA_PADRAO:
            self.lbl_erro.setText("Não pode usar a palavra-passe padrão.")
            return
        if nova != conf:
            self.lbl_erro.setText("As palavras-passe não coincidem.")
            self.inp_conf.clear(); self.inp_conf.setFocus()
            return

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "UPDATE utilizadores SET password_hash=%s WHERE id=%s",
                (hash_password(nova), self.user["id"])
            )
            conn.commit(); cur.close(); conn.close()
            QMessageBox.information(
                self, "✅  Sucesso",
                "Palavra-passe alterada com sucesso!\nBem-vindo ao AluminioManager.")
            self.accept()
        except Exception as e:
            self.lbl_erro.setText(f"Erro: {e}")


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.utilizador = None
        from version import VERSION as _versao
        self.setWindowTitle(f"AluminioManager v{_versao} — Login")
        self.setFixedSize(360, 300)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 36, 40, 36)
        lay.setSpacing(14)

        from modules.marca import logo_tile
        logo = QLabel()
        logo.setPixmap(logo_tile(84))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("background:transparent;")
        lay.addWidget(logo)

        titulo = QLabel("AluminioManager")
        titulo.setStyleSheet("font-size:18px;font-weight:800;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub = QLabel("Gestão de Oficina de Alumínios")
        sub.setStyleSheet(f"font-size:11px;color:{CORES['cinza']};")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.inp_user = QLineEdit()
        self.inp_user.setPlaceholderText("Utilizador")
        self.inp_user.setMinimumHeight(36)

        self.inp_pass = QLineEdit()
        self.inp_pass.setPlaceholderText("Palavra-passe")
        self.inp_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_pass.setMinimumHeight(36)
        self.inp_pass.returnPressed.connect(self._login)

        self.lbl_erro = QLabel("")
        self.lbl_erro.setStyleSheet(f"color:{CORES['danger']};font-size:12px;")
        self.lbl_erro.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn = QPushButton("Entrar")
        btn.setFixedHeight(38)
        btn.setStyleSheet(
            f"background:{CORES['laranja']};color:white;border:none;"
            f"border-radius:8px;font-weight:700;font-size:13px;")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
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
                # ── Verificar se ainda usa a senha padrão ─────────────────
                if _is_senha_padrao(u):
                    dlg = AlterarSenhaDialog(user, parent=self)
                    if dlg.exec() != QDialog.DialogCode.Accepted:
                        # Não deixa entrar sem mudar a senha
                        self.lbl_erro.setText("É obrigatório definir uma nova palavra-passe.")
                        return
                    # Recarregar utilizador com dados atualizados
                    conn2 = get_connection()
                    cur2 = conn2.cursor(dictionary=True)
                    cur2.execute("SELECT * FROM utilizadores WHERE id=%s", (user["id"],))
                    user = cur2.fetchone()
                    cur2.close(); conn2.close()

                self.utilizador = user
                self.accept()
            else:
                self.lbl_erro.setText("Utilizador ou palavra-passe incorrectos.")
                self.inp_pass.clear(); self.inp_pass.setFocus()

        except Exception as e:
            self.lbl_erro.setText(f"Erro: {e}")
