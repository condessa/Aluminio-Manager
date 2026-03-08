from PyQt6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,
    QLineEdit,QTableWidget,QTableWidgetItem,QHeaderView,QDialog,QFormLayout,
    QComboBox,QDateEdit,QTextEdit,QFrame,QScrollArea,QTabWidget,QDoubleSpinBox,
    QGroupBox,QMessageBox,QSplitter)
from PyQt6.QtCore import Qt,QDate
from PyQt6.QtGui import QColor
CORES={"aco":"#1a2332","aco_mid":"#2c3e55","laranja":"#d4560a","alum":"#e8edf2","alum_mid":"#c8d4de","branco":"#f8fafc","cinza":"#6b7c8e","success":"#1e7e44","danger":"#c0392b","warning":"#b8700a","info":"#1a6fa8"}
ESTADOS=["orcamento","confirmada","em_producao","em_montagem","concluida","cancelada","em_espera"]
TIPOS=["porta","janela","marquise","porta_de_correr","gradeamento","portao","cobertura","outro"]
PRIORIDADES=["normal","urgente","critica"]
ESTADO_COR={"orcamento":("#e8edf2","#4a6080"),"confirmada":("#fff3cd","#b8700a"),"em_producao":("#d4edda","#1e7e44"),"em_montagem":("#e8f0fa","#1a6fa8"),"concluida":("#d4edda","#1e7e44"),"cancelada":("#fde8e0","#c0392b"),"em_espera":("#e8edf2","#6b7c8e")}
PRI_COR={"normal":("#e8edf2","#4a6080"),"urgente":("#fff3cd","#b8700a"),"critica":("#fde8e0","#c0392b")}

def _btn(txt,obj): b=QPushButton(txt); b.setObjectName(obj); b.setCursor(Qt.CursorShape.PointingHandCursor); return b

