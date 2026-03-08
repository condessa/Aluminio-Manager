from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStackedWidget, QMessageBox)
from PyQt6.QtCore import Qt
import modules.dao as dao

class MainWindow(QMainWindow):
    def __init__(self, utilizador):
        super().__init__()
        self.utilizador = utilizador
        self.setWindowTitle("Aluminios Manager by HCsoftware")
        self.setMinimumSize(1200, 720)
        self.resize(1400, 820)

        from modules.dashboard    import DashboardWidget
        from modules.obras        import ObrasWidget
        from modules.clientes     import ClientesWidget
        from modules.stock        import StockWidget
        from modules.financeiro   import FinanceiroWidget
        from modules.tarefas      import TarefasWidget
        from modules.sobras       import SobrasWidget
        from modules.funcionarios import FuncionariosWidget
        from modules.relatorios   import RelatoriosWidget

        self._pages = {
            "dashboard":    ("⊞  Dashboard",    DashboardWidget(dao, utilizador)),
            "obras":        ("🔨  Obras",         ObrasWidget(dao, utilizador)),
            "clientes":     ("👥  Clientes",      ClientesWidget(dao, utilizador)),
            "stock":        ("📦  Stock",          StockWidget(dao, utilizador)),
            "financeiro":   ("💶  Financeiro",    FinanceiroWidget(dao, utilizador) if utilizador.get("perfil")=="admin" else QWidget()),
            "tarefas":      ("✓  Tarefas",        TarefasWidget(dao, utilizador)),
            "sobras":       ("♻️  Sobras",          SobrasWidget(dao, utilizador)),
            "funcionarios": ("👷  Funcionários",   FuncionariosWidget(dao, utilizador)),
            "relatorios":   ("📊  Relatórios",     RelatoriosWidget(dao, utilizador)),
        }
        # Sinal para logout
        from PyQt6.QtCore import pyqtSignal
        self.logout_signal = False

        # Timer de inactividade — bloqueia após 5 minutos
        self._inact_segundos = 60
        self._titulo_base = "Aluminios Manager by HCsoftware"
        self._inact_timer = QTimer(self)
        self._inact_timer.setInterval(1000)
        self._inact_timer.timeout.connect(self._tick_inatividade)
        self._inact_timer.start()
        from PyQt6.QtWidgets import QApplication
        QApplication.instance().installEventFilter(self)

        self._build()
        self._nav("dashboard")

    def _build(self):
        cw = QWidget(); self.setCentralWidget(cw)
        root = QHBoxLayout(cw); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        root.addWidget(self._build_sidebar())
        rw = QWidget(); rl = QVBoxLayout(rw); rl.setContentsMargins(0,0,0,0); rl.setSpacing(0)
        rl.addWidget(self._build_topbar())
        self.stack = QStackedWidget()
        for _, (_, w) in self._pages.items(): self.stack.addWidget(w)
        rl.addWidget(self.stack); root.addWidget(rw)
        self.statusBar().showMessage(f"  ⚙  Aluminios Manager by HCsoftware  ·  {self.utilizador['nome']}  ·  {self.utilizador['perfil'].upper()}")

    def _build_sidebar(self):
        sb = QWidget(); sb.setFixedWidth(220)
        sb.setStyleSheet("background:#1a2332;")
        lay = QVBoxLayout(sb); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        logo = QWidget(); logo.setStyleSheet("border-bottom:1px solid rgba(255,255,255,0.1);")
        ll = QVBoxLayout(logo); ll.setContentsMargins(16,18,16,14)
        t = QLabel("⚙️  Aluminios Manager"); t.setStyleSheet("font-size:15px;font-weight:800;color:#e8edf2;")
        # Carregar nome da firma da BD
        nome_firma = "Gestão de Oficina"
        try:
            from db.database import get_connection
            conn=get_connection(); cur=conn.cursor(dictionary=True)
            cur.execute("SELECT valor FROM oficina WHERE chave='nome'")
            r=cur.fetchone(); cur.close(); conn.close()
            if r and r["valor"]: nome_firma = r["valor"].replace(" by HCsoftware","").replace(" by Hcsoftware","")
        except: pass
        s = QLabel(nome_firma); s.setStyleSheet("font-size:11px;font-weight:700;color:#d4560a;letter-spacing:0.5px;")
        s.setWordWrap(True); s.setMaximumWidth(170)
        ll.addWidget(t); ll.addWidget(s); lay.addWidget(logo)
        self._sb_btns = {}
        nw = QWidget(); nl = QVBoxLayout(nw); nl.setContentsMargins(8,12,8,8); nl.setSpacing(2)
        perfil = self.utilizador.get("perfil","")
        # Permissões por perfil
        ACESSO = {
            "admin":    ["dashboard","obras","clientes","stock","sobras","funcionarios","financeiro","tarefas","relatorios"],
            "gestor":   ["dashboard","obras","clientes","stock","sobras","tarefas","relatorios"],
            "producao": ["dashboard","obras","stock","sobras","tarefas"],
            "vendas":   ["dashboard","obras","clientes","tarefas"],
        }
        permitidos = ACESSO.get(perfil, ["dashboard"])
        for sec, keys in [
            ("GESTÃO",  ["dashboard","obras","clientes"]),
            ("OFICINA", ["stock","sobras","funcionarios"]),
            ("ADMIN",   ["financeiro","tarefas","relatorios"]),
        ]:
            sl = QLabel(sec); sl.setStyleSheet("font-size:10px;letter-spacing:2px;color:#9aaabb;font-weight:500;padding:10px 10px 4px;")
            nl.addWidget(sl)
            for k in keys:
                label, _ = self._pages[k]
                tem_acesso = k in permitidos
                b = QPushButton(f"  {label}"); b.setFixedHeight(36)
                if tem_acesso:
                    b.setStyleSheet("QPushButton{background:transparent;border:none;color:rgba(232,237,242,0.6);text-align:left;padding:0 16px;border-radius:8px;font-size:13px;} QPushButton:hover{background:rgba(232,237,242,0.08);color:#e8edf2;} QPushButton[active=true]{background:#d4560a;color:white;font-weight:bold;}")
                    b.setCursor(Qt.CursorShape.PointingHandCursor)
                    b.clicked.connect(lambda _, key=k: self._nav(key))
                else:
                    b.setStyleSheet("QPushButton{background:transparent;border:none;color:rgba(232,237,242,0.2);text-align:left;padding:0 16px;border-radius:8px;font-size:13px;} QPushButton:hover{background:transparent;}")
                    b.setCursor(Qt.CursorShape.ForbiddenCursor)
                    b.setToolTip("Sem permissão de acesso")
                nl.addWidget(b); self._sb_btns[k] = b
        nl.addStretch(); lay.addWidget(nw, stretch=1)
        uw = QWidget(); uw.setStyleSheet("border-top:1px solid rgba(255,255,255,0.1);")
        ul = QHBoxLayout(uw); ul.setContentsMargins(12,10,12,10)
        av = QLabel(self.utilizador["nome"][:2].upper()); av.setFixedSize(32,32)
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av.setStyleSheet("background:#d4560a;color:white;border-radius:16px;font-weight:700;font-size:12px;")
        un = QLabel(self.utilizador["nome"]); un.setStyleSheet("color:#e8edf2;font-size:13px;font-weight:500;")
        bs = QPushButton("↩"); bs.setToolTip("Sair")
        bs.setStyleSheet("background:transparent;border:none;color:#9aaabb;font-size:18px;")
        bs.setCursor(Qt.CursorShape.PointingHandCursor); bs.clicked.connect(self._sair)
        ul.addWidget(av); ul.addWidget(un); ul.addStretch(); ul.addWidget(bs)
        lay.addWidget(uw); return sb

    def _build_topbar(self):
        tb = QWidget(); tb.setFixedHeight(58)
        tb.setStyleSheet("background:#f8fafc;border-bottom:1px solid #c8d4de;")
        lay = QHBoxLayout(tb); lay.setContentsMargins(22,0,22,0)
        self.tb_title = QLabel("Dashboard")
        self.tb_title.setStyleSheet("font-size:20px;font-weight:800;color:#1a2332;")
        self.tb_add = QPushButton("＋  Adicionar")
        self.tb_add.setStyleSheet("background:#d4560a;color:white;border:none;border-radius:8px;padding:8px 18px;font-weight:600;font-size:13px;")
        self.tb_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tb_add.clicked.connect(self._add_clicked)
        lay.addWidget(self.tb_title); lay.addStretch(); lay.addWidget(self.tb_add)
        return tb

    def _nav(self, key):
        self._current = key
        label, widget = self._pages[key]
        self.tb_title.setText(label.strip())
        for k, b in self._sb_btns.items():
            b.setProperty("active", k == key)
            b.style().unpolish(b); b.style().polish(b)
        self.stack.setCurrentIndex(list(self._pages.keys()).index(key))
        self.tb_add.setVisible(key not in {"dashboard","relatorios"})
        if hasattr(widget, "refresh"): widget.refresh()

    def _add_clicked(self):
        _, w = self._pages[self._current]
        if hasattr(w, "novo"): w.novo()

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        if event.type() in (QEvent.Type.MouseMove, QEvent.Type.MouseButtonPress,
                            QEvent.Type.KeyPress, QEvent.Type.Wheel):
            self._inact_segundos = 60
            self.setWindowTitle(self._titulo_base)
        return super().eventFilter(obj, event)

    def _tick_inatividade(self):
        self._inact_segundos -= 1
        if self._inact_segundos <= 0:
            self._inact_timer.stop()
            self.setWindowTitle(self._titulo_base)
            self._bloquear()
        elif self._inact_segundos <= 30:
            self.setWindowTitle(f"⚠️  Sessão bloqueia em {self._inact_segundos}s  —  {self._titulo_base}")
        else:
            self.setWindowTitle(self._titulo_base)

    def _bloquear(self):
        self._inact_timer.stop()
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QWidget
        from db.database import get_connection, hash_password
        dlg = QDialog(self); dlg.setWindowTitle("Sessão bloqueada")
        dlg.setFixedSize(360, 230)
        dlg.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint)
        lay = QVBoxLayout(dlg); lay.setContentsMargins(30,24,30,24); lay.setSpacing(10)
        ico = QLabel("🔒"); ico.setAlignment(Qt.AlignmentFlag.AlignCenter); ico.setStyleSheet("font-size:32px;")
        t1 = QLabel("Sessão bloqueada"); t1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t1.setStyleSheet("font-size:15px;font-weight:700;color:#1a2332;")
        t2 = QLabel("Introduza a sua palavra-passe para continuar")
        t2.setAlignment(Qt.AlignmentFlag.AlignCenter); t2.setStyleSheet("font-size:11px;color:#6b7c8e;")
        inp = QLineEdit(); inp.setEchoMode(QLineEdit.EchoMode.Password)
        inp.setPlaceholderText("Palavra-passe"); inp.setFixedHeight(36)
        lbl_erro = QLabel(""); lbl_erro.setStyleSheet("color:red;font-size:11px;")
        lbl_erro.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bw = QWidget(); bl = QHBoxLayout(bw); bl.setContentsMargins(0,0,0,0)
        btn = QPushButton("🔓  Desbloquear"); btn.setFixedHeight(36)
        btn.setStyleSheet("background:#d4560a;color:white;border:none;border-radius:8px;padding:0 20px;font-weight:600;")
        btn_sair = QPushButton("↩  Sair"); btn_sair.setFixedHeight(36)
        btn_sair.setStyleSheet("background:#e8edf2;color:#1a2332;border:none;border-radius:8px;padding:0 16px;font-weight:600;")
        bl.addWidget(btn_sair); bl.addStretch(); bl.addWidget(btn)
        lay.addWidget(ico); lay.addWidget(t1); lay.addWidget(t2)
        lay.addWidget(inp); lay.addWidget(lbl_erro); lay.addWidget(bw)
        def _verificar():
            try:
                conn=get_connection(); cur=conn.cursor(dictionary=True)
                cur.execute("SELECT id FROM utilizadores WHERE id=%s AND password_hash=%s AND ativo=1",
                    (self.utilizador["id"], hash_password(inp.text())))
                r=cur.fetchone(); cur.close(); conn.close()
                if r: self._inact_timer.start(); dlg.accept()
                else: lbl_erro.setText("Palavra-passe incorrecta."); inp.clear(); inp.setFocus()
            except Exception as e: lbl_erro.setText(str(e))
        def _sair_forcar():
            dlg.reject(); self.logout_signal=True; self.close()
        btn.clicked.connect(_verificar)
        btn_sair.clicked.connect(_sair_forcar)
        inp.returnPressed.connect(_verificar)
        inp.setFocus(); dlg.exec()

    def _configuracoes(self):
        from modules.configuracao import ConfiguracaoDialog
        d = ConfiguracaoDialog(parent=self)
        d.exec()

    def _sair(self):
        from PyQt6.QtWidgets import QMessageBox
        r = QMessageBox.question(self, "Sair", "Terminar sessão?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if r == QMessageBox.StandardButton.Yes:
            self._inact_timer.stop()
            self.logout_signal = True
            self.close()

