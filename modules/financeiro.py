from PyQt6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QLineEdit,
    QTableWidget,QTableWidgetItem,QHeaderView,QDialog,QFormLayout,QComboBox,QDoubleSpinBox,
    QDateEdit,QTextEdit,QMessageBox,QFrame,QTabWidget)
from PyQt6.QtCore import Qt,QDate
CORES={"aco":"#1a2332","alum":"#e8edf2","alum_mid":"#c8d4de","branco":"#f8fafc","cinza":"#6b7c8e","laranja":"#d4560a","danger":"#c0392b","success":"#1e7e44","warning":"#b8700a"}
CATS_RECEITA=["Adiantamento","Pagamento final","Pagamento parcial","Serviço","Venda material","Outro"]
CATS_DESPESA=["Material","Mão de obra","Equipamento","Combustível","Fornecedor","Subcontratado","Impostos","Outro"]
METODOS=["Numerário","Transferência","Cheque","MB","MBWay","Outro"]

def _btn(t,o): b=QPushButton(t); b.setObjectName(o); b.setCursor(Qt.CursorShape.PointingHandCursor); return b

class FinanceiroDialog(QDialog):
    def __init__(self,dao,user,mov=None,obra_id=None,parent=None):
        super().__init__(parent); self.dao=dao; self.user=user; self.mov=mov
        self.setWindowTitle("Novo Movimento" if not mov else "Editar Movimento")
        self.setMinimumWidth(500); self.resize(520,520)
        from PyQt6.QtWidgets import QDialogButtonBox
        lay=QVBoxLayout(self); lay.setContentsMargins(20,20,20,20); lay.setSpacing(10)

        # Tipo
        tw=QWidget(); tl=QHBoxLayout(tw); tl.setContentsMargins(0,0,0,0); tl.setSpacing(12)
        self.cmb_tipo=QComboBox(); self.cmb_tipo.addItems(["receita","despesa"])
        self.cmb_tipo.currentTextChanged.connect(self._update_cats)
        tl.addWidget(QLabel("Tipo:")); tl.addWidget(self.cmb_tipo); tl.addStretch()
        lay.addWidget(tw)

        fl=QFormLayout(); fl.setSpacing(9)
        self.cmb_cat=QComboBox()
        self.inp_desc=QLineEdit(); self.inp_desc.setPlaceholderText("Descrição do movimento")
        self.spn_val=QDoubleSpinBox(); self.spn_val.setMaximum(9999999); self.spn_val.setSuffix(" €"); self.spn_val.setDecimals(2)
        self.dt_mov=QDateEdit(QDate.currentDate()); self.dt_mov.setCalendarPopup(True)
        self.cmb_metodo=QComboBox(); [self.cmb_metodo.addItem(m) for m in METODOS]
        self.inp_fatura=QLineEdit(); self.inp_fatura.setPlaceholderText("Nº fatura (opcional)")
        self.cmb_obra=QComboBox(); self.cmb_obra.addItem("— Sem obra —",None)
        self.inp_notas=QTextEdit(); self.inp_notas.setMaximumHeight(60)

        try:
            obras=self.dao.listar_obras()
            for o in obras:
                self.cmb_obra.addItem(f"{o['numero']} — {o.get('descricao','')[:40]}",o["id"])
        except: pass

        for lbl,w in [("Categoria",self.cmb_cat),("Descrição *",self.inp_desc),
                      ("Valor *",self.spn_val),("Data",self.dt_mov),
                      ("Método pagamento",self.cmb_metodo),("Nº Fatura/Recibo",self.inp_fatura),
                      ("Obra",self.cmb_obra),("Notas",self.inp_notas)]:
            fl.addRow(lbl,w)
        lay.addLayout(fl)

        bb=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._guardar); bb.rejected.connect(self.reject); lay.addWidget(bb)

        self._update_cats()
        if obra_id:
            for i in range(self.cmb_obra.count()):
                if self.cmb_obra.itemData(i)==obra_id:
                    self.cmb_obra.setCurrentIndex(i); break
        if mov: self._preencher()

    def _update_cats(self):
        cats = CATS_RECEITA if self.cmb_tipo.currentText()=="receita" else CATS_DESPESA
        atual = self.cmb_cat.currentText()
        self.cmb_cat.clear()
        [self.cmb_cat.addItem(c) for c in cats]
        if atual in cats: self.cmb_cat.setCurrentText(atual)

    def _preencher(self):
        m=self.mov
        self.cmb_tipo.setCurrentText(m.get("tipo","receita"))
        self.inp_desc.setText(m.get("descricao",""))
        self.spn_val.setValue(float(m.get("valor",0)))
        if m.get("data"):
            try: self.dt_mov.setDate(QDate.fromString(str(m["data"]),"yyyy-MM-dd"))
            except: pass
        self.cmb_cat.setCurrentText(m.get("categoria",""))
        self.cmb_metodo.setCurrentText(m.get("metodo_pag","Numerário") or "Numerário")
        self.inp_fatura.setText(m.get("documento","") or "")
        self.inp_notas.setPlainText(m.get("notas","") or "")
        if m.get("obra_id"):
            for i in range(self.cmb_obra.count()):
                if self.cmb_obra.itemData(i)==m["obra_id"]:
                    self.cmb_obra.setCurrentIndex(i); break

    def _guardar(self):
        if not self.inp_desc.text().strip() or self.spn_val.value()<=0:
            QMessageBox.warning(self,"Erro","Descrição e valor são obrigatórios."); return
        d={"tipo":self.cmb_tipo.currentText(),"descricao":self.inp_desc.text().strip(),
           "valor":self.spn_val.value(),"data":self.dt_mov.date().toString("yyyy-MM-dd"),
           "categoria":self.cmb_cat.currentText(),"metodo_pag":self.cmb_metodo.currentText(),
           "documento":self.inp_fatura.text(),"obra_id":self.cmb_obra.currentData(),
           "notas":self.inp_notas.toPlainText(),"pago":1}
        if self.mov: d["id"]=self.mov["id"]
        try: self.dao.salvar_financeiro(d); self.accept()
        except Exception as e: QMessageBox.critical(self,"Erro",str(e))


