from PyQt6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,
    QLineEdit,QTableWidget,QTableWidgetItem,QHeaderView,QDialog,QFormLayout,
    QComboBox,QDateEdit,QTextEdit,QMessageBox)
from PyQt6.QtCore import Qt,QDate
from modules.temas import PALETA as CORES
PRIORIDADES=["baixa","media","alta","urgente"]
ESTADOS=["pendente","em_curso","concluida"]
PRI_COR={"baixa":("#d4edda","#1e7e44"),"media":("#e8f0fa","#1a4a8a"),"alta":("#fff3cd","#b8700a"),"urgente":("#fde8e0","#c0392b")}
CATS_T=["Produção","Manutenção","Entrega","Orçamento","Compras","Administrativo","Outro"]

def _btn(t,o): b=QPushButton(t); b.setObjectName(o); b.setCursor(Qt.CursorShape.PointingHandCursor); return b

class TarefaDialog(QDialog):
    def __init__(self,dao,user,tarefa=None,parent=None):
        super().__init__(parent); self.dao=dao; self.user=user; self.tarefa=tarefa
        self.setWindowTitle("Nova Tarefa" if not tarefa else "Editar Tarefa"); self.setMinimumWidth(460)
        from PyQt6.QtWidgets import QDialogButtonBox
        lay=QVBoxLayout(self); lay.setContentsMargins(20,20,20,20); lay.setSpacing(10)
        fl=QFormLayout(); fl.setSpacing(9)
        self.inp_titulo=QLineEdit(); self.inp_titulo.setPlaceholderText("Título da tarefa")
        self.inp_desc=QTextEdit(); self.inp_desc.setMaximumHeight(80); self.inp_desc.setPlaceholderText("Descrição...")
        self.cmb_cat=QComboBox(); [self.cmb_cat.addItem(c) for c in CATS_T]
        self.cmb_pri=QComboBox(); [self.cmb_pri.addItem(p) for p in PRIORIDADES]; self.cmb_pri.setCurrentText("media")
        self.cmb_estado=QComboBox(); [self.cmb_estado.addItem(e) for e in ESTADOS]
        self.cmb_user=QComboBox(); self.cmb_user.addItem("— Não atribuído —",None)
        self.cmb_obra=QComboBox(); self.cmb_obra.addItem("— Sem obra —",None)
        self.dt_limite=QDateEdit(QDate.currentDate().addDays(7)); self.dt_limite.setCalendarPopup(True)
        try:
            for u in self.dao.listar_utilizadores(): self.cmb_user.addItem(u["nome"],u["id"])
            for o in self.dao.listar_obras(): self.cmb_obra.addItem(f"{o['numero']} — {o['descricao'][:40]}",o["id"])
        except: pass
        for lbl,w in [("Título *",self.inp_titulo),("Descrição",self.inp_desc),("Categoria",self.cmb_cat),
                      ("Prioridade",self.cmb_pri),("Estado",self.cmb_estado),("Atribuir a",self.cmb_user),
                      ("Obra",self.cmb_obra),("Data limite",self.dt_limite)]:
            fl.addRow(lbl,w)
        lay.addLayout(fl)
        bb=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._guardar); bb.rejected.connect(self.reject); lay.addWidget(bb)
        if tarefa: self._preencher()

    def _preencher(self):
        t=self.tarefa; self.inp_titulo.setText(t.get("titulo","")); self.inp_desc.setPlainText(t.get("descricao","") or "")
        self.cmb_cat.setCurrentText(t.get("categoria","Outro")); self.cmb_pri.setCurrentText(t.get("prioridade","media"))
        self.cmb_estado.setCurrentText(t.get("estado","pendente"))
        if t.get("data_limite"):
            try: self.dt_limite.setDate(QDate.fromString(str(t["data_limite"]),"yyyy-MM-dd"))
            except: pass
        # Seleccionar utilizador atribuído
        if t.get("atribuido_a"):
            for i in range(self.cmb_user.count()):
                if self.cmb_user.itemData(i)==t["atribuido_a"]:
                    self.cmb_user.setCurrentIndex(i); break

    def _guardar(self):
        if not self.inp_titulo.text().strip(): QMessageBox.warning(self,"Erro","Título é obrigatório."); return
        d={"titulo":self.inp_titulo.text().strip(),"descricao":self.inp_desc.toPlainText(),
           "categoria":self.cmb_cat.currentText(),"prioridade":self.cmb_pri.currentText(),
           "estado":self.cmb_estado.currentText(),"atribuido_a":self.cmb_user.currentData(),
           "obra_id":self.cmb_obra.currentData(),"data_limite":self.dt_limite.date().toString("yyyy-MM-dd"),
           "criado_por":self.user.get("id")}
        if self.tarefa: d["id"]=self.tarefa["id"]
        try: self.dao.salvar_tarefa(d); self.accept()
        except Exception as e: QMessageBox.critical(self,"Erro",str(e))


