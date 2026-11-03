from modules.temas import cor_texto
from PyQt6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QLineEdit,
    QTableWidget,QTableWidgetItem,QHeaderView,QDialog,QFormLayout,QComboBox,QDoubleSpinBox,
    QTextEdit,QMessageBox,QCheckBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
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
        self.spn_qtd=QDoubleSpinBox(); self.spn_qtd.setMaximum(999999); self.spn_qtd.setDecimals(0)
        self.spn_min=QDoubleSpinBox(); self.spn_min.setMaximum(999999); self.spn_min.setDecimals(0)
        self.spn_custo=QDoubleSpinBox(); self.spn_custo.setMaximum(99999); self.spn_custo.setSuffix(" €"); self.spn_custo.setDecimals(2)
        self.spn_venda=QDoubleSpinBox(); self.spn_venda.setMaximum(99999); self.spn_venda.setSuffix(" €"); self.spn_venda.setDecimals(2)
        # Fornecedor com autocomplete
        self.inp_forn=QLineEdit(); self.inp_forn.setPlaceholderText("Escreva o nome do fornecedor...")
        self._forns = []
        self._forn_id = None
        try:
            from PyQt6.QtWidgets import QCompleter
            self._forns = dao.listar_fornecedores()
            nomes = [f["nome"] for f in self._forns]
            completer = QCompleter(nomes, self)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.activated.connect(self._forn_selecionado)
            self.inp_forn.setCompleter(completer)
        except Exception as e:
            print(f"Erro fornecedores: {e}")
        self.inp_local=QLineEdit()
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

    def _forn_selecionado(self, nome):

        for f in self._forns:
            if f["nome"] == nome:
                self._forn_id = f["id"]

                if hasattr(self, 'inp_local_forn'):
                    self.inp_local_forn.setText(f.get("localidade","") or "")
                break

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
            # Validar e registar fornecedor se necessário
            nome_forn = self.inp_forn.text().strip()
            self._forn_id = None
            if nome_forn:
                for f in self._forns:
                    if f["nome"].lower() == nome_forn.lower():
                        self._forn_id = f["id"]
                        break
                if not self._forn_id:
                    from modules.fornecedores import FornecedorDialog
                    QMessageBox.information(self, "Fornecedor não registado",
                        f"O fornecedor '{nome_forn}' não está registado.\nPor favor registe-o para continuar.")
                    dlg = FornecedorDialog(self.dao, self)
                    dlg.inp_nome.setText(nome_forn)
                    if dlg.exec() != QDialog.DialogCode.Accepted:
                        return
                    self._forns = self.dao.listar_fornecedores()
                    for f in self._forns:
                        if f["nome"].lower() == nome_forn.lower():
                            self._forn_id = f["id"]
                            # Preencher localidade com os dados do novo fornecedor
                            if hasattr(self, 'inp_local_forn'):
                                self.inp_local_forn.setText(f.get("localidade","") or "")
                            break
                    if not self._forn_id and self._forns:
                        self._forn_id = self._forns[-1]["id"]
                        if hasattr(self, 'inp_local_forn'):
                            self.inp_local_forn.setText(self._forns[-1].get("localidade","") or "")
            qtd_anterior = float(self.item.get("quantidade",0)) if self.item else 0
            sid = self.dao.salvar_stock(d)
            if not sid and self.item: sid = self.item["id"]
            qtd_nova = float(d["quantidade"])
            delta = qtd_nova - qtd_anterior
            if delta > 0:
                # Registar movimento em stock_movimentos
                stock_id = sid or self.dao.get_stock_by_ref(d["referencia"])
                if stock_id:
                    motivo = "Stock inicial" if not self.item else "Ajuste de edição"
                    _fazer_movimento(stock_id, "entrada" if not self.item else "ajuste",
                        delta, motivo, None, None)
                if float(d.get("preco_custo",0)) > 0:
                    _fazer_movimento_financeiro(
                        d["referencia"], d["nome"], d.get("unidade","un"),
                        delta, float(d["preco_custo"]))
            # Associar fornecedor ao artigo
            if self._forn_id and sid:
                self.dao.associar_fornecedor_stock(sid, self._forn_id)
            self.accept()
        except Exception as e: QMessageBox.critical(self,"Erro",str(e))

