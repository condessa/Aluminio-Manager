from PyQt6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QLineEdit,
    QTableWidget,QTableWidgetItem,QHeaderView,QDialog,QFormLayout,QComboBox,QDoubleSpinBox,
    QDateEdit,QTextEdit,QMessageBox,QFrame,QCheckBox)
from PyQt6.QtCore import Qt,QDate
CORES={"aco":"#1a2332","aco_mid":"#2c3e55","alum":"#e8edf2","alum_mid":"#c8d4de","branco":"#f8fafc","cinza":"#6b7c8e","laranja":"#d4560a","danger":"#c0392b","success":"#1e7e44","warning":"#b8700a"}
CATS=["Material","Mão de obra","Obra","Equipamento","Combustível","Fornecedor","Subcontratado","Impostos","Outro"]
METODOS=["numerario","transferencia","cheque","mb","mbway","outro"]
def _btn(t,o): b=QPushButton(t); b.setObjectName(o); b.setCursor(Qt.CursorShape.PointingHandCursor); return b
class FinanceiroDialog(QDialog):
    def __init__(self,dao,user,mov=None,parent=None):
        super().__init__(parent); self.dao=dao; self.user=user; self.mov=mov
        self.setWindowTitle("Novo Movimento" if not mov else "Editar Movimento"); self.setMinimumWidth(480)
        from PyQt6.QtWidgets import QDialogButtonBox
        lay=QVBoxLayout(self); lay.setContentsMargins(20,20,20,20); lay.setSpacing(10)
        # tipo radio
        tipo_w=QWidget(); tl=QHBoxLayout(tipo_w); tl.setContentsMargins(0,0,0,0)
        self.cmb_tipo=QComboBox(); self.cmb_tipo.addItems(["receita","despesa"])
        if mov: self.cmb_tipo.setCurrentText(mov.get("tipo","receita"))
        tl.addWidget(QLabel("Tipo:")); tl.addWidget(self.cmb_tipo); tl.addStretch(); lay.addWidget(tipo_w)
        fl=QFormLayout(); fl.setSpacing(9)
        self.inp_desc=QLineEdit(); self.inp_desc.setPlaceholderText("Descrição do movimento")
        self.spn_val=QDoubleSpinBox(); self.spn_val.setMaximum(999999); self.spn_val.setSuffix(" €"); self.spn_val.setDecimals(2)
        self.dt_mov=QDateEdit(QDate.currentDate()); self.dt_mov.setCalendarPopup(True)
        self.cmb_cat=QComboBox(); [self.cmb_cat.addItem(c) for c in CATS]
        self.cmb_metodo=QComboBox(); [self.cmb_metodo.addItem(m) for m in METODOS]
        self.inp_fatura=QLineEdit(); self.inp_fatura.setPlaceholderText("Nº fatura (opcional)")
        self.cmb_cli=QComboBox(); self.cmb_cli.addItem("— Sem cliente —",None)
        self.cmb_obra=QComboBox(); self.cmb_obra.addItem("— Sem obra —",None)
        self.inp_notas=QTextEdit(); self.inp_notas.setMaximumHeight(60)
        try:
            for c in self.dao.listar_clientes(): self.cmb_cli.addItem(c["nome"],c["id"])
            for o in self.dao.listar_obras(): self.cmb_obra.addItem(f"{o['numero']} — {o['descricao'][:40]}",o["id"])
        except: pass
        for lbl,w in [("Descrição *",self.inp_desc),("Valor *",self.spn_val),("Data",self.dt_mov),
                      ("Categoria",self.cmb_cat),("Método pag.",self.cmb_metodo),("Nº Fatura",self.inp_fatura),
                      ("Cliente",self.cmb_cli),("Obra",self.cmb_obra),("Notas",self.inp_notas)]:
            fl.addRow(lbl,w)
        lay.addLayout(fl)
        bb=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._guardar); bb.rejected.connect(self.reject); lay.addWidget(bb)
        if mov: self._preencher()
    def _preencher(self):
        m=self.mov; self.inp_desc.setText(m.get("descricao","")); self.spn_val.setValue(float(m.get("valor",0)))
        if m.get("data_mov"):
            try: self.dt_mov.setDate(QDate.fromString(str(m["data_mov"]),"yyyy-MM-dd"))
            except: pass
        self.cmb_cat.setCurrentText(m.get("categoria","Material"))
        self.cmb_metodo.setCurrentText(m.get("metodo_pag","numerario"))
        self.inp_fatura.setText(m.get("fatura_num",""))
        self.inp_notas.setPlainText(m.get("notas",""))
        for i in range(self.cmb_cli.count()):
            if self.cmb_cli.itemData(i)==m.get("cliente_id"): self.cmb_cli.setCurrentIndex(i); break
    def _guardar(self):
        if not self.inp_desc.text().strip() or self.spn_val.value()<=0:
            QMessageBox.warning(self,"Erro","Descrição e valor são obrigatórios."); return
        d={"tipo":self.cmb_tipo.currentText(),"descricao":self.inp_desc.text().strip(),
           "valor":self.spn_val.value(),"data_mov":self.dt_mov.date().toString("yyyy-MM-dd"),
           "categoria":self.cmb_cat.currentText(),"metodo_pag":self.cmb_metodo.currentText(),
           "fatura_num":self.inp_fatura.text(),"cliente_id":self.cmb_cli.currentData(),
           "obra_id":self.cmb_obra.currentData(),"notas":self.inp_notas.toPlainText(),"pago":1}
        if self.mov: d["id"]=self.mov["id"]
        try: self.dao.salvar_financeiro(d); self.accept()
        except Exception as e: QMessageBox.critical(self,"Erro",str(e))
