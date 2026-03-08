from PyQt6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QLineEdit,
    QTableWidget,QTableWidgetItem,QHeaderView,QDialog,QFormLayout,QComboBox,QDateEdit,
    QDoubleSpinBox,QTextEdit,QMessageBox)
from PyQt6.QtCore import Qt,QDate
CORES={"aco":"#1a2332","alum":"#e8edf2","alum_mid":"#c8d4de","branco":"#f8fafc","cinza":"#6b7c8e","laranja":"#d4560a","danger":"#c0392b","success":"#1e7e44"}
ROLES=["admin","gestor","operador","vendedor"]
def _btn(t,o): b=QPushButton(t); b.setObjectName(o); b.setCursor(Qt.CursorShape.PointingHandCursor); return b
class FuncionarioDialog(QDialog):
    def __init__(self,dao,func=None,parent=None):
        super().__init__(parent); self.dao=dao; self.func=func
        self.setWindowTitle("Novo Funcionário" if not func else "Editar Funcionário"); self.setMinimumWidth(500)
        from PyQt6.QtWidgets import QDialogButtonBox
        lay=QVBoxLayout(self); lay.setContentsMargins(20,20,20,20); lay.setSpacing(10)
        fl=QFormLayout(); fl.setSpacing(9)
        self.inp_nome=QLineEdit()
        self.inp_user=QLineEdit(); self.inp_user.setPlaceholderText("nome.apelido")
        self.inp_pass=QLineEdit(); self.inp_pass.setPlaceholderText("Deixar em branco para não alterar" if func else "Palavra-passe")
        self.inp_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.cmb_role=QComboBox(); [self.cmb_role.addItem(r) for r in ROLES]
        self.inp_tlm=QLineEdit(); self.inp_email=QLineEdit()
        self.inp_esp=QLineEdit(); self.inp_esp.setPlaceholderText("ex: Corte, Montagem, Vidro...")
        self.dt_adm=QDateEdit(QDate.currentDate()); self.dt_adm.setCalendarPopup(True)
        self.spn_sal=QDoubleSpinBox(); self.spn_sal.setMaximum(99999); self.spn_sal.setSuffix(" €"); self.spn_sal.setDecimals(2)
        self.inp_nif=QLineEdit(); self.inp_ss=QLineEdit()
        self.inp_notas=QTextEdit(); self.inp_notas.setMaximumHeight(60)
        for lbl,w in [("Nome *",self.inp_nome),("Utilizador *",self.inp_user),("Palavra-passe",self.inp_pass),
                      ("Perfil/Role",self.cmb_role),("Telemóvel",self.inp_tlm),("Email",self.inp_email),
                      ("Especialidade",self.inp_esp),("Data admissão",self.dt_adm),
                      ("Salário base",self.spn_sal),("NIF",self.inp_nif),("Nº Seg. Social",self.inp_ss),("Notas",self.inp_notas)]:
            fl.addRow(lbl,w)
        lay.addLayout(fl)
        bb=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._guardar); bb.rejected.connect(self.reject); lay.addWidget(bb)
        if func: self._preencher()
    def _preencher(self):
        f=self.func; self.inp_nome.setText(f.get("nome","")); self.inp_user.setText(f.get("username",""))
        self.cmb_role.setCurrentText(f.get("role","operador")); self.inp_tlm.setText(f.get("telemovel",""))
        self.inp_email.setText(f.get("email","")); self.inp_esp.setText(f.get("especialidade",""))
        self.inp_nif.setText(f.get("nif","")); self.inp_notas.setPlainText(f.get("notas",""))
    def _guardar(self):
        if not self.inp_nome.text().strip() or not self.inp_user.text().strip():
            QMessageBox.warning(self,"Erro","Nome e utilizador são obrigatórios."); return
        d={"nome":self.inp_nome.text().strip(),"username":self.inp_user.text().strip(),
           "role":self.cmb_role.currentText(),"telemovel":self.inp_tlm.text(),"email":self.inp_email.text(),"ativo":1}
        if self.inp_pass.text(): d["password"]=self.inp_pass.text()
        elif not self.func: QMessageBox.warning(self,"Erro","Palavra-passe obrigatória para novo utilizador."); return
        if self.func: d["id"]=self.func["id"]
        try:
            uid=self.dao.salvar_utilizador(d)
            fd={"utilizador_id":uid,"especialidade":self.inp_esp.text(),
                "data_admissao":self.dt_adm.date().toString("yyyy-MM-dd"),
                "salario_base":self.spn_sal.value(),"nif":self.inp_nif.text(),"ss_num":self.inp_ss.text()}
            self.dao.execute("INSERT INTO funcionarios (utilizador_id,especialidade,data_admissao,salario_base,nif,ss_num) VALUES(%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE especialidade=VALUES(especialidade),salario_base=VALUES(salario_base)",
                tuple(fd.values()))
            self.accept()
        except Exception as e: QMessageBox.critical(self,"Erro",str(e))
class FuncionariosWidget(QWidget):
    def __init__(self,dao,user): super().__init__(); self.dao=dao; self.user=user; self._build()
    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(0,0,0,0)
        self.table=QTableWidget(); self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Nome","Utilizador","Perfil","Especialidade","Telemóvel","Ações"])
        self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False); lay.addWidget(self.table)
    def refresh(self):
        try: funcs=self.dao.listar_utilizadores()
        except: funcs=[]
        self.table.setRowCount(len(funcs))
        ROLE_COR={"admin":("#fde8e0","#c0392b"),"gestor":("#fff3cd","#b8700a"),"operador":("#d4edda","#1e7e44"),"vendedor":("#e8f0fa","#1a4a8a")}
        for r,f in enumerate(funcs):
            vals=[f["nome"],f.get("username",""),"",f.get("especialidade","—"),f.get("telemovel","—")]
            for c,v in enumerate(vals):
                item=QTableWidgetItem(v); item.setData(Qt.ItemDataRole.UserRole,f["id"]); self.table.setItem(r,c,item)
            bg,fg=ROLE_COR.get(f["role"],("#e8edf2","#4a6080"))
            rl=QLabel(f["role"]); rl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            rl.setStyleSheet(f"background:{bg};color:{fg};border-radius:10px;padding:2px 8px;font-size:11px;font-weight:600;margin:4px;")
            self.table.setCellWidget(r,2,rl)
            acoes=QWidget(); al=QHBoxLayout(acoes); al.setContentsMargins(4,2,4,2); al.setSpacing(4)
            be=_btn("✏️","btn_outline"); be.setFixedHeight(26); be.clicked.connect(lambda _,fid=f["id"]: self._editar(fid))
            al.addWidget(be); self.table.setCellWidget(r,5,acoes)
        self.table.resizeRowsToContents()
    def novo(self):
        d=FuncionarioDialog(self.dao,parent=self)
        if d.exec()==QDialog.DialogCode.Accepted: self.refresh()
    def _editar(self,fid):
        try: f=self.dao.fetchone("SELECT u.*,fn.especialidade,fn.salario_base,fn.nif,fn.ss_num FROM utilizadores u LEFT JOIN funcionarios fn ON fn.utilizador_id=u.id WHERE u.id=%s",(fid,))
        except: return
        d=FuncionarioDialog(self.dao,f,parent=self)
        if d.exec()==QDialog.DialogCode.Accepted: self.refresh()
