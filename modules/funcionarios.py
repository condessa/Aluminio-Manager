from modules.validacoes import aplicar_mascara_telefone, aplicar_mascara_nif, aplicar_mascara_ss, aplicar_validacao_email
from PyQt6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QLineEdit,
    QTableWidget,QTableWidgetItem,QHeaderView,QDialog,QFormLayout,QComboBox,QDateEdit,
    QDoubleSpinBox,QTextEdit,QMessageBox)
from PyQt6.QtCore import Qt,QDate
CORES={"aco":"#1a2332","alum":"#e8edf2","alum_mid":"#c8d4de","branco":"#f8fafc","cinza":"#6b7c8e","laranja":"#d4560a","danger":"#c0392b","success":"#1e7e44"}
PERFIS=["admin","gestor","producao","vendas"]
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
        self.inp_pass=QLineEdit()
        self.inp_pass.setPlaceholderText("Deixar em branco para não alterar" if func else "Palavra-passe")
        self.inp_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.cmb_perfil=QComboBox(); [self.cmb_perfil.addItem(p) for p in PERFIS]
        self.inp_tlm=QLineEdit(); self.inp_email=QLineEdit()

        self.inp_esp=QLineEdit(); self.inp_esp.setPlaceholderText("ex: Corte, Montagem, Vidro...")
        self.dt_adm=QDateEdit(QDate.currentDate()); self.dt_adm.setCalendarPopup(True)
        self.dt_nasc=QDateEdit(); self.dt_nasc.setCalendarPopup(True); self.dt_nasc.setDisplayFormat("dd/MM/yyyy"); self.dt_nasc.setMinimumDate(QDate(1900,1,1)); self.dt_nasc.setDate(QDate(1900,1,1)); self.dt_nasc.setSpecialValueText("Não definido")
        self.spn_sal=QDoubleSpinBox(); self.spn_sal.setMaximum(99999); self.spn_sal.setSuffix(" €"); self.spn_sal.setDecimals(2)
        self.inp_nif=QLineEdit(); self.inp_ss=QLineEdit()
        self.inp_notas=QTextEdit(); self.inp_notas.setMaximumHeight(60)
        for lbl,w in [("Nome *",self.inp_nome),("Utilizador *",self.inp_user),("Palavra-passe",self.inp_pass),
                      ("Perfil",self.cmb_perfil),("Telemóvel",self.inp_tlm),("Email",self.inp_email),
                      ("Especialidade",self.inp_esp),("Data admissão",self.dt_adm),("Data nascimento",self.dt_nasc),("NIF *",self.inp_nif),("Nº Seg. Social *",self.inp_ss),
                      ("Salário base",self.spn_sal),("Notas",self.inp_notas)]:
            fl.addRow(lbl,w)
        lay.addLayout(fl)
        bb=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._guardar); bb.rejected.connect(self.reject); lay.addWidget(bb)
        aplicar_mascara_telefone(self.inp_tlm)
        aplicar_mascara_nif(self.inp_nif)
        aplicar_mascara_ss(self.inp_ss)
        aplicar_validacao_email(self.inp_email)
        if func: self._preencher()

    def _preencher(self):
        f=self.func
        self.inp_nome.setText(f.get("nome",""))
        self.inp_user.setText(f.get("username",""))
        self.cmb_perfil.setCurrentText(f.get("perfil","producao"))
        self.inp_tlm.setText(f.get("telemovel","") or "")
        self.inp_email.setText(f.get("email","") or "")
        self.inp_esp.setText(f.get("especialidade","") or "")
        self.inp_nif.setText(f.get("nif","") or "")
        self.inp_ss.setText(f.get("num_seg_social","") or "")
        self.inp_notas.setPlainText(f.get("notas","") or "")
        if f.get("data_admissao"):
            try: self.dt_adm.setDate(QDate.fromString(str(f["data_admissao"]),"yyyy-MM-dd"))
            except: pass
        if f.get("data_nascimento"):
            try: self.dt_nasc.setDate(QDate.fromString(str(f["data_nascimento"]),"yyyy-MM-dd"))
            except: pass
        if f.get("salario_base"):
            self.spn_sal.setValue(float(f.get("salario_base",0) or 0))

    def _guardar(self):
        if not self.inp_nome.text().strip() or not self.inp_user.text().strip():
            QMessageBox.warning(self,"Erro","Nome e utilizador são obrigatórios."); return
        if not self.func and not self.inp_pass.text():
            QMessageBox.warning(self,"Erro","Palavra-passe obrigatória para novo funcionário."); return
        email = self.inp_email.text().strip()
        if email and "@" not in email:
            QMessageBox.warning(self,"Erro","O email não é válido."); return
        tlm = self.inp_tlm.text().strip()
        if tlm and (len(tlm) != 9 or not tlm.isdigit()):
            QMessageBox.warning(self,"Erro","O telemóvel deve ter 9 dígitos."); return
        nif = self.inp_nif.text().strip()
        if not nif:
            QMessageBox.warning(self,"Erro","O NIF é obrigatório."); return
        if not nif.isdigit() or len(nif) != 9:
            QMessageBox.warning(self,"Erro","O NIF deve ter 9 dígitos."); return
        ss = self.inp_ss.text().strip()
        if not ss:
            QMessageBox.warning(self,"Erro","O Nº de Segurança Social é obrigatório."); return
        if not ss.isdigit() or len(ss) != 11:
            QMessageBox.warning(self,"Erro","O Nº de Segurança Social deve ter 11 dígitos."); return
        d={"nome":self.inp_nome.text().strip(),"username":self.inp_user.text().strip(),
           "perfil":self.cmb_perfil.currentText(),"ativo":1,
           "telemovel":self.inp_tlm.text(),"email":self.inp_email.text(),
           "especialidade":self.inp_esp.text(),"nif":self.inp_nif.text(),
           "num_seg_social":self.inp_ss.text(),
           "data_admissao":self.dt_adm.date().toString("yyyy-MM-dd"),
           "data_nascimento":self.dt_nasc.date().toString("yyyy-MM-dd") if self.dt_nasc.date() != QDate(1900,1,1) else None,
           "salario_base":self.spn_sal.value(),"notas":self.inp_notas.toPlainText()}
        if self.inp_pass.text(): d["password"]=self.inp_pass.text()
        if self.func: d["id"]=self.func["id"]
        try:
            self.dao.salvar_utilizador(d)
            self.accept()
        except Exception as e:
            import traceback
            QMessageBox.critical(self,"Erro",traceback.format_exc())