class MovimentoDialog(QDialog):
    def __init__(self, stock_item, user, dao=None, parent=None):
        super().__init__(parent)
        self.stock_item = stock_item
        self.user = user
        self.dao = dao
        self.setWindowTitle(f"Movimento — {stock_item['nome']}")
        self.setMinimumWidth(440)
        from PyQt6.QtWidgets import QDialogButtonBox, QCompleter
        from PyQt6.QtCore import QStringListModel
        lay = QVBoxLayout(self); lay.setContentsMargins(20,20,20,20); lay.setSpacing(10)
        fl = QFormLayout(); fl.setSpacing(10)

        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems(["entrada","saida","ajuste","sobra"])
        self.cmb_tipo.currentTextChanged.connect(self._tipo_changed)

        self.spn_qtd = QDoubleSpinBox()
        self.spn_qtd.setMaximum(99999); self.spn_qtd.setDecimals(0); self.spn_qtd.setMinimum(0)

        self.inp_motivo = QLineEdit()
        self.inp_motivo.setPlaceholderText("Motivo / referência obra")

        # Fornecedor com autocomplete
        self.inp_forn = QLineEdit()
        self.inp_forn.setPlaceholderText("Escreva o nome do fornecedor...")
        self._forns = []
        self._forn_id = None
        if dao:
            try:
                self._forns = dao.listar_fornecedores()
                nomes = [f["nome"] for f in self._forns]
                completer = QCompleter(nomes, self)
                completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
                completer.setFilterMode(Qt.MatchFlag.MatchContains)
                completer.activated.connect(self._forn_selecionado)
                self.inp_forn.setCompleter(completer)
                self.inp_forn.textChanged.connect(self._forn_texto_changed)
                # Pre-selecionar fornecedor principal se existir
                forn_stock = dao.listar_fornecedores_stock(stock_item["id"])
                for fs in forn_stock:
                    if fs.get("fornecedor_principal"):
                        for f in self._forns:
                            if f["id"] == fs["fornecedor_id"]:
                                self.inp_forn.setText(f["nome"])
                                self._forn_id = f["id"]
                                self.inp_local_forn.setText(f.get("localidade","") or "")
                                break
            except Exception as e:
                print(f"Erro ao carregar fornecedores: {e}")

        # Campo localidade (preenchido automaticamente)
        self.inp_local_forn = QLineEdit()
        self.inp_local_forn.setPlaceholderText("Preenchido automaticamente")
        self.inp_local_forn.setReadOnly(True)
        self.inp_local_forn.setStyleSheet("background:#f0f4f8;color:#6b7c8e;")
        self.lbl_forn = QLabel("Fornecedor *")
        self.lbl_local_forn = QLabel("Localidade")
        fl.addRow("Tipo", self.cmb_tipo)
        fl.addRow("Quantidade", self.spn_qtd)
        fl.addRow("Motivo", self.inp_motivo)
        fl.addRow(self.lbl_forn, self.inp_forn)
        fl.addRow(self.lbl_local_forn, self.inp_local_forn)
        lay.addLayout(fl)

        info = QLabel(f"Stock actual: {int(float(stock_item.get('quantidade',0)))} {stock_item.get('unidade','')}")
        info.setStyleSheet(f"color:{CORES['cinza']};font-size:12px;")
        lay.addWidget(info)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._guardar); bb.rejected.connect(self.reject)
        lay.addWidget(bb)
        self._tipo_changed("entrada")

    def _forn_selecionado(self, nome):

        for f in self._forns:
            if f["nome"] == nome:
                self._forn_id = f["id"]

                if hasattr(self, 'inp_local_forn'):
                    self.inp_local_forn.setText(f.get("localidade","") or "")
                break

    def _tipo_changed(self, tipo):
        visivel = tipo == "entrada"
        self.lbl_forn.setVisible(visivel)
        self.inp_forn.setVisible(visivel)
        self.lbl_local_forn.setVisible(visivel)
        self.inp_local_forn.setVisible(visivel)

    def _guardar(self):
        tipo = self.cmb_tipo.currentText()
        # Validar fornecedor obrigatório para entradas
        if tipo == "entrada":
            nome_forn = self.inp_forn.text().strip()
            if not nome_forn:
                QMessageBox.warning(self, "Atenção", "O fornecedor é obrigatório para entradas de stock.")
                return
            # Verificar se o fornecedor existe
            self._forn_id = None
            for f in self._forns:
                if f["nome"].lower() == nome_forn.lower():
                    self._forn_id = f["id"]
                    break
            # Se não existe abre o formulário de registo
            if not self._forn_id:
                from modules.fornecedores import FornecedorDialog
                QMessageBox.information(self, "Fornecedor não registado",
                    f"O fornecedor '{nome_forn}' não está registado.\nPor favor registe-o para continuar.")
                dlg = FornecedorDialog(self.dao, self)
                dlg.inp_nome.setText(nome_forn)
                if dlg.exec() != QDialog.DialogCode.Accepted:
                    return
                # Recarregar lista e selecionar novo fornecedor
                self._forns = self.dao.listar_fornecedores()
                for f in self._forns:
                    if f["nome"].lower() == nome_forn.lower():
                        self._forn_id = f["id"]
                        break
                if not self._forn_id and self._forns:
                    self._forn_id = self._forns[-1]["id"]
        try:
            _fazer_movimento(
                self.stock_item["id"], tipo,
                self.spn_qtd.value(),
                self.inp_motivo.text(),
                None, self.user.get("id")
            )
            if tipo == "entrada" and self.dao and self._forn_id:
                self.dao.associar_fornecedor_stock(self.stock_item["id"], self._forn_id)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

