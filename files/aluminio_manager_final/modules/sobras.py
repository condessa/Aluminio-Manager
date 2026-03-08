from PyQt6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QLineEdit,
    QTableWidget,QTableWidgetItem,QHeaderView,QDialog,QFormLayout,QComboBox,QDoubleSpinBox,
    QDateEdit,QTextEdit,QMessageBox)
from PyQt6.QtCore import Qt,QDate
CORES={"aco":"#1a2332","alum":"#e8edf2","alum_mid":"#c8d4de","branco":"#f8fafc","cinza":"#6b7c8e","danger":"#c0392b","success":"#1e7e44","warning":"#b8700a"}
EST_COR={"reutilizavel":("#d4edda","#1e7e44"),"desperdicio":("#fde8e0","#c0392b"),"vendido":("#e8f0fa","#1a4a8a")}
def _btn(t,o): b=QPushButton(t); b.setObjectName(o); b.setCursor(Qt.CursorShape.PointingHandCursor); return b
class SobraDialog(QDialog):
    def __init__(self,dao,user,sobra=None,parent=None):
        super().__init__(parent); self.dao=dao; self.user=user; self.sobra=sobra
        self.setWindowTitle("Registar Sobra/Desperdício"); self.setMinimumWidth(460)
        from PyQt6.QtWidgets import QDialogButtonBox
        lay=QVBoxLayout(self); lay.setContentsMargins(20,20,20,20); lay.setSpacing(10)
        fl=QFormLayout(); fl.setSpacing(9)
        self.cmb_mat=QComboBox(); self.cmb_mat.addItem("— Seleccionar material —",None)
        self.cmb_obra=QComboBox(); self.cmb_obra.addItem("— Sem obra —",None)
        self.spn_qtd=QDoubleSpinBox(); self.spn_qtd.setMaximum(99999); self.spn_qtd.setDecimals(3); self.spn_qtd.setMinimum(0.001)
        self.spn_comp=QDoubleSpinBox(); self.spn_comp.setMaximum(99999); self.spn_comp.setSuffix(" cm"); self.spn_comp.setDecimals(1)
        self.cmb_estado=QComboBox(); [self.cmb_estado.addItem(e) for e in ["reutilizavel","desperdicio","vendido"]]
        self.inp_local=QLineEdit(); self.inp_local.setPlaceholderText("ex: Prateleira A3")
        self.dt_reg=QDateEdit(QDate.currentDate()); self.dt_reg.setCalendarPopup(True)
        self.inp_notas=QTextEdit(); self.inp_notas.setMaximumHeight(60)
        try:
            for s in self.dao.listar_stock(): self.cmb_mat.addItem(f"{s['referencia']} — {s['descricao'][:40]}",s["id"])
            for o in self.dao.listar_obras(): self.cmb_obra.addItem(f"{o['numero']} — {o['descricao'][:40]}",o["id"])
        except: pass
        for lbl,w in [("Material *",self.cmb_mat),("Origem (Obra)",self.cmb_obra),("Quantidade *",self.spn_qtd),
                      ("Comprimento",self.spn_comp),("Estado",self.cmb_estado),("Localização",self.inp_local),
                      ("Data",self.dt_reg),("Notas",self.inp_notas)]:
            fl.addRow(lbl,w)
        lay.addLayout(fl)
        bb=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._guardar); bb.rejected.connect(self.reject); lay.addWidget(bb)
        if sobra: self._preencher()
    def _preencher(self):
        s=self.sobra; self.spn_qtd.setValue(float(s.get("quantidade",0)))
        self.spn_comp.setValue(float(s.get("comprimento_cm",0) or 0))
        self.cmb_estado.setCurrentText(s.get("estado","reutilizavel"))
        self.inp_local.setText(s.get("localizacao","")); self.inp_notas.setPlainText(s.get("notas",""))
        if s.get("data_registo"):
            try: self.dt_reg.setDate(QDate.fromString(str(s["data_registo"]),"yyyy-MM-dd"))
            except: pass
    def _guardar(self):
        if not self.cmb_mat.currentData(): QMessageBox.warning(self,"Erro","Seleccione um material."); return
        d={"stock_id":self.cmb_mat.currentData(),"obra_id":self.cmb_obra.currentData(),
           "quantidade":self.spn_qtd.value(),"comprimento_cm":self.spn_comp.value() or None,
           "estado":self.cmb_estado.currentText(),"localizacao":self.inp_local.text(),
           "data_registo":self.dt_reg.date().toString("yyyy-MM-dd"),"notas":self.inp_notas.toPlainText()}
        if self.sobra: d["id"]=self.sobra["id"]
        try: self.dao.salvar_sobra(d); self.accept()
        except Exception as e: QMessageBox.critical(self,"Erro",str(e))
