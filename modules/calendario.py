from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QScrollArea, QFrame, QDialog, QFormLayout, QLineEdit, QComboBox,
    QDateEdit, QTextEdit, QMessageBox, QSizePolicy)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont
import calendar
from datetime import date, datetime

def _btn(t, o="btn_outline"):
    b = QPushButton(t); b.setObjectName(o)
    b.setCursor(Qt.CursorShape.PointingHandCursor); return b

MESES_PT = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
            "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
DIAS_PT  = ["Seg","Ter","Qua","Qui","Sex","Sáb","Dom"]

COR_OBRA    = "#1a56db"
COR_TAREFA  = "#d4560a"
COR_EVENTO  = "#1a7a3a"
COR_HOJE    = "#d4560a"


class EventoDialog(QDialog):
    def __init__(self, dao, parent=None, evento=None, data_inicial=None):
        super().__init__(parent)
        self.dao = dao
        self.evento = evento
        self.setWindowTitle("Novo Evento" if not evento else "Editar Evento")
        self.setMinimumWidth(400)
        self._build(data_inicial)
        if evento:
            self._preencher()

    def _build(self, data_inicial):
        lay = QVBoxLayout(self)
        form = QFormLayout(); form.setSpacing(10)

        self.inp_titulo = QLineEdit(); self.inp_titulo.setPlaceholderText("Título do evento")
        self.inp_descricao = QTextEdit(); self.inp_descricao.setFixedHeight(70)
        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems(["reuniao","entrega","manutencao","outro"])

        self.dt_data = QDateEdit()
        self.dt_data.setCalendarPopup(True)
        self.dt_data.setDate(QDate.fromString(str(data_inicial or date.today()), "yyyy-MM-dd"))
        self.dt_data.setDisplayFormat("dd/MM/yyyy")

        form.addRow("Título *", self.inp_titulo)
        form.addRow("Tipo", self.cmb_tipo)
        form.addRow("Data", self.dt_data)
        form.addRow("Descrição", self.inp_descricao)
        lay.addLayout(form)

        bt = QHBoxLayout(); bt.addStretch()
        bc = _btn("Cancelar","btn_secondary"); bc.clicked.connect(self.reject)
        bg = _btn("💾 Guardar","btn_primary"); bg.clicked.connect(self._guardar)
        bt.addWidget(bc); bt.addWidget(bg)
        lay.addLayout(bt)

    def _preencher(self):
        e = self.evento
        self.inp_titulo.setText(e.get("titulo",""))
        self.inp_descricao.setPlainText(e.get("descricao","") or "")
        self.dt_data.setDate(QDate.fromString(str(e.get("data",""))[:10], "yyyy-MM-dd"))
        tipos = ["reuniao","entrega","manutencao","outro"]
        if e.get("tipo") in tipos:
            self.cmb_tipo.setCurrentIndex(tipos.index(e["tipo"]))

    def _guardar(self):
        if not self.inp_titulo.text().strip():
            QMessageBox.warning(self,"Atenção","O título é obrigatório."); return
        d = {
            "id": self.evento["id"] if self.evento else None,
            "titulo": self.inp_titulo.text().strip(),
            "tipo": self.cmb_tipo.currentText(),
            "data": self.dt_data.date().toString("yyyy-MM-dd"),
            "descricao": self.inp_descricao.toPlainText().strip()
        }
        self.dao.salvar_evento(d)
        self.accept()