class ObraDialog(QDialog):
    def __init__(self,dao,user,obra=None,parent=None):
        super().__init__(parent); self.dao=dao; self.user=user; self.obra=obra
        self.setWindowTitle("Nova Obra" if not obra else f"Editar — {obra['numero']}")
        self.setMinimumWidth(620); self.resize(660,620)
        self._build()
        if obra: self._preencher()

    def _build(self):
        from PyQt6.QtWidgets import QDialogButtonBox
        lay=QVBoxLayout(self); lay.setContentsMargins(20,20,20,20); lay.setSpacing(12)
        tabs=QTabWidget(); lay.addWidget(tabs)
        # Tab 1 — Dados gerais
        t1=QWidget(); t1l=QFormLayout(t1); t1l.setSpacing(10)
        self.inp_num=QLineEdit(); self.inp_num.setReadOnly(bool(self.obra))
        self.inp_num.setText(self.dao.proximo_numero_obra() if not self.obra else self.obra["numero"])
        self.cmb_cli=QComboBox(); self._load_clientes()
        self.inp_desc=QLineEdit(); self.inp_desc.setPlaceholderText("Descrição da obra")
        self.cmb_tipo=QComboBox(); [self.cmb_tipo.addItem(t) for t in TIPOS]
        self.cmb_estado=QComboBox(); [self.cmb_estado.addItem(e) for e in ESTADOS]
        self.cmb_pri=QComboBox(); [self.cmb_pri.addItem(p) for p in PRIORIDADES]
        self.dt_entrada=QDateEdit(QDate.currentDate()); self.dt_entrada.setCalendarPopup(True)
        self.dt_prevista=QDateEdit(QDate.currentDate().addDays(30)); self.dt_prevista.setCalendarPopup(True)
        for lbl,w in [("Número",self.inp_num),("Cliente",self.cmb_cli),("Descrição",self.inp_desc),
                      ("Tipo",self.cmb_tipo),("Estado",self.cmb_estado),("Prioridade",self.cmb_pri),
                      ("Data entrada",self.dt_entrada),("Data prevista",self.dt_prevista)]:
            t1l.addRow(lbl,w)
        tabs.addTab(t1,"📋  Geral")
        # Tab 2 — Especificações
        t2=QWidget(); t2l=QFormLayout(t2); t2l.setSpacing(10)
        self.inp_cor=QLineEdit(); self.inp_cor.setPlaceholderText("ex: RAL 9016 Branco")
        self.inp_acab=QLineEdit(); self.inp_acab.setPlaceholderText("ex: Lacado, Termolacado, Anodizado")
        self.inp_vidro=QLineEdit(); self.inp_vidro.setPlaceholderText("ex: Duplo 4/16/4")
        self.inp_medidas=QTextEdit(); self.inp_medidas.setPlaceholderText("Medidas, quantidades, observações técnicas...")
        self.inp_medidas.setMaximumHeight(100)
        self.inp_morada=QLineEdit(); self.inp_morada.setPlaceholderText("Morada da instalação")
        for lbl,w in [("Cor / RAL",self.inp_cor),("Acabamento",self.inp_acab),("Vidro",self.inp_vidro),
                      ("Medidas/Qtds",self.inp_medidas),("Morada obra",self.inp_morada)]:
            t2l.addRow(lbl,w)
        tabs.addTab(t2,"📐  Especificações")
        # Tab 3 — Financeiro
        t3=QWidget(); t3l=QFormLayout(t3); t3l.setSpacing(10)
        self.inp_orc=QDoubleSpinBox(); self.inp_orc.setMaximum(999999); self.inp_orc.setSuffix(" €"); self.inp_orc.setDecimals(2)
        self.inp_fat=QDoubleSpinBox(); self.inp_fat.setMaximum(999999); self.inp_fat.setSuffix(" €"); self.inp_fat.setDecimals(2)
        self.inp_pago=QDoubleSpinBox(); self.inp_pago.setMaximum(999999); self.inp_pago.setSuffix(" €"); self.inp_pago.setDecimals(2)
        self.inp_notas=QTextEdit(); self.inp_notas.setPlaceholderText("Notas internas...")
        self.inp_notas.setMaximumHeight(80)
        for lbl,w in [("Orçamento",self.inp_orc),("Faturado",self.inp_fat),("Pago",self.inp_pago),("Notas",self.inp_notas)]:
            t3l.addRow(lbl,w)
        tabs.addTab(t3,"💶  Financeiro")
        # Botões
        bb=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._guardar); bb.rejected.connect(self.reject); lay.addWidget(bb)

    def _load_clientes(self):
        self.cmb_cli.addItem("— Sem cliente —",None)
        try:
            for c in self.dao.listar_clientes(): self.cmb_cli.addItem(c["nome"],c["id"])
        except: pass

    def _preencher(self):
        o=self.obra
        self.inp_desc.setText(o.get("descricao",""))
        idx=TIPOS.index(o["tipo_obra"]) if o.get("tipo_obra") in TIPOS else 0; self.cmb_tipo.setCurrentIndex(idx)
        idx=ESTADOS.index(o["estado"]) if o.get("estado") in ESTADOS else 0; self.cmb_estado.setCurrentIndex(idx)
        idx=PRIORIDADES.index(o["prioridade"]) if o.get("prioridade") in PRIORIDADES else 0; self.cmb_pri.setCurrentIndex(idx)
        if o.get("data_entrada"):
            try: self.dt_entrada.setDate(QDate.fromString(str(o["data_entrada"]),"yyyy-MM-dd"))
            except: pass
        if o.get("data_prevista"):
            try: self.dt_prevista.setDate(QDate.fromString(str(o["data_prevista"]),"yyyy-MM-dd"))
            except: pass
        self.inp_cor.setText(o.get("cor_perfil",""))
        self.inp_acab.setText(o.get("acabamento",""))
        self.inp_vidro.setText(o.get("vidro",""))
        self.inp_medidas.setPlainText(o.get("medidas",""))
        self.inp_morada.setText(o.get("morada_obra",""))
        self.inp_orc.setValue(float(o.get("valor_orcamento",0)))
        self.inp_fat.setValue(float(o.get("valor_faturado",0)))
        self.inp_pago.setValue(float(o.get("valor_pago",0)))
        self.inp_notas.setPlainText(o.get("notas",""))
        # cliente
        for i in range(self.cmb_cli.count()):
            if self.cmb_cli.itemData(i)==o.get("cliente_id"): self.cmb_cli.setCurrentIndex(i); break

    def _guardar(self):
        if not self.inp_desc.text().strip(): QMessageBox.warning(self,"Erro","Preencha a descrição."); return
        d={"descricao":self.inp_desc.text().strip(),"numero":self.inp_num.text().strip(),
           "cliente_id":self.cmb_cli.currentData(),"tipo_obra":self.cmb_tipo.currentText(),
           "estado":self.cmb_estado.currentText(),"prioridade":self.cmb_pri.currentText(),
           "data_entrada":self.dt_entrada.date().toString("yyyy-MM-dd"),
           "data_prevista":self.dt_prevista.date().toString("yyyy-MM-dd"),
           "cor_perfil":self.inp_cor.text(),"acabamento":self.inp_acab.text(),
           "vidro":self.inp_vidro.text(),"medidas":self.inp_medidas.toPlainText(),
           "morada_obra":self.inp_morada.text(),"valor_orcamento":self.inp_orc.value(),
           "valor_faturado":self.inp_fat.value(),"valor_pago":self.inp_pago.value(),
           "notas":self.inp_notas.toPlainText(),"responsavel_id":self.user.get("id")}
        if self.obra: d["id"]=self.obra["id"]
        try:
            oid=self.dao.salvar_obra(d)
            if not self.obra: self.dao.criar_fases_obra(oid)
            self.accept()
        except Exception as e: QMessageBox.critical(self,"Erro",str(e))

