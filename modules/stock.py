from PyQt6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QLineEdit,
    QTableWidget,QTableWidgetItem,QHeaderView,QDialog,QFormLayout,QComboBox,QDoubleSpinBox,
    QTextEdit,QMessageBox,QCheckBox)
from PyQt6.QtCore import Qt
from datetime import date
from db.database import get_connection

CORES={"aco":"#1a2332","alum":"#e8edf2","alum_mid":"#c8d4de","branco":"#f8fafc","cinza":"#6b7c8e","laranja":"#d4560a","danger":"#c0392b","warning":"#b8700a","success":"#1e7e44"}

def _fazer_movimento_financeiro(referencia, nome, unidade, qtd, preco_custo):
    from datetime import date
    conn = get_connection()
    cur = conn.cursor()
    try:
        valor = qtd * preco_custo
        desc = f"Compra stock: {nome} ({qtd} {unidade})"
        cur.execute(
            "INSERT INTO financeiro (tipo,categoria,descricao,valor,data,pago) VALUES(%s,%s,%s,%s,%s,%s)",
            ("despesa","Material",desc,valor,str(date.today()),1))
        conn.commit()
        print(f"[FINANCEIRO] Despesa criada: {desc} — {valor}€")
    finally:
        cur.close(); conn.close()

def _btn(t,o): b=QPushButton(t); b.setObjectName(o); b.setCursor(Qt.CursorShape.PointingHandCursor); return b