class ObraFinanceiroDialog(QDialog):
    """Mostra resumo financeiro de uma obra específica"""
    def __init__(self,dao,obra,parent=None):
        super().__init__(parent); self.dao=dao; self.obra=obra
        self.setWindowTitle(f"Financeiro — {obra['numero']}"); self.setMinimumSize(700,500)
        lay=QVBoxLayout(self); lay.setContentsMargins(16,16,16,16); lay.setSpacing(12)

        # Resumo da obra
        resumo=QFrame(); resumo.setStyleSheet(f"background:{CORES['aco']};border-radius:8px;")
        rl=QHBoxLayout(resumo); rl.setContentsMargins(16,12,16,12)
        orc=float(obra.get("valor_orcamento",0) or 0)
        fat=float(obra.get("valor_faturado",0) or 0)
        # calcular recebido da BD
        try:
            res=dao.fetchone("""SELECT
                SUM(CASE WHEN tipo='receita' THEN valor ELSE 0 END) AS recebido,
                SUM(CASE WHEN tipo='despesa' THEN valor ELSE 0 END) AS gasto
                FROM financeiro WHERE obra_id=%s""",(obra["id"],))
            recebido=float(res["recebido"] or 0)
            gasto=float(res["gasto"] or 0)
        except: recebido=0; gasto=0
        por_receber=orc-recebido

        def _stat(titulo,valor,cor):
            w=QWidget(); l=QVBoxLayout(w); l.setContentsMargins(0,0,0,0); l.setSpacing(2)
            lv=QLabel(f"{valor:.2f} €"); lv.setStyleSheet(f"font-size:20px;font-weight:800;color:{cor};")
            lt=QLabel(titulo); lt.setStyleSheet("font-size:11px;color:rgba(255,255,255,.6);")
            l.addWidget(lv); l.addWidget(lt); return w

        rl.addWidget(_stat("Orçamento",orc,"white"))
        rl.addWidget(_stat("Recebido",recebido,"#a8e6cf"))
        rl.addWidget(_stat("Por receber",por_receber,"#ffd3a5" if por_receber>0 else "#a8e6cf"))
        rl.addWidget(_stat("Gastos",gasto,"#ffaaa5"))
        rl.addWidget(_stat("Margem",recebido-gasto,"#a8e6cf" if recebido-gasto>=0 else "#ffaaa5"))
        lay.addWidget(resumo)

        # Botão registar recebimento
        bw=QWidget(); bl=QHBoxLayout(bw); bl.setContentsMargins(0,0,0,0)
        b_rec=QPushButton("💰  Registar Recebimento"); b_rec.setStyleSheet(f"background:{CORES['success']};color:white;border:none;border-radius:6px;padding:8px 16px;font-weight:600;")
        b_rec.clicked.connect(lambda: self._novo_movimento("receita"))
        b_des=QPushButton("💸  Registar Despesa"); b_des.setStyleSheet(f"background:{CORES['danger']};color:white;border:none;border-radius:6px;padding:8px 16px;font-weight:600;")
        b_des.clicked.connect(lambda: self._novo_movimento("despesa"))
        bl.addWidget(b_rec); bl.addWidget(b_des); bl.addStretch()
        lay.addWidget(bw)

        # Tabela movimentos
        self.table=QTableWidget(); self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Data","Tipo","Categoria","Descrição","Valor"])
        self.table.horizontalHeader().setSectionResizeMode(3,QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        lay.addWidget(self.table)
        self._load()

    def _load(self):
        try: movs=self.dao.listar_financeiro(obra_id=self.obra["id"])
        except: movs=[]
        self.table.setRowCount(len(movs))
        for r,m in enumerate(movs):
            vals=[str(m.get("data","—")),"",m.get("categoria","—"),m.get("descricao",""),f"{float(m.get('valor',0)):.2f} €"]
            for c,v in enumerate(vals):
                self.table.setItem(r,c,QTableWidgetItem(v))
            is_rec=m["tipo"]=="receita"
            bg,fg=("#d4edda","#1e7e44") if is_rec else ("#fde8e0","#c0392b")
            tl=QLabel("↑ Receita" if is_rec else "↓ Despesa"); tl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tl.setStyleSheet(f"background:{bg};color:{fg};border-radius:10px;padding:2px 8px;font-size:11px;font-weight:600;margin:4px;")
            self.table.setCellWidget(r,1,tl)
        self.table.resizeRowsToContents()

    def _novo_movimento(self,tipo):
        d=FinanceiroDialog(self.dao,None,obra_id=self.obra["id"],parent=self)
        d.cmb_tipo.setCurrentText(tipo)
        d._update_cats()
        if tipo=="receita":
            # Calcular valor em falta
            try:
                orc=float(self.obra.get("valor_orcamento",0) or 0)
                res=self.dao.fetchone(
                    "SELECT COALESCE(SUM(valor),0) AS rec FROM financeiro WHERE obra_id=%s AND tipo='receita'",
                    (self.obra["id"],))
                ja_recebido=float(res["rec"] or 0)
                por_receber=orc-ja_recebido
            except: por_receber=0; ja_recebido=0

            if por_receber>0 and ja_recebido>0:
                # Já houve adiantamento — sugere pagamento final
                d.cmb_cat.setCurrentText("Pagamento final")
                d.spn_val.setValue(por_receber)
                d.inp_desc.setText(f"Pagamento final obra {self.obra['numero']}")
            elif ja_recebido==0:
                d.cmb_cat.setCurrentText("Adiantamento")
                d.inp_desc.setText(f"Adiantamento obra {self.obra['numero']}")
            else:
                d.cmb_cat.setCurrentText("Pagamento parcial")

            # Quando categoria muda para "Pagamento final", preencher valor automaticamente
            def _on_cat_change(cat):
                if cat=="Pagamento final" and por_receber>0:
                    d.spn_val.setValue(por_receber)
                    d.inp_desc.setText(f"Pagamento final obra {self.obra['numero']}")
                elif cat=="Adiantamento":
                    d.inp_desc.setText(f"Adiantamento obra {self.obra['numero']}")
            d.cmb_cat.currentTextChanged.connect(_on_cat_change)

        if d.exec()==QDialog.DialogCode.Accepted:
            self._load(); self.__init__(self.dao,self.dao.get_obra(self.obra["id"]),self.parent())


class FinanceiroWidget(QWidget):
    def __init__(self,dao,user): super().__init__(); self.dao=dao; self.user=user; self._build()

    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(0,0,0,0)

        # Hero saldo
        self.hero=QFrame(); self.hero.setStyleSheet(f"background:{CORES['aco']};")
        hl=QHBoxLayout(self.hero); hl.setContentsMargins(22,16,22,16); hl.setSpacing(40)
        self.lbl_saldo=QLabel("0.00 €"); self.lbl_saldo.setStyleSheet("font-size:32px;font-weight:800;color:white;")
        self.lbl_rec=QLabel("Receitas: 0.00 €"); self.lbl_rec.setStyleSheet("font-size:12px;color:rgba(255,255,255,.7);")
        self.lbl_des=QLabel("Despesas: 0.00 €"); self.lbl_des.setStyleSheet("font-size:12px;color:rgba(255,255,255,.7);")
        iv=QVBoxLayout(); iv.setSpacing(2); iv.addWidget(self.lbl_rec); iv.addWidget(self.lbl_des)
        hl.addWidget(QLabel("💶  Saldo:")); hl.addWidget(self.lbl_saldo); hl.addLayout(iv); hl.addStretch()
        lay.addWidget(self.hero)

        # Tabs: Todos os movimentos | Por obra
        self.tabs=QTabWidget(); lay.addWidget(self.tabs)

        # Tab 1 — Todos
        t1=QWidget(); t1l=QVBoxLayout(t1); t1l.setContentsMargins(0,8,0,0)
        fb=QWidget(); fb.setStyleSheet(f"background:{CORES['branco']};border-bottom:1px solid {CORES['alum_mid']};")
        fl=QHBoxLayout(fb); fl.setContentsMargins(12,8,12,8); fl.setSpacing(10)
        self.inp_f=QLineEdit(); self.inp_f.setPlaceholderText("🔍  Pesquisar..."); self.inp_f.setMaximumWidth(220)
        self.inp_f.textChanged.connect(self.refresh)
        self.cmb_filtro=QComboBox()
        self.cmb_filtro.addItem("Todos",None); self.cmb_filtro.addItem("↑ Receitas","receita"); self.cmb_filtro.addItem("↓ Despesas","despesa")
        self.cmb_filtro.currentIndexChanged.connect(self.refresh)
        fl.addWidget(self.inp_f); fl.addWidget(self.cmb_filtro); fl.addStretch()
        t1l.addWidget(fb)
        self.table=QTableWidget(); self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Data","Tipo","Categoria","Descrição","Valor","Obra","Ações"])
        self.table.horizontalHeader().setSectionResizeMode(3,QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        t1l.addWidget(self.table)
        self.tabs.addTab(t1,"📋  Todos os Movimentos")

        # Tab 2 — Por obra
        t2=QWidget(); t2l=QVBoxLayout(t2); t2l.setContentsMargins(0,8,0,0)
        self.table_obras=QTableWidget(); self.table_obras.setColumnCount(6)
        self.table_obras.setHorizontalHeaderLabels(["Obra","Cliente","Orçamento","Recebido","Por receber","Ações"])
        self.table_obras.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
        self.table_obras.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_obras.verticalHeader().setVisible(False)
        t2l.addWidget(self.table_obras)
        self.tabs.addTab(t2,"🏗️  Por Obra")

        self.tabs.currentChanged.connect(self.refresh)

    def refresh(self):
        # Resumo geral
        try:
            res=self.dao.resumo_financeiro()
            saldo=res["saldo"]
            self.lbl_saldo.setText(f"{saldo:.2f} €")
            cor="#a8e6cf" if saldo>=0 else "#ffaaa5"
            self.lbl_saldo.setStyleSheet(f"font-size:32px;font-weight:800;color:{cor};")
            self.lbl_rec.setText(f"Receitas: {res['receitas']:.2f} €")
            self.lbl_des.setText(f"Despesas: {res['despesas']:.2f} €")
        except Exception as e: print("[FIN resumo]",e)

        if self.tabs.currentIndex()==0:
            self._refresh_lista()
        else:
            self._refresh_obras()

    def _refresh_lista(self):
        try: movs=self.dao.listar_financeiro(self.inp_f.text(),self.cmb_filtro.currentData())
        except Exception as e: print("[FIN lista]",e); movs=[]
        self.table.setRowCount(len(movs))
        for r,m in enumerate(movs):
            vals=[str(m.get("data","—")),"",m.get("categoria","—"),m.get("descricao",""),
                  f"{float(m.get('valor',0)):.2f} €",m.get("obra_numero") or "—"]
            for c,v in enumerate(vals):
                item=QTableWidgetItem(v); item.setData(Qt.ItemDataRole.UserRole,m["id"])
                self.table.setItem(r,c,item)
            is_rec=m["tipo"]=="receita"
            bg,fg=("#d4edda","#1e7e44") if is_rec else ("#fde8e0","#c0392b")
            tl=QLabel("↑ Receita" if is_rec else "↓ Despesa"); tl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tl.setStyleSheet(f"background:{bg};color:{fg};border-radius:10px;padding:2px 8px;font-size:11px;font-weight:600;margin:4px;")
            self.table.setCellWidget(r,1,tl)
            acoes=QWidget(); al=QHBoxLayout(acoes); al.setContentsMargins(4,2,4,2); al.setSpacing(4)
            be=_btn("✏️","btn_outline"); be.setFixedHeight(26); be.clicked.connect(lambda _,mid=m["id"]: self._editar(mid))
            bd=_btn("🗑️","btn_danger"); bd.setFixedHeight(26); bd.clicked.connect(lambda _,mid=m["id"]: self._eliminar(mid))
            al.addWidget(be); al.addWidget(bd); self.table.setCellWidget(r,6,acoes)
        self.table.resizeRowsToContents()

    def _refresh_obras(self):
        try: obras=self.dao.listar_obras()
        except: obras=[]
        # só obras com valor orçamento
        obras=[o for o in obras if float(o.get("valor_orcamento",0) or 0)>0]
        self.table_obras.setRowCount(len(obras))
        for r,o in enumerate(obras):
            orc=float(o.get("valor_orcamento",0) or 0)
            try:
                res=self.dao.fetchone("""SELECT SUM(CASE WHEN tipo='receita' THEN valor ELSE 0 END) AS rec
                    FROM financeiro WHERE obra_id=%s""",(o["id"],))
                recebido=float(res["rec"] or 0)
            except: recebido=0
            por_receber=orc-recebido
            vals=[f"{o['numero']} — {o.get('descricao','')[:30]}",o.get("cliente_nome","—"),
                  f"{orc:.2f} €",f"{recebido:.2f} €",f"{por_receber:.2f} €"]
            for c,v in enumerate(vals):
                item=QTableWidgetItem(v); item.setData(Qt.ItemDataRole.UserRole,o["id"])
                self.table_obras.setItem(r,c,item)
            # cor por receber
            cor="#fde8e0" if por_receber>0 else "#d4edda"
            self.table_obras.item(r,4).setBackground(__import__("PyQt6.QtGui",fromlist=["QColor"]).QColor(cor))
            # botão
            bw=QWidget(); bl=QHBoxLayout(bw); bl.setContentsMargins(4,2,4,2)
            b=_btn("💰 Recebimentos","btn_outline"); b.setFixedHeight(26)
            b.clicked.connect(lambda _,oid=o["id"]: self._ver_obra(oid))
            bl.addWidget(b); self.table_obras.setCellWidget(r,5,bw)
        self.table_obras.resizeRowsToContents()

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

    def _ver_obra(self,oid):
        try: obra=self.dao.get_obra(oid)
        except: return
        d=ObraFinanceiroDialog(self.dao,obra,parent=self)
        d.exec(); self.refresh()