class ObrasWidget(QWidget):
    def __init__(self,dao,user): super().__init__(); self.dao=dao; self.user=user; self._build()
    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        # Filtros
        fbar=QWidget(); fbar.setStyleSheet(f"background:{CORES['branco']};border-bottom:1px solid {CORES['alum_mid']};")
        fl=QHBoxLayout(fbar); fl.setContentsMargins(16,10,16,10); fl.setSpacing(10)
        self.inp_filtro=QLineEdit(); self.inp_filtro.setPlaceholderText("🔍  Pesquisar obra, cliente...")
        self.inp_filtro.setMaximumWidth(260); self.inp_filtro.textChanged.connect(self.refresh)
        self.cmb_estado=QComboBox(); self.cmb_estado.addItem("Todos os estados",None)
        [self.cmb_estado.addItem(e,e) for e in ESTADOS]; self.cmb_estado.currentIndexChanged.connect(self.refresh)
        fl.addWidget(self.inp_filtro); fl.addWidget(self.cmb_estado); fl.addStretch()
        lay.addWidget(fbar)
        # Tabela
        self.table=QTableWidget(); self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["Número","Cliente","Descrição","Tipo","Estado","Prioridade","Data Entrada","Ações"])
        self.table.horizontalHeader().setSectionResizeMode(2,QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._abrir_detalhe)
        lay.addWidget(self.table)

    def refresh(self):
        filtro=self.inp_filtro.text(); estado=self.cmb_estado.currentData()
        try: obras=self.dao.listar_obras(filtro,estado)
        except: obras=[]
        self.table.setRowCount(len(obras))
        for r,o in enumerate(obras):
            bg_e,fg_e=ESTADO_COR.get(o["estado"],("#e8edf2","#4a6080"))
            bg_p,fg_p=PRI_COR.get(o["prioridade"],("#e8edf2","#4a6080"))
            vals=[o["numero"],o.get("cliente_nome","—"),o["descricao"],o.get("tipo_obra",""),
                  "","",(str(o["data_entrada"]) if o.get("data_entrada") else "—")]
            for c,v in enumerate(vals):
                item=QTableWidgetItem(v); item.setData(Qt.ItemDataRole.UserRole,o["id"])
                self.table.setItem(r,c,item)
            # badge estado
            est_lbl=QLabel(o["estado"].replace("_"," ").title())
            est_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            est_lbl.setStyleSheet(f"background:{bg_e};color:{fg_e};border-radius:10px;padding:2px 8px;font-size:11px;font-weight:600;margin:4px;")
            self.table.setCellWidget(r,4,est_lbl)
            pri_lbl=QLabel(o["prioridade"])
            pri_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pri_lbl.setStyleSheet(f"background:{bg_p};color:{fg_p};border-radius:10px;padding:2px 8px;font-size:11px;font-weight:600;margin:4px;")
            self.table.setCellWidget(r,5,pri_lbl)
            # ações
            acoes=QWidget(); al=QHBoxLayout(acoes); al.setContentsMargins(4,2,4,2); al.setSpacing(4)
            be=_btn("✏️","btn_outline"); be.setFixedHeight(26); be.setToolTip("Editar"); be.clicked.connect(lambda _,oid=o["id"]: self._editar(oid))
            bd=_btn("🗑️","btn_danger"); bd.setFixedHeight(26); bd.setToolTip("Eliminar"); bd.clicked.connect(lambda _,oid=o["id"]: self._eliminar(oid))
            bf=_btn("📋","btn_outline"); bf.setFixedHeight(26); bf.setToolTip("Fases"); bf.clicked.connect(lambda _,oid=o["id"]: self._fases(oid))
            al.addWidget(be); al.addWidget(bf); al.addWidget(bd)
            self.table.setCellWidget(r,7,acoes)
        self.table.resizeRowsToContents()

    def novo(self):
        d=ObraDialog(self.dao,self.user,parent=self)
        if d.exec()==QDialog.DialogCode.Accepted: self.refresh()

    def _editar(self,oid):
        try: obra=self.dao.get_obra(oid)
        except: return
        d=ObraDialog(self.dao,self.user,obra,parent=self)
        if d.exec()==QDialog.DialogCode.Accepted: self.refresh()

    def _eliminar(self,oid):
        r=QMessageBox.question(self,"Eliminar obra","Tem a certeza? Esta acção não pode ser desfeita.",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if r==QMessageBox.StandardButton.Yes:
            try: self.dao.execute("DELETE FROM obras WHERE id=%s",(oid,)); self.refresh()
            except Exception as e: QMessageBox.critical(self,"Erro",str(e))

    def _fases(self,oid):
        try: obra=self.dao.get_obra(oid)
        except: return
        d=FasesDialog(self.dao,self.user,obra,parent=self); d.exec()

    def _abrir_detalhe(self,idx):
        oid=self.table.item(idx.row(),0).data(Qt.ItemDataRole.UserRole)
        if oid: self._editar(oid)

class FasesDialog(QDialog):
    FASE_ICO={"corte":"✂️","furação":"🔩","montagem":"🔧","vidro":"🪟","acabamento":"🎨","instalacao":"🏗️","revisao":"🔍","entrega":"🚚"}
    FASE_ESTADOS=["pendente","em_curso","concluida","bloqueada"]
    FASE_COR={"pendente":("#e8edf2","#4a6080"),"em_curso":("#fff3cd","#b8700a"),"concluida":("#d4edda","#1e7e44"),"bloqueada":("#fde8e0","#c0392b")}
    def __init__(self,dao,user,obra,parent=None):
        super().__init__(parent); self.dao=dao; self.user=user; self.obra=obra
        self.setWindowTitle(f"Fases — {obra['numero']}"); self.setMinimumWidth(560); self.resize(580,500)
        lay=QVBoxLayout(self); lay.setContentsMargins(20,20,20,20); lay.setSpacing(12)
        tit=QLabel(f"🔨  {obra['descricao']}"); tit.setStyleSheet(f"font-size:14px;font-weight:700;color:{CORES['aco']};")
        lay.addWidget(tit)
        self.fases_lay=QVBoxLayout(); self.fases_lay.setSpacing(8)
        cw=QWidget(); cw.setLayout(self.fases_lay)
        sa=QScrollArea(); sa.setWidget(cw); sa.setWidgetResizable(True); sa.setFrameShape(QFrame.Shape.NoFrame)
        lay.addWidget(sa); self._load()

    def _load(self):
        while self.fases_lay.count():
            it=self.fases_lay.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        try: fases=self.dao.fases_obra(self.obra["id"])
        except: fases=[]
        for f in fases:
            card=QFrame(); card.setStyleSheet(f"background:{CORES['branco']};border:1px solid {CORES['alum_mid']};border-radius:10px;")
            cl=QHBoxLayout(card); cl.setContentsMargins(14,10,14,10)
            ico=self.FASE_ICO.get(f["fase"],"⚙️")
            il=QLabel(f"{ico}  {f['fase'].replace('_',' ').title()}"); il.setStyleSheet(f"font-size:13px;font-weight:600;color:{CORES['aco']};min-width:140px;")
            bg,fg=self.FASE_COR.get(f["estado"],("#e8edf2","#4a6080"))
            sl=QLabel(f["estado"].replace("_"," ").title())
            sl.setStyleSheet(f"background:{bg};color:{fg};border-radius:10px;padding:2px 9px;font-size:11px;font-weight:600;")
            op=QLabel(f["operador_nome"] or "—"); op.setStyleSheet(f"font-size:12px;color:{CORES['cinza']};min-width:100px;")
            cmb=QComboBox(); [cmb.addItem(e) for e in self.FASE_ESTADOS]
            cmb.setCurrentText(f["estado"]); cmb.setMaximumWidth(130)
            fid=f["id"]; cmb.currentTextChanged.connect(lambda st,fid=fid: self._update_fase(fid,st))
            cl.addWidget(il); cl.addWidget(sl); cl.addWidget(op); cl.addStretch(); cl.addWidget(cmb)
            self.fases_lay.addWidget(card)

    def _update_fase(self,fid,estado):
        try: self.dao.atualizar_fase(fid,estado,self.user.get("id")); self._load()
        except Exception as e: QMessageBox.critical(self,"Erro",str(e))
