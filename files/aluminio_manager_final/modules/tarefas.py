from PyQt6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,
    QLineEdit,QTableWidget,QTableWidgetItem,QHeaderView,QDialog,QFormLayout,
    QComboBox,QDateEdit,QTextEdit,QMessageBox)
from PyQt6.QtCore import Qt,QDate
CORES={"aco":"#1a2332","alum":"#e8edf2","alum_mid":"#c8d4de","branco":"#f8fafc","cinza":"#6b7c8e","laranja":"#d4560a","danger":"#c0392b","success":"#1e7e44","warning":"#b8700a"}
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
        t=self.tarefa; self.inp_titulo.setText(t.get("titulo","")); self.inp_desc.setPlainText(t.get("descricao",""))
        self.cmb_cat.setCurrentText(t.get("categoria","Outro")); self.cmb_pri.setCurrentText(t.get("prioridade","media"))
        self.cmb_estado.setCurrentText(t.get("estado","pendente"))
        if t.get("data_limite"):
            try: self.dt_limite.setDate(QDate.fromString(str(t["data_limite"]),"yyyy-MM-dd"))
            except: pass
    def _guardar(self):
        if not self.inp_titulo.text().strip(): QMessageBox.warning(self,"Erro","Título é obrigatório."); return
        d={"titulo":self.inp_titulo.text().strip(),"descricao":self.inp_desc.toPlainText(),
           "categoria":self.cmb_cat.currentText(),"prioridade":self.cmb_pri.currentText(),
           "estado":self.cmb_estado.currentText(),"atribuido_a":self.cmb_user.currentData(),
           "obra_id":self.cmb_obra.currentData(),"data_limite":self.dt_limite.date().toString("yyyy-MM-dd"),
           "created_by":self.user.get("id")}
        if self.tarefa: d["id"]=self.tarefa["id"]
        try: self.dao.salvar_tarefa(d); self.accept()
        except Exception as e: QMessageBox.critical(self,"Erro",str(e))
class TarefasWidget(QWidget):
    def __init__(self,dao,user): super().__init__(); self.dao=dao; self.user=user; self._build()
    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(0,0,0,0)
        fb=QWidget(); fb.setStyleSheet(f"background:{CORES['branco']};border-bottom:1px solid {CORES['alum_mid']};")
        fl=QHBoxLayout(fb); fl.setContentsMargins(16,10,16,10); fl.setSpacing(10)
        self.cmb_estado=QComboBox(); self.cmb_estado.addItem("Todas",None); [self.cmb_estado.addItem(e,e) for e in ESTADOS]
        self.cmb_estado.currentIndexChanged.connect(self.refresh)
        fl.addWidget(QLabel("Estado:")); fl.addWidget(self.cmb_estado); fl.addStretch(); lay.addWidget(fb)
        self.table=QTableWidget(); self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Título","Categoria","Prioridade","Estado","Atribuído a","Data Limite","Ações"])
        self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False); lay.addWidget(self.table)
    def refresh(self):
        try: tarefas=self.dao.listar_tarefas(self.cmb_estado.currentData())
        except: tarefas=[]
        self.table.setRowCount(len(tarefas))
        EST_COR={"pendente":("#e8edf2","#4a6080"),"em_curso":("#fff3cd","#b8700a"),"concluida":("#d4edda","#1e7e44")}
        for r,t in enumerate(tarefas):
            vals=[t["titulo"],t.get("categoria","—"),"","",t.get("atribuido_nome","—"),str(t.get("data_limite","—"))]
            for c,v in enumerate(vals):
                item=QTableWidgetItem(v); item.setData(Qt.ItemDataRole.UserRole,t["id"])
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
            bc=_btn("✓","btn_outline"); bc.setFixedHeight(26); bc.setToolTip("Concluir"); bc.clicked.connect(lambda _,tid=t["id"]: self._concluir(tid))
            be=_btn("✏️","btn_outline"); be.setFixedHeight(26); be.clicked.connect(lambda _,tid=t["id"]: self._editar(tid))
            bd=_btn("🗑️","btn_danger"); bd.setFixedHeight(26); bd.clicked.connect(lambda _,tid=t["id"]: self._eliminar(tid))
            al.addWidget(bc); al.addWidget(be); al.addWidget(bd); self.table.setCellWidget(r,6,acoes)
        self.table.resizeRowsToContents()
    def novo(self):
        d=TarefaDialog(self.dao,self.user,parent=self)
        if d.exec()==QDialog.DialogCode.Accepted: self.refresh()
    def _editar(self,tid):
        try: t=self.dao.fetchone("SELECT * FROM tarefas WHERE id=%s",(tid,))
        except: return
        d=TarefaDialog(self.dao,self.user,t,parent=self)
        if d.exec()==QDialog.DialogCode.Accepted: self.refresh()
    def _concluir(self,tid):
        try: self.dao.concluir_tarefa(tid); self.refresh()
        except Exception as e: QMessageBox.critical(self,"Erro",str(e))
    def _eliminar(self,tid):
        r=QMessageBox.question(self,"Eliminar","Tem a certeza?",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if r==QMessageBox.StandardButton.Yes:
            try: self.dao.execute("DELETE FROM tarefas WHERE id=%s",(tid,)); self.refresh()
            except Exception as e: QMessageBox.critical(self,"Erro",str(e))