def _fazer_movimento(stock_id, tipo, qtd, motivo="", obra_id=None, user_id=None):
    """Faz movimento de stock e regista automaticamente no financeiro."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        # Buscar material
        cur.execute("SELECT * FROM stock WHERE id=%s", (stock_id,))
        item = cur.fetchone()
        if not item:
            raise Exception("Material não encontrado.")

        # Actualizar quantidade
        delta = qtd if tipo == "entrada" else -qtd
        cur.execute("UPDATE stock SET quantidade=quantidade+%s WHERE id=%s", (delta, stock_id))

        # Registar movimento
        cur.execute(
            "INSERT INTO stock_movimentos (stock_id,tipo,quantidade,motivo,obra_id,utilizador_id) VALUES(%s,%s,%s,%s,%s,%s)",
            (stock_id, tipo, qtd, motivo, obra_id, user_id))

        # Registo financeiro automático
        if tipo == "entrada":
            valor = float(item.get("preco_custo") or 0) * float(qtd)
            if valor > 0:
                desc = f"Compra stock: {item['nome']} ({qtd} {item['unidade']})"
                if motivo: desc += f" — {motivo}"
                cur.execute(
                    "INSERT INTO financeiro (tipo,categoria,descricao,valor,data,obra_id,pago) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                    ("despesa", "Material", desc, valor, str(date.today()), obra_id, 1))
                print(f"[FINANCEIRO] Despesa criada: {desc} — {valor}€")

        elif tipo == "saida":
            valor = float(item.get("preco_venda") or 0) * float(qtd)
            if valor > 0:
                desc = f"Saída stock: {item['nome']} ({qtd} {item['unidade']})"
                if motivo: desc += f" — {motivo}"
                cur.execute(
                    "INSERT INTO financeiro (tipo,categoria,descricao,valor,data,obra_id,pago) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                    ("receita", "Material", desc, valor, str(date.today()), obra_id, 1))
                print(f"[FINANCEIRO] Receita criada: {desc} — {valor}€")

        conn.commit()
        print(f"[STOCK] Movimento '{tipo}' de {qtd} unidades concluído.")
    finally:
        cur.close()
        conn.close()

class StockDialog(QDialog):
    def __init__(self,dao,item=None,parent=None):
        super().__init__(parent); self.dao=dao; self.item=item
        self.setWindowTitle("Novo Material" if not item else "Editar Material")
        self.setMinimumWidth(500); self.resize(520,500)
        from PyQt6.QtWidgets import QDialogButtonBox
        lay=QVBoxLayout(self); lay.setContentsMargins(20,20,20,20); lay.setSpacing(10)
        fl=QFormLayout(); fl.setSpacing(9)
        self.inp_ref=QLineEdit(); self.inp_ref.setPlaceholderText("ex: PERF-6060-60X40")
        self.inp_nome=QLineEdit(); self.inp_nome.setPlaceholderText("Descrição do material")
        self.cmb_cat=QComboBox(); self._load_cats()
        self.cmb_un=QComboBox(); self.cmb_un.addItems(["un","m","m2","kg","lt","barra","rolo","caixa"])
        self.spn_qtd=QDoubleSpinBox(); self.spn_qtd.setMaximum(999999); self.spn_qtd.setDecimals(3)
        self.spn_min=QDoubleSpinBox(); self.spn_min.setMaximum(999999); self.spn_min.setDecimals(3)
        self.spn_custo=QDoubleSpinBox(); self.spn_custo.setMaximum(99999); self.spn_custo.setSuffix(" €"); self.spn_custo.setDecimals(2)
        self.spn_venda=QDoubleSpinBox(); self.spn_venda.setMaximum(99999); self.spn_venda.setSuffix(" €"); self.spn_venda.setDecimals(2)
        self.inp_forn=QLineEdit(); self.inp_local=QLineEdit()
        self.inp_notas=QTextEdit(); self.inp_notas.setMaximumHeight(60)
        for lbl,w in [("Referência *",self.inp_ref),("Descrição *",self.inp_nome),("Categoria",self.cmb_cat),
                      ("Unidade",self.cmb_un),("Quantidade",self.spn_qtd),("Qtd. mínima",self.spn_min),
                      ("Preço custo",self.spn_custo),("Preço venda",self.spn_venda),
                      ("Fornecedor",self.inp_forn),("Localização",self.inp_local),("Notas",self.inp_notas)]:
            fl.addRow(lbl,w)
        lay.addLayout(fl)
        bb=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._guardar); bb.rejected.connect(self.reject); lay.addWidget(bb)
        if item: self._preencher()

    def _load_cats(self):
        self.cmb_cat.addItem("— Seleccionar —",None)
        try:
            for c in self.dao.listar_categorias_stock():
                self.cmb_cat.addItem(c["nome"],c["id"])
        except: pass

    def _preencher(self):
        s=self.item
        self.inp_ref.setText(s.get("referencia",""))
        self.inp_nome.setText(s.get("nome",""))
        self.cmb_un.setCurrentText(s.get("unidade","un"))
        self.spn_qtd.setValue(float(s.get("quantidade",0)))
        self.spn_min.setValue(float(s.get("stock_minimo",0)))
        self.spn_custo.setValue(float(s.get("preco_custo",0)))
        self.spn_venda.setValue(float(s.get("preco_venda",0)))
        self.inp_forn.setText(s.get("fornecedor",""))
        self.inp_local.setText(s.get("localizacao",""))
        self.inp_notas.setPlainText(s.get("notas",""))
        for i in range(self.cmb_cat.count()):
            if self.cmb_cat.itemData(i)==s.get("categoria_id"):
                self.cmb_cat.setCurrentIndex(i); break

    def _guardar(self):
        if not self.inp_ref.text().strip() or not self.inp_nome.text().strip():
            QMessageBox.warning(self,"Erro","Referência e descrição são obrigatórias."); return
        d={"referencia":self.inp_ref.text().strip(),"nome":self.inp_nome.text().strip(),
           "categoria_id":self.cmb_cat.currentData(),"unidade":self.cmb_un.currentText(),
           "quantidade":self.spn_qtd.value(),"stock_minimo":self.spn_min.value(),
           "preco_custo":self.spn_custo.value(),"preco_venda":self.spn_venda.value(),
           "fornecedor":self.inp_forn.text(),"localizacao":self.inp_local.text(),
           "notas":self.inp_notas.toPlainText()}
        if self.item: d["id"]=self.item["id"]
        try:
            qtd_anterior = float(self.item.get("quantidade",0)) if self.item else 0
            self.dao.salvar_stock(d)
            # Se é novo produto com quantidade, ou edição que aumentou quantidade -> registo financeiro
            qtd_nova = float(d["quantidade"])
            delta = qtd_nova - qtd_anterior
            if delta > 0 and float(d.get("preco_custo",0)) > 0:
                _fazer_movimento_financeiro(
                    d["referencia"], d["nome"], d.get("unidade","un"),
                    delta, float(d["preco_custo"]))
            self.accept()
        except Exception as e: QMessageBox.critical(self,"Erro",str(e))

class MovimentoDialog(QDialog):
    def __init__(self,stock_item,user,parent=None):
        super().__init__(parent); self.stock_item=stock_item; self.user=user
        self.setWindowTitle(f"Movimento — {stock_item['nome']}"); self.setFixedSize(400,260)
        from PyQt6.QtWidgets import QDialogButtonBox
        lay=QVBoxLayout(self); lay.setContentsMargins(20,20,20,20); lay.setSpacing(10)
        fl=QFormLayout(); fl.setSpacing(8)
        self.cmb_tipo=QComboBox(); self.cmb_tipo.addItems(["entrada","saida","ajuste","sobra"])
        self.spn_qtd=QDoubleSpinBox(); self.spn_qtd.setMaximum(99999); self.spn_qtd.setDecimals(3); self.spn_qtd.setMinimum(0.001)
        self.inp_motivo=QLineEdit(); self.inp_motivo.setPlaceholderText("Motivo / referência obra")
        fl.addRow("Tipo",self.cmb_tipo); fl.addRow("Quantidade",self.spn_qtd); fl.addRow("Motivo",self.inp_motivo)
        lay.addLayout(fl)
        info=QLabel(f"Stock actual: {stock_item['quantidade']} {stock_item['unidade']}")
        info.setStyleSheet(f"color:{CORES['cinza']};font-size:12px;"); lay.addWidget(info)
        bb=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._guardar); bb.rejected.connect(self.reject); lay.addWidget(bb)

    def _guardar(self):
        try:
            _fazer_movimento(
                self.stock_item["id"],
                self.cmb_tipo.currentText(),
                self.spn_qtd.value(),
                self.inp_motivo.text(),
                None,
                self.user.get("id")
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self,"Erro",str(e))

class StockWidget(QWidget):
    def __init__(self,dao,user): super().__init__(); self.dao=dao; self.user=user; self._build()

    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(0,0,0,0)
        fb=QWidget(); fb.setStyleSheet(f"background:{CORES['branco']};border-bottom:1px solid {CORES['alum_mid']};")
        fl=QHBoxLayout(fb); fl.setContentsMargins(16,10,16,10); fl.setSpacing(10)
        self.inp_f=QLineEdit(); self.inp_f.setPlaceholderText("🔍  Pesquisar referência ou descrição...")
        self.inp_f.setMaximumWidth(300); self.inp_f.textChanged.connect(self.refresh)
        self.chk_baixo=QCheckBox("Só stock baixo"); self.chk_baixo.toggled.connect(self.refresh)
        fl.addWidget(self.inp_f); fl.addWidget(self.chk_baixo); fl.addStretch(); lay.addWidget(fb)
        self.table=QTableWidget(); self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["Ref.","Descrição","Categoria","Unidade","Quantidade","Qtd. Mín.","Custo","Ações"])
        self.table.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False); lay.addWidget(self.table)

    def refresh(self):
        try: items=self.dao.listar_stock(self.inp_f.text(),self.chk_baixo.isChecked())
        except: items=[]
        self.table.setRowCount(len(items))
        for r,s in enumerate(items):
            baixo=float(s.get("quantidade",0))<=float(s.get("stock_minimo",0))
            vals=[s["referencia"],s.get("nome","—"),s.get("categoria_nome","—"),
                  s.get("unidade",""),str(s.get("quantidade",0)),str(s.get("stock_minimo",0)),
                  f"{float(s.get('preco_custo',0)):.2f} €"]
            for c,v in enumerate(vals):
                item=QTableWidgetItem(v); item.setData(Qt.ItemDataRole.UserRole,s["id"])
                self.table.setItem(r,c,item)
            acoes=QWidget(); al=QHBoxLayout(acoes); al.setContentsMargins(4,2,4,2); al.setSpacing(4)
            bm=_btn("📥","btn_outline"); bm.setFixedHeight(26); bm.setToolTip("Movimento")
            bm.clicked.connect(lambda _,sid=s["id"]: self._movimento(sid))
            be=_btn("✏️","btn_outline"); be.setFixedHeight(26)
            be.clicked.connect(lambda _,sid=s["id"]: self._editar(sid))
            bd=_btn("🗑️","btn_danger"); bd.setFixedHeight(26)
            bd.clicked.connect(lambda _,sid=s["id"]: self._eliminar(sid))
            al.addWidget(bm); al.addWidget(be); al.addWidget(bd)
            self.table.setCellWidget(r,7,acoes)
        self.table.resizeRowsToContents()

    def novo(self):
        d=StockDialog(self.dao,parent=self)
        if d.exec()==QDialog.DialogCode.Accepted: self.refresh()

    def _editar(self,sid):
        try: s=self.dao.get_stock(sid)
        except: return
        d=StockDialog(self.dao,s,parent=self)
        if d.exec()==QDialog.DialogCode.Accepted: self.refresh()

    def _movimento(self,sid):
        try: s=self.dao.get_stock(sid)
        except: return
        d=MovimentoDialog(s,self.user,parent=self)
        if d.exec()==QDialog.DialogCode.Accepted: self.refresh()

    def _eliminar(self,sid):
        r=QMessageBox.question(self,"Eliminar","Tem a certeza?",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if r==QMessageBox.StandardButton.Yes:
            try:
                conn=get_connection(); cur=conn.cursor()
                cur.execute("DELETE FROM stock WHERE id=%s",(sid,))
                conn.commit(); cur.close(); conn.close(); self.refresh()
            except Exception as e: QMessageBox.critical(self,"Erro",str(e))