class HistoricoStockDialog(QDialog):
    def __init__(self, parent, dao, stock_item):
        super().__init__(parent)
        self.setWindowTitle(f"📋 Histórico — {stock_item.get('nome','')}")
        self.resize(750, 450)
        lay = QVBoxLayout(self)

        # Cabeçalho
        info = QLabel(f"<b>{stock_item.get('referencia','')} — {stock_item.get('nome','')}</b> &nbsp;|&nbsp; Stock actual: <b>{int(float(stock_item.get('quantidade',0)))}</b> {stock_item.get('unidade','')}")
        info.setStyleSheet("padding:8px; background:#1a2332; color:white; border-radius:4px;")
        lay.addWidget(info)

        # Tabela
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Data","Tipo","Quantidade","Qtd. Anterior","Motivo","Obra","Utilizador"])
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 130)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 110)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        lay.addWidget(self.table)

        # Fechar
        btn_fechar = QPushButton("Fechar")
        btn_fechar.clicked.connect(self.accept)
        btn_fechar.setObjectName("btn_secondary")
        lay.addWidget(btn_fechar, alignment=Qt.AlignmentFlag.AlignRight)

        self._carregar(dao, stock_item["id"])

    def _carregar(self, dao, stock_id):
        TIPO_COR = {
                "entrada":  ("#e6f4ea", "#1a7a3a"),
                "saida":    ("#fdecea", "#c0392b"),
                "ajuste":   ("#fff8e1", "#e67e00"),
                "sobra":    ("#e8f0fe", "#1a56db"),
            }
        TIPO_LABEL = {"entrada":"▲ Entrada","saida":"▼ Saída","ajuste":"⚙ Ajuste","sobra":"♻ Sobra"}
        movs = dao.listar_movimentos_stock(stock_id)
        self.table.setRowCount(len(movs))
        for r, m in enumerate(movs):
            tipo = m.get("tipo","")
            bg, fg = TIPO_COR.get(tipo, ("#f8fafc","#333"))
            vals = [
                str(m.get("criado_em",""))[:16],
                TIPO_LABEL.get(tipo, tipo),
                str(int(float(m.get("quantidade",0)))),
                str(int(float(m.get("quantidade_anterior",0)))) if m.get("quantidade_anterior") is not None else "—",
                m.get("motivo","") or "—",
                m.get("obra_numero","") or "—",
                m.get("utilizador_nome","") or "—",
            ]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setBackground(QColor(bg))
                item.setForeground(QColor(fg if c == 1 else cor_texto()))
                if c in (2,3): item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(r, c, item)