class FuncionariosWidget(QWidget):
    def __init__(self,dao,user): super().__init__(); self.dao=dao; self.user=user; self._build()

    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(0,0,0,0)
        fb=QWidget(); fb.setStyleSheet(f"background:{CORES['branco']};border-bottom:1px solid {CORES['alum_mid']};")
        fl=QHBoxLayout(fb); fl.setContentsMargins(16,10,16,10)
        self.inp_f=QLineEdit(); self.inp_f.setPlaceholderText("🔍  Pesquisar por nome...")
        self.inp_f.setMaximumWidth(280); self.inp_f.textChanged.connect(self.refresh)
        self.chk_inativos=QComboBox()
        self.chk_inativos.addItems(["Só activos","Todos","Só inactivos"])
        self.chk_inativos.currentIndexChanged.connect(self.refresh)
        fl.addWidget(self.inp_f); fl.addWidget(self.chk_inativos); fl.addStretch()
        lay.addWidget(fb)
        self.table=QTableWidget(); self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Nome","Utilizador","Perfil","Especialidade","Telemóvel","Estado","Ações"])
        hh=self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(1,110)
        self.table.setColumnWidth(2,90)
        self.table.setColumnWidth(3,120)
        self.table.setColumnWidth(4,100)
        self.table.setColumnWidth(5,90)
        self.table.setColumnWidth(6,100)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(lambda idx: self._editar(self.table.item(idx.row(),0).data(Qt.ItemDataRole.UserRole)))
        lay.addWidget(self.table)

    def refresh(self):
        filtro=self.inp_f.text().strip()
        mostrar=self.chk_inativos.currentIndex()
        try:
            sql="SELECT u.* FROM utilizadores u WHERE 1=1"
            params=[]
            if mostrar==0: sql+=" AND u.ativo=1"
            elif mostrar==2: sql+=" AND u.ativo=0"
            if filtro: sql+=" AND u.nome LIKE %s"; params.append(f"%{filtro}%")
            sql+=" ORDER BY u.nome"
            funcs=self.dao.fetchall(sql,params)
        except: funcs=[]
        self.table.setRowCount(len(funcs))
        PERFIL_COR={"admin":("#fde8e0","#c0392b"),"gestor":("#fff3cd","#b8700a"),
                    "producao":("#d4edda","#1e7e44"),"vendas":("#e8f0fa","#1a4a8a")}
        for r,f in enumerate(funcs):
            vals=[f["nome"],f.get("username",""),
                  "",
                  f.get("especialidade","") or "—",
                  f.get("telemovel","") or "—",
                  ""]
            for c,v in enumerate(vals):
                item=QTableWidgetItem(v); item.setData(Qt.ItemDataRole.UserRole,f["id"])
                self.table.setItem(r,c,item)
            bg,fg=PERFIL_COR.get(f.get("perfil","producao"),("#e8edf2","#4a6080"))
            rl=QLabel(f.get("perfil","—")); rl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            rl.setStyleSheet(f"background:{bg};color:{fg};border-radius:10px;padding:2px 8px;font-size:11px;font-weight:600;margin:4px;")
            self.table.setCellWidget(r,2,rl)
            ativo=f.get("ativo",1)
            sl=QLabel("✅ Activo" if ativo else "❌ Inactivo"); sl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sl.setStyleSheet(f"background:{'#d4edda' if ativo else '#fde8e0'};color:{'#1e7e44' if ativo else '#c0392b'};border-radius:10px;padding:2px 8px;font-size:11px;font-weight:600;margin:4px;")
            self.table.setCellWidget(r,5,sl)
            acoes=QWidget(); al=QHBoxLayout(acoes); al.setContentsMargins(4,2,4,2); al.setSpacing(4)
            be=_btn("✏️","btn_outline"); be.setFixedHeight(26); be.setToolTip("Editar")
            be.clicked.connect(lambda _,fid=f["id"]: self._editar(fid))
            if ativo:
                bd=_btn("🚫","btn_danger"); bd.setFixedHeight(26); bd.setToolTip("Desactivar")
                bd.clicked.connect(lambda _,fid=f["id"]: self._desativar(fid))
            else:
                bd=_btn("✅","btn_outline"); bd.setFixedHeight(26); bd.setToolTip("Reactivar")
                bd.clicked.connect(lambda _,fid=f["id"]: self._reativar(fid))
            bdel=_btn("🗑️","btn_danger"); bdel.setFixedHeight(26); bdel.setToolTip("Eliminar permanentemente")
            bdel.clicked.connect(lambda _,fid=f["id"]: self._eliminar(fid))
            al.addWidget(be); al.addWidget(bd); al.addWidget(bdel)
            self.table.setCellWidget(r,6,acoes)
        self.table.resizeRowsToContents()

    def novo(self):
        d=FuncionarioDialog(self.dao,parent=self)
        if d.exec()==QDialog.DialogCode.Accepted: self.refresh()

    def _editar(self,fid):
        if not fid: return
        try: f=self.dao.fetchone("SELECT * FROM utilizadores WHERE id=%s",(fid,))
        except: return
        if not f: return
        d=FuncionarioDialog(self.dao,f,parent=self)
        if d.exec()==QDialog.DialogCode.Accepted: self.refresh()

    def _desativar(self,fid):
        r=QMessageBox.question(self,"Desactivar funcionário",
            "Marcar este funcionário como inactivo?\n(O registo é mantido mas o acesso é bloqueado.)",
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if r==QMessageBox.StandardButton.Yes:
            try:
                self.dao.execute("UPDATE utilizadores SET ativo=0 WHERE id=%s",(fid,))
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self,"Erro",str(e))

    def _reativar(self,fid):
        try:
            self.dao.execute("UPDATE utilizadores SET ativo=1 WHERE id=%s",(fid,))
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self,"Erro",str(e))

    def _eliminar(self,fid):
        r=QMessageBox.warning(self,"Eliminar permanentemente",
            "⚠️  Esta acção apaga o funcionário definitivamente e não pode ser desfeita.\n\nTem a certeza?",
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if r==QMessageBox.StandardButton.Yes:
            try:
                self.dao.execute("DELETE FROM utilizadores WHERE id=%s",(fid,))
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self,"Erro",str(e))
