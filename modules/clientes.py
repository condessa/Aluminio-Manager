from PyQt6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QLineEdit,
    QTableWidget,QTableWidgetItem,QHeaderView,QDialog,QFormLayout,QComboBox,QTextEdit,QMessageBox)
from PyQt6.QtCore import Qt
CORES={"aco":"#1a2332","alum":"#e8edf2","alum_mid":"#c8d4de","branco":"#f8fafc","cinza":"#6b7c8e","laranja":"#d4560a","danger":"#c0392b"}
def _btn(t,o): b=QPushButton(t); b.setObjectName(o); b.setCursor(Qt.CursorShape.PointingHandCursor); return b
class ClienteDialog(QDialog):
    def __init__(self,dao,cli=None,parent=None):
        super().__init__(parent); self.dao=dao; self.cli=cli
        self.setWindowTitle("Novo Cliente" if not cli else f"Editar — {cli['nome']}")
        self.setMinimumWidth(520); self.resize(540,480)
        from PyQt6.QtWidgets import QDialogButtonBox,QGroupBox
        lay=QVBoxLayout(self); lay.setContentsMargins(20,20,20,20); lay.setSpacing(10)
        fl=QFormLayout(); fl.setSpacing(9)
        self.inp_nome=QLineEdit(); self.inp_nif=QLineEdit()
        self.cmb_tipo=QComboBox(); self.cmb_tipo.addItems(["particular","empresa"])
        self.inp_morada=QLineEdit(); self.inp_local=QLineEdit(); self.inp_cp=QLineEdit()
        self.inp_tel=QLineEdit(); self.inp_tlm=QLineEdit(); self.inp_email=QLineEdit()
        self.inp_notas=QTextEdit(); self.inp_notas.setMaximumHeight(70)
        for lbl,w in [("Nome *",self.inp_nome),("NIF",self.inp_nif),("Tipo",self.cmb_tipo),
                      ("Morada",self.inp_morada),("Localidade",self.inp_local),("Cód. Postal",self.inp_cp),
                      ("Telefone",self.inp_tel),("Telemóvel",self.inp_tlm),("Email",self.inp_email),("Notas",self.inp_notas)]:
            fl.addRow(lbl,w)
        lay.addLayout(fl)
        bb=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._guardar); bb.rejected.connect(self.reject); lay.addWidget(bb)
        if cli: self._preencher()
    def _preencher(self):
        c=self.cli; self.inp_nome.setText(c.get("nome","")); self.inp_nif.setText(c.get("nif",""))
        self.cmb_tipo.setCurrentText(c.get("tipo","particular")); self.inp_morada.setText(c.get("morada",""))
        self.inp_local.setText(c.get("localidade","")); self.inp_cp.setText(c.get("cp",""))
        self.inp_tel.setText(c.get("telefone","")); self.inp_tlm.setText(c.get("telemovel",""))
        self.inp_email.setText(c.get("email","")); self.inp_notas.setPlainText(c.get("notas",""))
    def _guardar(self):
        if not self.inp_nome.text().strip(): QMessageBox.warning(self,"Erro","Preencha o nome."); return
        d={"nome":self.inp_nome.text().strip(),"nif":self.inp_nif.text(),"tipo":self.cmb_tipo.currentText(),
           "morada":self.inp_morada.text(),"localidade":self.inp_local.text(),"cp":self.inp_cp.text(),
           "telefone":self.inp_tel.text(),"telemovel":self.inp_tlm.text(),
           "email":self.inp_email.text(),"notas":self.inp_notas.toPlainText()}
        if self.cli: d["id"]=self.cli["id"]
        try: self.dao.salvar_cliente(d); self.accept()
        except Exception as e: QMessageBox.critical(self,"Erro",str(e))
class ClientesWidget(QWidget):
    def __init__(self,dao,user): super().__init__(); self.dao=dao; self.user=user; self._build()
    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(0,0,0,0)
        fb=QWidget(); fb.setStyleSheet(f"background:{CORES['branco']};border-bottom:1px solid {CORES['alum_mid']};")
        fl=QHBoxLayout(fb); fl.setContentsMargins(16,10,16,10)
        self.inp_f=QLineEdit(); self.inp_f.setPlaceholderText("🔍  Pesquisar por nome ou NIF...")
        self.inp_f.setMaximumWidth(300); self.inp_f.textChanged.connect(self.refresh)
        fl.addWidget(self.inp_f); fl.addStretch(); lay.addWidget(fb)
        self.table=QTableWidget(); self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Nome","NIF","Tipo","Localidade","Telefone","Email","Ações"])
        self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(lambda idx: self._editar(self.table.item(idx.row(),0).data(Qt.ItemDataRole.UserRole)))
        lay.addWidget(self.table)
    def refresh(self):
        try: clientes=self.dao.listar_clientes(self.inp_f.text())
        except: clientes=[]
        self.table.setRowCount(len(clientes))
        TIPO_COR={"particular":("#e8f0fa","#1a4a8a"),"empresa":("#d4edda","#1e6040")}
        for r,c in enumerate(clientes):
            vals=[c["nome"],c.get("nif","—"),"",c.get("localidade","—"),
                  c.get("telefone",c.get("telemovel","—")),c.get("email","—")]
            for col,v in enumerate(vals):
                item=QTableWidgetItem(v); item.setData(Qt.ItemDataRole.UserRole,c["id"])
                self.table.setItem(r,col,item)
            bg,fg=TIPO_COR.get(c.get("tipo","particular"),("#e8edf2","#4a6080"))
            tl=QLabel(c.get("tipo","—").title()); tl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tl.setStyleSheet(f"background:{bg};color:{fg};border-radius:10px;padding:2px 8px;font-size:11px;font-weight:600;margin:4px;")
            self.table.setCellWidget(r,2,tl)
            acoes=QWidget(); al=QHBoxLayout(acoes); al.setContentsMargins(4,2,4,2); al.setSpacing(4)
            be=_btn("✏️","btn_outline"); be.setFixedHeight(26); be.clicked.connect(lambda _,cid=c["id"]: self._editar(cid))
            bd=_btn("🗑️","btn_danger"); bd.setFixedHeight(26); bd.clicked.connect(lambda _,cid=c["id"]: self._eliminar(cid))
            al.addWidget(be); al.addWidget(bd); self.table.setCellWidget(r,6,acoes)
        self.table.resizeRowsToContents()
    def novo(self):
        d=ClienteDialog(self.dao,parent=self)
        if d.exec()==QDialog.DialogCode.Accepted: self.refresh()
    def _editar(self,cid):
        try: c=self.dao.get_cliente(cid)
        except: return
        d=ClienteDialog(self.dao,c,parent=self)
        if d.exec()==QDialog.DialogCode.Accepted: self.refresh()
    def _eliminar(self,cid):
        r=QMessageBox.question(self,"Eliminar","Tem a certeza?",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if r==QMessageBox.StandardButton.Yes:
            try: self.dao.eliminar_cliente(cid); self.refresh()
            except Exception as e: QMessageBox.critical(self,"Erro",str(e))