class SobrasWidget(QWidget):
    def __init__(self,dao,user): super().__init__(); self.dao=dao; self.user=user; self._build()
    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(0,0,0,0)
        fb=QWidget(); fb.setStyleSheet(f"background:{CORES['branco']};border-bottom:1px solid {CORES['alum_mid']};")
        fl=QHBoxLayout(fb); fl.setContentsMargins(16,10,16,10)
        self.cmb_est=QComboBox(); self.cmb_est.addItem("Todos",None)
        [self.cmb_est.addItem(e,e) for e in ["reutilizavel","desperdicio","vendido"]]
        self.cmb_est.currentIndexChanged.connect(self.refresh)
        fl.addWidget(QLabel("Estado:")); fl.addWidget(self.cmb_est); fl.addStretch(); lay.addWidget(fb)
        self.table=QTableWidget(); self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Material","Ref.","Quantidade","Comprimento","Estado","Obra","Ações"])
        self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False); lay.addWidget(self.table)
    def refresh(self):
        try: sobras=self.dao.listar_sobras(self.cmb_est.currentData())
        except: sobras=[]
        self.table.setRowCount(len(sobras))
        for r,s in enumerate(sobras):
            comp=f"{s['comprimento_cm']} cm" if s.get("comprimento_cm") else "—"
            vals=[s.get("material","—"),s.get("referencia","—"),f"{s['quantidade']} {s.get('unidade','')}",comp,"",s.get("obra_numero","—")]
            for c,v in enumerate(vals):
                item=QTableWidgetItem(v); item.setData(Qt.ItemDataRole.UserRole,s["id"]); self.table.setItem(r,c,item)
            bg,fg=EST_COR.get(s["estado"],("#e8edf2","#4a6080"))
            el=QLabel(s["estado"]); el.setAlignment(Qt.AlignmentFlag.AlignCenter)
            el.setStyleSheet(f"background:{bg};color:{fg};border-radius:10px;padding:2px 8px;font-size:11px;font-weight:600;margin:4px;")
            self.table.setCellWidget(r,4,el)
            acoes=QWidget(); al=QHBoxLayout(acoes); al.setContentsMargins(4,2,4,2)
            be=_btn("✏️","btn_outline"); be.setFixedHeight(26); be.clicked.connect(lambda _,sid=s["id"]: self._editar(sid))
            bd=_btn("🗑️","btn_danger"); bd.setFixedHeight(26); bd.clicked.connect(lambda _,sid=s["id"]: self._eliminar(sid))
            al.addWidget(be); al.addWidget(bd); self.table.setCellWidget(r,6,acoes)
        self.table.resizeRowsToContents()
    def novo(self):
        d=SobraDialog(self.dao,self.user,parent=self)
        if d.exec()==QDialog.DialogCode.Accepted: self.refresh()
    def _editar(self,sid):
        try: s=self.dao.fetchone("SELECT * FROM sobras WHERE id=%s",(sid,))
        except: return
        d=SobraDialog(self.dao,self.user,s,parent=self)
        if d.exec()==QDialog.DialogCode.Accepted: self.refresh()
    def _eliminar(self,sid):
        r=QMessageBox.question(self,"Eliminar","Tem a certeza?",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if r==QMessageBox.StandardButton.Yes:
            try: self.dao.execute("DELETE FROM sobras WHERE id=%s",(sid,)); self.refresh()
            except Exception as e: QMessageBox.critical(self,"Erro",str(e))