class StockWidget(QWidget):
    def __init__(self,dao,user): super().__init__(); self.dao=dao; self.user=user; self._build()

    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(0,0,0,0)
        fb=QWidget(); fb.setStyleSheet(f"background:{CORES['branco']};border-bottom:1px solid {CORES['alum_mid']};")
        fl=QHBoxLayout(fb); fl.setContentsMargins(16,10,16,10); fl.setSpacing(10)
        self.inp_f=QLineEdit(); self.inp_f.setPlaceholderText("🔍  Pesquisar referência ou descrição...")
        self.inp_f.setMaximumWidth(300); self.inp_f.textChanged.connect(self.refresh)
        self.chk_baixo=QCheckBox("Só stock baixo"); self.chk_baixo.toggled.connect(self.refresh)
        btn_exp = _btn("📤 Exportar","btn_outline")
        btn_exp.clicked.connect(self._exportar)
        fl.addWidget(self.inp_f); fl.addWidget(self.chk_baixo); fl.addStretch()
        fl.addWidget(btn_exp); lay.addWidget(fb)
        self.table=QTableWidget(); self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["Ref.","Descrição","Categoria","Unidade","Quantidade","Qtd. Mín.","Custo","Ações"])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 130)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 70)
        self.table.setColumnWidth(4, 90)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 90)
        self.table.setColumnWidth(7, 100)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False); lay.addWidget(self.table)

    def _ver_historico(self, stock_item):
        dlg = HistoricoStockDialog(self, self.dao, stock_item)
        dlg.exec()

    def _exportar(self):
        try:
            items = self.dao.listar_stock(self.inp_f.text(), self.chk_baixo.isChecked())
            colunas = ["Referência","Descrição","Categoria","Unidade","Quantidade","Qtd. Mín.","Custo (€)"]
            linhas = [[
                s["referencia"], s.get("nome",""),s.get("categoria_nome",""),
                s.get("unidade",""), int(float(s.get("quantidade",0))),
                int(float(s.get("stock_minimo",0))),
                float(s.get("preco_custo",0))
            ] for s in items]
            from modules.exportar import dialogo_exportar
            dialogo_exportar(self, "Stock", colunas, linhas)
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Erro", str(e))

    def refresh(self):
        try: items=self.dao.listar_stock(self.inp_f.text(),self.chk_baixo.isChecked())
        except: items=[]
        self.table.setRowCount(len(items))
        for r,s in enumerate(items):
            baixo=float(s.get("quantidade",0))<=float(s.get("stock_minimo",0))
            vals=[s["referencia"],s.get("nome","—"),s.get("categoria_nome","—"),
                  s.get("unidade",""),str(int(float(s.get("quantidade",0)))),str(int(float(s.get("stock_minimo",0)))),
                  f"{float(s.get('preco_custo',0)):.2f} €"]
            for c,v in enumerate(vals):
                item=QTableWidgetItem(v); item.setData(Qt.ItemDataRole.UserRole,s["id"])
                if baixo:
                    item.setBackground(QColor("#fdecea"))
                    item.setForeground(QColor("#c0392b"))
                self.table.setItem(r,c,item)
            acoes=QWidget(); al=QHBoxLayout(acoes); al.setContentsMargins(4,2,4,2); al.setSpacing(4)
            bm=_btn("📥","btn_outline"); bm.setFixedHeight(26); bm.setToolTip("Movimento")
            bm.clicked.connect(lambda _,sid=s["id"]: self._movimento(sid))
            bh=_btn("📋","btn_outline"); bh.setFixedHeight(26); bh.setToolTip("Histórico")
            bh.clicked.connect(lambda _, s=s: self._ver_historico(s))
            be=_btn("✏️","btn_outline"); be.setFixedHeight(26); be.setToolTip("Editar artigo")
            be.clicked.connect(lambda _,sid=s["id"]: self._editar(sid))
            bd=_btn("🗑️","btn_danger"); bd.setFixedHeight(26); bd.setToolTip("Eliminar artigo")
            bd.clicked.connect(lambda _,sid=s["id"]: self._eliminar(sid))
            al.addWidget(bm); al.addWidget(bh); al.addWidget(be); al.addWidget(bd)
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
        d=MovimentoDialog(s,self.user,dao=self.dao,parent=self)
        if d.exec()==QDialog.DialogCode.Accepted: self.refresh()

    def _eliminar(self,sid):
        r=QMessageBox.question(self,"Eliminar","Tem a certeza?",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if r==QMessageBox.StandardButton.Yes:
            try:
                conn=get_connection(); cur=conn.cursor()
                cur.execute("DELETE FROM stock WHERE id=%s",(sid,))
                conn.commit(); cur.close(); conn.close(); self.refresh()
            except Exception as e: QMessageBox.critical(self,"Erro",str(e))
