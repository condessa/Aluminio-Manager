from PyQt6.QtCore import QTimer

def cor_fundo():
    return "#f0f4f8"
from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStackedWidget, QMessageBox, QFrame, QHBoxLayout)
from PyQt6.QtCore import Qt
import modules.dao as dao

def cor_fundo():
    return "#f0f4f8"


def cor_fundo():
    return "#f0f4f8"


def cor_fundo():
    return "#f0f4f8"


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
        from modules.fornecedores import FornecedoresWidget
        from modules.calendario import CalendarioWidget
        from modules.relatorios   import RelatoriosWidget

        self._pages = {
            "dashboard":    ("⊞  Dashboard",    DashboardWidget(dao, utilizador)),
            "obras":        ("🔨  Obras",         ObrasWidget(dao, utilizador)),
            "clientes":     ("👥  Clientes",      ClientesWidget(dao, utilizador)),
            "stock":        ("📦  Stock",          StockWidget(dao, utilizador)),
            "financeiro":   ("💶  Financeiro",    FinanceiroWidget(dao, utilizador) if utilizador.get("perfil")=="admin" else QWidget()),
            "calendario":   ("📅  Calendário",  CalendarioWidget(dao, utilizador)),
            "tarefas":      ("✓  Tarefas",        TarefasWidget(dao, utilizador)),
            "sobras":       ("♻️  Sobras",          SobrasWidget(dao, utilizador)),
            "funcionarios": ("👷  Funcionários",   FuncionariosWidget(dao, utilizador)),
            "fornecedores": ("🏭  Fornecedores",   FornecedoresWidget(dao, utilizador)),
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
        self._build_menubar()
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
        self.statusBar().showMessage(
            f"⚙  Aluminios Manager by HCsoftware  ·  {self.utilizador['nome']}  ·  {self.utilizador['perfil'].upper()}")

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
            "admin":    ["dashboard","obras","clientes","stock","sobras","funcionarios","fornecedores","financeiro","calendario","tarefas","relatorios"],
            "gestor":   ["dashboard","obras","clientes","stock","sobras","fornecedores","financeiro","calendario","tarefas","relatorios"],
            "producao": ["dashboard","obras","stock","sobras","tarefas"],
            "vendas":   ["dashboard","obras","clientes","tarefas"],
        }
        permitidos = ACESSO.get(perfil, ["dashboard"])
        for sec, keys in [
            ("GESTÃO",  ["dashboard","obras","clientes"]),
            ("OFICINA", ["stock","sobras","funcionarios","fornecedores"]),
            ("ADMIN",   ["financeiro","calendario","tarefas","relatorios"]),
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
        ul.addWidget(av); ul.addWidget(un); ul.addStretch()
        if self.utilizador.get("perfil") in ("admin","gestor"):
            bcfg = QPushButton("⚙"); bcfg.setToolTip("Configurações da empresa")
            bcfg.setStyleSheet("background:transparent;border:none;color:#9aaabb;font-size:16px;")
            bcfg.setCursor(Qt.CursorShape.PointingHandCursor); bcfg.clicked.connect(self._configuracoes)
            ul.addWidget(bcfg)
        ul.addWidget(bs)
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
            self.statusBar().setStyleSheet("")
            self._bloquear()
        elif self._inact_segundos <= 30:
            self.setWindowTitle(self._titulo_base)
            self.statusBar().setStyleSheet("background:#1a4a8a;color:white;font-size:11px;font-weight:600;")
            self.statusBar().showMessage(f"  🔒  Sessão bloqueia automaticamente em {self._inact_segundos} segundos — mova o rato ou pressione uma tecla para continuar")
        else:
            self.setWindowTitle(self._titulo_base)
            self.statusBar().setStyleSheet("")
            self.statusBar().showMessage(f"  ⚙  {self._titulo_base}  ·  {self.utilizador['nome']}  ·  {self.utilizador['perfil'].upper()}")

    def _bloquear(self):
        self._inact_timer.stop()
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QWidget
        from db.database import get_connection, hash_password
        dlg = QDialog(self); dlg.setWindowTitle("Sessão bloqueada")
        dlg.setFixedSize(400, 320)
        dlg.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint)
        dlg.setStyleSheet(f"background:{cor_fundo()};")
        lay = QVBoxLayout(dlg); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        # Cabeçalho escuro
        from PyQt6.QtWidgets import QFrame
        header = QFrame(); header.setFixedHeight(110)
        header.setStyleSheet("background:#1a2332;border-radius:0px;")
        hl = QVBoxLayout(header); hl.setAlignment(Qt.AlignmentFlag.AlignCenter); hl.setSpacing(4)
        ico = QLabel("🔒"); ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ico.setStyleSheet("font-size:28px;background:transparent;")
        t1 = QLabel("Sessão Bloqueada"); t1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t1.setStyleSheet("font-size:16px;font-weight:800;color:white;background:transparent;")
        t2 = QLabel(f"👤  {self.utilizador['nome']}")
        t2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t2.setStyleSheet("font-size:11px;color:rgba(255,255,255,0.6);background:transparent;")
        hl.addWidget(ico); hl.addWidget(t1); hl.addWidget(t2)
        lay.addWidget(header)

        # Corpo
        body = QWidget(); body.setStyleSheet(f"background:{cor_fundo()};")
        bl2 = QVBoxLayout(body); bl2.setContentsMargins(32,24,32,24); bl2.setSpacing(12)
        t3 = QLabel("Introduza a sua palavra-passe para continuar")
        t3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t3.setStyleSheet("font-size:12px;color:#6b7c8e;")
        inp = QLineEdit(); inp.setEchoMode(QLineEdit.EchoMode.Password)
        inp.setPlaceholderText("Palavra-passe"); inp.setFixedHeight(40)
        inp.setStyleSheet("border:2px solid #c8d4de;border-radius:8px;padding:0 12px;font-size:13px;background:white;")
        lbl_erro = QLabel(""); lbl_erro.setStyleSheet("color:#c0392b;font-size:11px;font-weight:600;")
        lbl_erro.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bw = QWidget(); bw.setStyleSheet("background:transparent;")
        bl = QHBoxLayout(bw); bl.setContentsMargins(0,0,0,0); bl.setSpacing(8)
        btn = QPushButton("🔓  Desbloquear"); btn.setFixedHeight(40)
        btn.setStyleSheet("background:#d4560a;color:white;border:none;border-radius:8px;padding:0 20px;font-weight:700;font-size:13px;")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_sair = QPushButton("↩  Sair"); btn_sair.setFixedHeight(40)
        btn_sair.setStyleSheet("background:#e8edf2;color:#1a2332;border:none;border-radius:8px;padding:0 16px;font-weight:600;font-size:13px;")
        btn_sair.setCursor(Qt.CursorShape.PointingHandCursor)
        bl.addWidget(btn_sair); bl.addStretch(); bl.addWidget(btn)
        bl2.addWidget(t3); bl2.addWidget(inp); bl2.addWidget(lbl_erro); bl2.addWidget(bw)
        lay.addWidget(body)
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


    def _build_menubar(self):
        from PyQt6.QtGui import QAction
        mb = self.menuBar()
        mb.setStyleSheet("""
            QMenuBar { background:#1a2332; color:#e8edf2; font-size:12px; padding:2px; }
            QMenuBar::item { padding:4px 12px; border-radius:4px; }
            QMenuBar::item:selected { background:#d4560a; }
            QMenu { background:#1a2332; color:#e8edf2; border:1px solid #2d3f55; font-size:12px; }
            QMenu::item { padding:8px 24px; }
            QMenu::item:selected { background:#d4560a; color:white; }
            QMenu::separator { height:1px; background:#2d3f55; margin:4px 0; }
        """)
        m_fich = mb.addMenu("📁  Ficheiro")
        perfil = self.utilizador.get("perfil","")
        if perfil in ("admin","gestor"):
            a_cfg = QAction("⚙️  Configurações", self); a_cfg.triggered.connect(self._configuracoes)
            m_fich.addAction(a_cfg); m_fich.addSeparator()
        a_sair = QAction("↩  Terminar Sessão", self); a_sair.triggered.connect(self._sair)
        m_fich.addAction(a_sair)

        m_ajuda = mb.addMenu("❓  Ajuda")
        a_email = QAction("📧  Como configurar o Email", self); a_email.triggered.connect(self._ajuda_email)
        a_perfis = QAction("👥  Perfis de Utilizador", self); a_perfis.triggered.connect(self._ajuda_perfis)
        a_orc = QAction("📋  Como criar um Orçamento", self); a_orc.triggered.connect(self._ajuda_orcamento)
        a_sobre = QAction("ℹ️  Sobre", self); a_sobre.triggered.connect(self._sobre)
        from version import VERSION as _versao
        a_novidades = QAction(f"🆕  Novidades v{_versao}", self); a_novidades.triggered.connect(self._ajuda_novidades)
        m_ajuda.addAction(a_email); m_ajuda.addAction(a_perfis)
        m_ajuda.addAction(a_orc); m_ajuda.addAction(a_novidades)
        m_ajuda.addSeparator(); m_ajuda.addAction(a_sobre)

    def _ajuda_email(self):
        from modules.email_setup import DialogoEmail
        DialogoEmail(self).exec()

    def _ajuda_perfis(self):
        self._mostrar_ajuda("👥  Perfis de Utilizador", """
<h2 style='color:#d4560a;'>Perfis de Utilizador</h2>
<table border='1' cellpadding='8' cellspacing='0' style='border-collapse:collapse;width:100%;font-size:12px;'>
<tr style='background:#1a2332;color:white;'><th>Perfil</th><th>Acesso</th></tr>
<tr style='background:#fde8e0;'><td><b>🔴 Admin</b></td><td>Acesso total a todas as funcionalidades e configurações</td></tr>
<tr style='background:#fff3cd;'><td><b>🟡 Gestor</b></td><td>Obras, Clientes, Stock, Sobras, Tarefas, Relatórios, Configurações</td></tr>
<tr style='background:#d4edda;'><td><b>🟢 Produção</b></td><td>Dashboard, Obras, Stock, Sobras, Tarefas (só as suas)</td></tr>
<tr style='background:#e8f0fa;'><td><b>🔵 Vendas</b></td><td>Dashboard, Obras, Clientes, Tarefas (só as suas)</td></tr>
</table>
<p style='margin-top:16px;'>Para criar utilizadores aceda a <b>Funcionários → tab Utilizadores</b>.</p>
""")

    def _ajuda_orcamento(self):
        self._mostrar_ajuda("📋  Como criar um Orçamento", """
<h2 style='color:#d4560a;'>Como criar e enviar um Orçamento</h2>
<h3 style='color:#1a2332;'>1. Criar a Obra</h3>
<ol>
<li>Aceda a <b>Obras</b> → clique <b>＋ Adicionar</b></li>
<li>Preencha a descrição, cliente, valor do orçamento e datas</li>
<li>Guarde a obra</li>
</ol>
<h3 style='color:#1a2332;'>2. Imprimir ou Enviar</h3>
<ol>
<li>Na lista de Obras clique em <b>Ações ▾</b></li>
<li>Escolha <b>🖨️ Imprimir Orçamento</b></li>
<li>Na janela pode pré-visualizar, imprimir ou enviar por email</li>
<li>Pode incluir ou excluir IVA (23%)</li>
</ol>
<h3 style='color:#1a2332;'>3. Assinatura Digital</h3>
<p>O PDF enviado por email é assinado digitalmente com o certificado da empresa (válido 10 anos).</p>
<p style='color:#6b7c8e;font-size:11px;'>⚠️ O cliente precisa de ter email registado na sua ficha.</p>
""")

    def _ajuda_novidades(self):
        from version import VERSION
        self._mostrar_ajuda(f"🆕  Novidades v{VERSION}", f"""
<h2 style='color:#d4560a;'>Novidades na versão {VERSION}</h2>

<h3 style='color:#1a2332;'>🆓 Gratuito e de código aberto</h3>
<p>O AluminioManager passou a ser software livre (GPLv3): sem período de avaliação,
sem chaves de ativação e sem pagamentos.</p>

<h3 style='color:#1a2332;'>📦 Instalação sem Internet</h3>
<p>O pacote inclui todas as bibliotecas necessárias. Pode ser instalado numa oficina
sem ligação à rede.</p>

<h3 style='color:#1a2332;'>⚙️ Base de dados automática</h3>
<p>Se a ligação ao MySQL/MariaDB falhar, aparece o botão <b>«Configurar automaticamente»</b>,
que cria a base de dados e o utilizador com a palavra-passe do sistema.</p>

<h3 style='color:#1a2332;'>👤 Primeira utilização</h3>
<p>Sem contas pré-definidas: na primeira execução é criada a conta de administrador
e o programa entra diretamente nela.</p>

<h3 style='color:#1a2332;'>📧 Envio pela conta da oficina</h3>
<p>Em <b>Ajuda → Como configurar o Email</b> é possível ligar a conta Google da oficina
e os orçamentos passam a sair desse email (OAuth), sem palavras-passe.</p>

<h3 style='color:#1a2332;'>🔒 Estados finais das obras</h3>
<p>Uma obra <b>Concluída</b> ou <b>Cancelada</b> já não pode mudar de estado. O menu
«Mudar estado» mostra apenas as transições válidas.</p>

<h3 style='color:#1a2332;'>🐛 Correções</h3>
<ul>
<li>Mensagens claras para servidor em baixo, credenciais recusadas e base de dados inexistente.</li>
<li>Compatibilidade com Python 3.10 a 3.13.</li>
<li>Configuração guardada em <b>~/.config/aluminio-manager</b>, gravável por qualquer utilizador.</li>
</ul>
""")

    def _sobre(self):
        from pathlib import Path
        from version import VERSION
        from modules.marca import caminho as caminho_marca
        ficheiro_logo = caminho_marca("hcsoftware.png")
        logo_html = (f"<img src='file:///{ficheiro_logo}' width='88'/><br/>"
                     if ficheiro_logo else "⚙️")
        self._mostrar_ajuda("ℹ️  Sobre", f"""
<div style='text-align:center;padding:20px;'>
{logo_html}
<h1 style='color:#d4560a;font-size:24px;'>Aluminios Manager</h1>
<p style='color:#6b7c8e;'>by HCsoftware</p>
<p style='margin-top:16px;font-size:13px;'>Sistema de gestão completo para oficinas de alumínio e caixilharia.</p>
<hr style='border:none;border-top:1px solid #e8edf2;margin:20px 0;'/>
<table border='0' cellpadding='6' style='margin:0 auto;font-size:12px;'>
<tr><td style='color:#6b7c8e;'>Versão:</td><td><b>{VERSION}</b></td></tr>
<tr><td style='color:#6b7c8e;'>Desenvolvido por:</td><td><b>HCsoftware</b></td></tr>
<tr><td style='color:#6b7c8e;'>Contacto:</td><td><b>condessasilva@gmail.com</b></td></tr>
<tr><td style='color:#6b7c8e;'>Plataforma:</td><td><b>Python 3 + PyQt6</b></td></tr>
<tr><td style='color:#6b7c8e;'>Base de dados:</td><td><b>MySQL / MariaDB</b></td></tr>
<tr><td style='color:#6b7c8e;'>Licença:</td><td><b>GPLv3 — software livre</b></td></tr>
</table>
<hr style='border:none;border-top:1px solid #e8edf2;margin:20px 0;'/>
<p style='color:#9aaabb;font-size:10px;'>© 2026 HCsoftware — Licença GPLv3</p>
</div>
""")

    def _mostrar_ajuda(self, titulo, html):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton, QHBoxLayout, QWidget
        dlg = QDialog(self); dlg.setWindowTitle(titulo); dlg.resize(640, 520)
        lay = QVBoxLayout(dlg); lay.setContentsMargins(0,0,0,0)
        tb = QTextBrowser()
        tb.setHtml(f"<html><body style='font-family:Arial,sans-serif;font-size:13px;color:#1a2332;padding:24px;line-height:1.7;'>{html}</body></html>")
        lay.addWidget(tb)
        bw = QWidget(); bw.setStyleSheet("background:#f8fafc;border-top:1px solid #e8edf2;")
        bl = QHBoxLayout(bw); bl.setContentsMargins(16,10,16,10)
        btn = QPushButton("✕  Fechar"); btn.setFixedHeight(34)
        btn.setStyleSheet("background:#e8edf2;color:#1a2332;border:none;border-radius:8px;padding:0 20px;font-weight:600;")
        btn.clicked.connect(dlg.reject)
        bl.addStretch(); bl.addWidget(btn)
        lay.addWidget(bw)
        dlg.exec()