class FinanceiroWidget(QWidget):
    def __init__(self,dao,user): super().__init__(); self.dao=dao; self.user=user; self._build()
    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(0,0,0,0)
        # Hero saldo
        self.hero=QFrame(); self.hero.setStyleSheet(f"background:{CORES['aco']};border-radius:0;")
        hl=QHBoxLayout(self.hero); hl.setContentsMargins(22,16,22,16)
        self.lbl_saldo=QLabel("0 €"); self.lbl_saldo.setStyleSheet(f"font-size:32px;font-weight:800;color:white;")
        self.lbl_rec=QLabel("Receitas: 0 €"); self.lbl_rec.setStyleSheet(f"font-size:12px;color:rgba(255,255,255,.7);")
        self.lbl_des=QLabel("Despesas: 0 €"); self.lbl_des.setStyleSheet(f"font-size:12px;color:rgba(255,255,255,.7);")
        iv=QVBoxLayout(); iv.addWidget(self.lbl_rec); iv.addWidget(self.lbl_des)
        hl.addWidget(QLabel("💶  Saldo:").setStyleSheet if False else QLabel("💶  Saldo:")); 
        hl.addWidget(self.lbl_saldo); hl.addSpacing(40); hl.addLayout(iv); hl.addStretch()
        lay.addWidget(self.hero)
        fb=QWidget(); fb.setStyleSheet(f"background:{CORES['branco']};border-bottom:1px solid {CORES['alum_mid']};")
        fl=QHBoxLayout(fb); fl.setContentsMargins(16,10,16,10); fl.setSpacing(10)
        self.inp_f=QLineEdit(); self.inp_f.setPlaceholderText("🔍  Pesquisar..."); self.inp_f.setMaximumWidth(220)
        self.inp_f.textChanged.connect(self.refresh)
        self.cmb_tipo=QComboBox(); self.cmb_tipo.addItem("Todos",None); self.cmb_tipo.addItem("Receitas","receita"); self.cmb_tipo.addItem("Despesas","despesa")
        self.cmb_tipo.currentIndexChanged.connect(self.refresh)
        fl.addWidget(self.inp_f); fl.addWidget(self.cmb_tipo); fl.addStretch(); lay.addWidget(fb)
        self.table=QTableWidget(); self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Data","Tipo","Categoria","Descrição","Valor","Obra","Ações"])
        self.table.horizontalHeader().setSectionResizeMode(3,QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False); lay.addWidget(self.table)
    def refresh(self):
        try:
            res=self.dao.resumo_financeiro()
            self.lbl_saldo.setText(f"{res['saldo']:.2f} €")
            self.lbl_saldo.setStyleSheet(f"font-size:32px;font-weight:800;color:{'#d4edda' if res['saldo']>=0 else CORES['danger']};")
            self.lbl_rec.setText(f"Receitas: {res['receitas']:.2f} €")
            self.lbl_des.setText(f"Despesas: {res['despesas']:.2f} €")
        except: pass
        try: movs=self.dao.listar_financeiro(self.inp_f.text(),self.cmb_tipo.currentData())
        except: movs=[]
        self.table.setRowCount(len(movs))
        for r,m in enumerate(movs):
            vals=[str(m.get("data_mov","—")),"",m.get("categoria","—"),m.get("descricao",""),
                  f"{float(m.get('valor',0)):.2f} €",m.get("obra_numero","—")]
            for c,v in enumerate(vals):
                item=QTableWidgetItem(v); item.setData(Qt.ItemDataRole.UserRole,m["id"])
                self.table.setItem(r,c,item)
            is_rec=m["tipo"]=="receita"; bg=("#d4edda","#1e7e44") if is_rec else ("#fde8e0","#c0392b")
            tl=QLabel("↑ Receita" if is_rec else "↓ Despesa"); tl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tl.setStyleSheet(f"background:{bg[0]};color:{bg[1]};border-radius:10px;padding:2px 8px;font-size:11px;font-weight:600;margin:4px;")
            self.table.setCellWidget(r,1,tl)
            acoes=QWidget(); al=QHBoxLayout(acoes); al.setContentsMargins(4,2,4,2); al.setSpacing(4)
            be=_btn("✏️","btn_outline"); be.setFixedHeight(26); be.clicked.connect(lambda _,mid=m["id"]: self._editar(mid))
            bd=_btn("🗑️","btn_danger"); bd.setFixedHeight(26); bd.clicked.connect(lambda _,mid=m["id"]: self._eliminar(mid))
            al.addWidget(be); al.addWidget(bd); self.table.setCellWidget(r,6,acoes)
        self.table.resizeRowsToContents()
    def novo(self):
        d=FinanceiroDialog(self.dao,self.user,parent=self)
        if d.exec()==QDialog.DialogCode.Accepted: self.refresh()
    def _editar(self,mid):
        try: m=self.dao.fetchone("SELECT * FROM financeiro WHERE id=%s",(mid,))
        except: return
        d=FinanceiroDialog(self.dao,self.user,m,parent=self)
        if d.exec()==QDialog.DialogCode.Accepted: self.refresh()
    def _eliminar(self,mid):
        r=QMessageBox.question(self,"Eliminar","Tem a certeza?",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if r==QMessageBox.StandardButton.Yes:
            try: self.dao.execute("DELETE FROM financeiro WHERE id=%s",(mid,)); self.refresh()
            except Exception as e: QMessageBox.critical(self,"Erro",str(e))