class TarefasWidget(QWidget):
    def __init__(self,dao,user):
        super().__init__(); self.dao=dao; self.user=user
        self.perfil=user.get("perfil","")
        self.is_gestor = self.perfil in ("admin","gestor")
        self._build()

    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(0,0,0,0)

        # Barra de filtros + botão novo (só admin/gestor)
        fb=QWidget(); fb.setStyleSheet(f"background:{CORES['branco']};border-bottom:1px solid {CORES['alum_mid']};")
        fl=QHBoxLayout(fb); fl.setContentsMargins(16,10,16,10); fl.setSpacing(10)
        self.cmb_estado=QComboBox(); self.cmb_estado.addItem("Todas",None)
        [self.cmb_estado.addItem(e,e) for e in ESTADOS]
        self.cmb_estado.currentIndexChanged.connect(self.refresh)
        fl.addWidget(QLabel("Estado:")); fl.addWidget(self.cmb_estado)

        # Filtro "As minhas / Todas" para admin/gestor
        if self.is_gestor:
            self.cmb_filtro=QComboBox()
            self.cmb_filtro.addItem("Todas as tarefas","todas")
            self.cmb_filtro.addItem("Atribuídas a mim","minhas")
            self.cmb_filtro.currentIndexChanged.connect(self.refresh)
            fl.addWidget(QLabel("Mostrar:")); fl.addWidget(self.cmb_filtro)

        fl.addStretch()

        if not self.is_gestor:
            # Info para funcionários
            info=QLabel("👤  A mostrar as tarefas atribuídas a si")
            info.setStyleSheet(f"font-size:11px;color:{CORES['cinza']};font-style:italic;")
            fl.addWidget(info)

        lay.addWidget(fb)

        # Tabela
        self.table=QTableWidget(); self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Título","Categoria","Prioridade","Estado","Atribuído a","Data Limite","Ações"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(1, 110)  # Categoria
        self.table.setColumnWidth(2, 90)   # Prioridade
        self.table.setColumnWidth(3, 90)   # Estado
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(5, 100)  # Data Limite
        self.table.setColumnWidth(6, 90)   # Ações
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        lay.addWidget(self.table)

    def refresh(self):
        estado = self.cmb_estado.currentData()
        uid = self.user.get("id")

        # Filtro por perfil
        if self.is_gestor:
            filtro_minhas = hasattr(self,"cmb_filtro") and self.cmb_filtro.currentData()=="minhas"
            filtro_uid = uid if filtro_minhas else None
        else:
            # Funcionários só vêem as suas
            filtro_uid = uid

        try:
            if filtro_uid:
                tarefas=self.dao.fetchall(
                    "SELECT t.*, u.nome as atribuido_nome FROM tarefas t LEFT JOIN utilizadores u ON t.atribuido_a=u.id WHERE t.atribuido_a=%s" +
                    (" AND t.estado=%s" if estado else "") + " ORDER BY t.data_limite ASC",
                    (filtro_uid, estado) if estado else (filtro_uid,)
                )
            else:
                tarefas=self.dao.listar_tarefas(estado)
        except: tarefas=[]

        self.table.setRowCount(len(tarefas))
        EST_COR={"pendente":("#e8edf2","#4a6080"),"em_curso":("#fff3cd","#b8700a"),"concluida":("#d4edda","#1e7e44")}

        for r,t in enumerate(tarefas):
            vals=[t["titulo"],t.get("categoria","—"),"","",t.get("atribuido_nome","—"),str(t.get("data_limite","—"))]
            for c,v in enumerate(vals):
                item=QTableWidgetItem(str(v) if v else "—"); item.setData(Qt.ItemDataRole.UserRole,t["id"])
                self.table.setItem(r,c,item)
            bg_p,fg_p=PRI_COR.get(t["prioridade"],("#e8edf2","#4a6080"))
            pl=QLabel(t["prioridade"]); pl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pl.setStyleSheet(f"background:{bg_p};color:{fg_p};border-radius:10px;padding:2px 8px;font-size:11px;font-weight:600;margin:4px;")
            self.table.setCellWidget(r,2,pl)
            bg_e,fg_e=EST_COR.get(t["estado"],("#e8edf2","#4a6080"))
            el=QLabel(t["estado"].replace("_"," ").title()); el.setAlignment(Qt.AlignmentFlag.AlignCenter)
            el.setStyleSheet(f"background:{bg_e};color:{fg_e};border-radius:10px;padding:2px 8px;font-size:11px;font-weight:600;margin:4px;")
            self.table.setCellWidget(r,3,el)

            acoes=QWidget(); al=QHBoxLayout(acoes); al.setContentsMargins(4,2,4,2); al.setSpacing(4)
            if self.is_gestor:
                # Admin/gestor: concluir, editar, eliminar
                bc=_btn("✓","btn_outline"); bc.setFixedHeight(26); bc.setToolTip("Concluir")
                bc.clicked.connect(lambda _,tid=t["id"]: self._concluir(tid))
                be=_btn("✏️","btn_outline"); be.setFixedHeight(26)
                be.clicked.connect(lambda _,tid=t["id"]: self._editar(tid))
                bd=_btn("🗑️","btn_danger"); bd.setFixedHeight(26)
                bd.clicked.connect(lambda _,tid=t["id"]: self._eliminar(tid))
                al.addWidget(bc); al.addWidget(be); al.addWidget(bd)
            else:
                # Funcionários: só podem marcar como concluída
                bc=_btn("✓  Concluir","btn_outline"); bc.setFixedHeight(26)
                bc.setToolTip("Marcar como concluída")
                bc.clicked.connect(lambda _,tid=t["id"]: self._concluir(tid))
                if t["estado"]=="concluida":
                    bc.setEnabled(False)
                    bc.setStyleSheet("color:#9aaabb;")
                al.addWidget(bc)
            self.table.setCellWidget(r,6,acoes)
        self.table.resizeRowsToContents()

    def novo(self):
        if not self.is_gestor: return
        d=TarefaDialog(self.dao,self.user,parent=self)
        if d.exec()==QDialog.DialogCode.Accepted: self.refresh()

    def _editar(self,tid):
        if not self.is_gestor: return
        try: t=self.dao.fetchone("SELECT * FROM tarefas WHERE id=%s",(tid,))
        except: return
        d=TarefaDialog(self.dao,self.user,t,parent=self)
        if d.exec()==QDialog.DialogCode.Accepted: self.refresh()

    def _concluir(self,tid):
        try: self.dao.concluir_tarefa(tid); self.refresh()
        except Exception as e: QMessageBox.critical(self,"Erro",str(e))

    def _eliminar(self,tid):
        if not self.is_gestor: return
        r=QMessageBox.question(self,"Eliminar","Tem a certeza?",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if r==QMessageBox.StandardButton.Yes:
            try: self.dao.execute("DELETE FROM tarefas WHERE id=%s",(tid,)); self.refresh()
            except Exception as e: QMessageBox.critical(self,"Erro",str(e))