class CalendarioWidget(QWidget):
    def __init__(self, dao, utilizador):
        super().__init__()
        self.dao = dao
        self.utilizador = utilizador
        self._ano = date.today().year
        self._mes = date.today().month
        self._eventos = []
        self._obras = []
        self._tarefas = []
        self._funcionarios = []
        self._build()
        self._carregar_dados()
        self._desenhar()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24,24,24,24); lay.setSpacing(16)

        nav = QHBoxLayout()
        tit = QLabel("📅  Calendário")
        tit.setStyleSheet("font-size:22px;font-weight:700;color:#1a2332;")
        nav.addWidget(tit); nav.addStretch()

        btn_prev = _btn("◀","btn_outline"); btn_prev.setFixedWidth(36)
        btn_prev.clicked.connect(self._mes_anterior)
        self.lbl_mes = QLabel()
        self.lbl_mes.setStyleSheet("font-size:16px;font-weight:700;color:#1a2332;min-width:180px;")
        self.lbl_mes.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_next = _btn("▶","btn_outline"); btn_next.setFixedWidth(36)
        btn_next.clicked.connect(self._mes_seguinte)
        btn_hoje = _btn("Hoje","btn_secondary"); btn_hoje.clicked.connect(self._ir_hoje)
        btn_novo = _btn("+ Evento","btn_primary"); btn_novo.clicked.connect(self._novo_evento)

        nav.addWidget(btn_prev); nav.addWidget(self.lbl_mes); nav.addWidget(btn_next)
        nav.addSpacing(16); nav.addWidget(btn_hoje); nav.addWidget(btn_novo)
        lay.addLayout(nav)

        leg = QHBoxLayout()
        for cor, txt in [(COR_OBRA,"🔨 Obra"),(COR_TAREFA,"✓ Tarefa"),(COR_EVENTO,"📌 Evento"),("#8e44ad","🎂 Aniversário")]:
            l = QLabel(f"<span style='color:{cor};font-weight:bold;'>■</span> {txt}")
            l.setStyleSheet("font-size:12px; margin-right:12px;")
            leg.addWidget(l)
        leg.addStretch()
        lay.addLayout(leg)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.cal_widget = QWidget()
        self.cal_layout = QVBoxLayout(self.cal_widget)
        self.cal_layout.setContentsMargins(0,0,0,0)
        self.scroll.setWidget(self.cal_widget)
        lay.addWidget(self.scroll)

    def _carregar_dados(self):
        try: self._eventos = self.dao.listar_eventos(self._ano, self._mes)
        except: self._eventos = []
        try: self._obras = self.dao.listar_obras()
        except: self._obras = []
        try: self._tarefas = self.dao.listar_tarefas()
        except: self._tarefas = []
        try: self._funcionarios = self.dao.listar_utilizadores()
        except: self._funcionarios = []

    def _desenhar(self):
        while self.cal_layout.count():
            item = self.cal_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        self.lbl_mes.setText(f"{MESES_PT[self._mes-1]} {self._ano}")

        header = QWidget()
        hl = QGridLayout(header); hl.setSpacing(2); hl.setContentsMargins(0,0,0,0)
        for c, d in enumerate(DIAS_PT):
            lbl = QLabel(d)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cor = "#c0392b" if c >= 5 else "#1a2332"
            lbl.setStyleSheet(f"font-weight:700;font-size:12px;color:{cor};padding:4px;")
            hl.addWidget(lbl, 0, c)
        self.cal_layout.addWidget(header)

        hoje = date.today()
        mapa = {}

        for o in self._obras:
            dp = str(o.get("data_prevista",""))[:10]
            if dp and dp.startswith(f"{self._ano}-{self._mes:02d}"):
                dia = int(dp[8:10])
                mapa.setdefault(dia,[]).append(("obra", f"🔨 {o.get('cliente_nome','')[:15]}", COR_OBRA, o))

        for t in self._tarefas:
            dl = str(t.get("data_limite",""))[:10]
            if dl and dl.startswith(f"{self._ano}-{self._mes:02d}"):
                dia = int(dl[8:10])
                mapa.setdefault(dia,[]).append(("tarefa", f"✓ {t.get('titulo','')[:15]}", COR_TAREFA, t))

        for f in self._funcionarios:
            dn = str(f.get("data_nascimento",""))[:10]
            if dn and len(dn)==10:
                mes_nasc = int(dn[5:7])
                dia_nasc = int(dn[8:10])
                if mes_nasc == self._mes:
                    idade = self._ano - int(dn[:4])
                    mapa.setdefault(dia_nasc,[]).append(("aniversario", f"🎂 {f.get('nome','').split()[0]} ({idade})", "#8e44ad", f))

        for e in self._eventos:
            de = str(e.get("data",""))[:10]
            if de and de.startswith(f"{self._ano}-{self._mes:02d}"):
                dia = int(de[8:10])
                mapa.setdefault(dia,[]).append(("evento", f"📌 {e.get('titulo','')[:15]}", COR_EVENTO, e))

        grid = QWidget()
        gl = QGridLayout(grid); gl.setSpacing(4); gl.setContentsMargins(0,0,0,0)

        primeiro_dia, total_dias = calendar.monthrange(self._ano, self._mes)
        col = primeiro_dia
        row = 0

        for dia in range(1, total_dias + 1):
            d = date(self._ano, self._mes, dia)
            e_hoje = (d == hoje)
            e_fim_semana = col >= 5

            cell = QFrame()
            cell.setFrameShape(QFrame.Shape.StyledPanel)
            cell_lay = QVBoxLayout(cell)
            cell_lay.setContentsMargins(4,4,4,4); cell_lay.setSpacing(2)
            cell.setMinimumHeight(80)
            cell.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

            if e_hoje:
                cell.setStyleSheet("QFrame{background:#fff3e0;border:2px solid #d4560a;border-radius:6px;}")
            elif e_fim_semana:
                cell.setStyleSheet("QFrame{background:#fafafa;border:1px solid #e0e0e0;border-radius:6px;}")
            else:
                cell.setStyleSheet(f"QFrame{{background:{CORES['cartao']};border:1px solid {CORES['alum']};border-radius:6px;}}")

            lbl_dia = QLabel(str(dia))
            cor_dia = COR_HOJE if e_hoje else ("#c0392b" if e_fim_semana else "#1a2332")
            lbl_dia.setStyleSheet(f"font-weight:{'800' if e_hoje else '600'};font-size:13px;color:{cor_dia};")
            cell_lay.addWidget(lbl_dia)

            for tipo, label, cor, obj in mapa.get(dia, [])[:3]:
                ev = QLabel(label)
                ev.setStyleSheet(f"background:{cor};color:white;border-radius:3px;font-size:10px;padding:1px 4px;")
                ev.setCursor(Qt.CursorShape.PointingHandCursor)
                ev.mousePressEvent = lambda e, t=tipo, o=obj: self._clique_evento(t, o)
                cell_lay.addWidget(ev)

            if len(mapa.get(dia,[])) > 3:
                mais = QLabel(f"+{len(mapa[dia])-3} mais")
                mais.setStyleSheet("color:#666;font-size:10px;")
                cell_lay.addWidget(mais)

            cell_lay.addStretch()
            cell.mousePressEvent = lambda e, d=d: self._clique_dia(d) if not e.isAccepted() else None
            gl.addWidget(cell, row, col)
            col += 1
            if col > 6:
                col = 0; row += 1

        self.cal_layout.addWidget(grid)
        self.cal_layout.addStretch()

    def _clique_evento(self, tipo, obj):
        if tipo == "evento":
            dlg = EventoDialog(self.dao, self, evento=obj)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                self._carregar_dados(); self._desenhar()
        elif tipo == "obra":
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, f"🔨 Obra — {obj.get('numero','')}",
                f"<b>Cliente:</b> {obj.get('cliente_nome','')}<br>"
                f"<b>Descrição:</b> {obj.get('descricao','')}<br>"
                f"<b>Estado:</b> {obj.get('estado','')}<br>"
                f"<b>Data prevista:</b> {str(obj.get('data_prevista',''))[:10]}<br>"
                f"<b>Orçamento:</b> {float(obj.get('valor_orcamento',0)):.2f} €")
        elif tipo == "aniversario":
            from PyQt6.QtWidgets import QMessageBox
            dn = str(obj.get("data_nascimento",""))[:10]
            idade = self._ano - int(dn[:4]) if dn else "?"
            QMessageBox.information(self, f"🎂 Aniversário",
                f"<b>{obj.get('nome','')}</b> faz {idade} anos hoje!<br>"
                f"<b>Especialidade:</b> {obj.get('especialidade','') or '—'}<br>"
                f"<b>Telemóvel:</b> {obj.get('telemovel','') or '—'}")
        elif tipo == "tarefa":
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, f"✓ Tarefa — {obj.get('titulo','')}",
                f"<b>Categoria:</b> {obj.get('categoria','')}<br>"
                f"<b>Estado:</b> {obj.get('estado','')}<br>"
                f"<b>Prioridade:</b> {obj.get('prioridade','')}<br>"
                f"<b>Atribuído a:</b> {obj.get('atribuido_nome','')}<br>"
                f"<b>Data limite:</b> {str(obj.get('data_limite',''))[:10]}<br>"
                f"<b>Descrição:</b> {obj.get('descricao','') or '—'}")

    def _clique_dia(self, d):
        dlg = EventoDialog(self.dao, self, data_inicial=d)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._carregar_dados(); self._desenhar()

    def _novo_evento(self):
        dlg = EventoDialog(self.dao, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._carregar_dados(); self._desenhar()

    def _mes_anterior(self):
        self._mes -= 1
        if self._mes < 1: self._mes = 12; self._ano -= 1
        self._carregar_dados(); self._desenhar()

    def _mes_seguinte(self):
        self._mes += 1
        if self._mes > 12: self._mes = 1; self._ano += 1
        self._carregar_dados(); self._desenhar()

    def _ir_hoje(self):
        self._ano = date.today().year
        self._mes = date.today().month
        self._carregar_dados(); self._desenhar()

    def refresh(self):
        self._carregar_dados(); self._desenhar()
