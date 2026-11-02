from PyQt6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,
    QLineEdit,QTableWidget,QTableWidgetItem,QHeaderView,QDialog,QFormLayout,
    QComboBox,QDateEdit,QTextEdit,QFrame,QScrollArea,QTabWidget,QDoubleSpinBox,QCheckBox,
    QGroupBox,QMessageBox,QSplitter)
from PyQt6.QtCore import Qt,QDate
from PyQt6.QtGui import QColor

CORES = {
    "aco": "#1a2332",
    "aco_mid": "#2c3e55",
    "laranja": "#d4560a",
    "alum": "#e8edf2",
    "alum_mid": "#c8d4de",
    "branco": "#f8fafc",
    "cinza": "#6b7c8e",
    "success": "#1e7e44",
    "danger": "#c0392b",
    "warning": "#b8700a",
    "info": "#1a6fa8"
}

ESTADOS = ["orcamento", "confirmada", "em_producao", "em_montagem", "concluida", "cancelada", "em_espera"]
ESTADOS_TEXTO = {
    "orcamento": "Orçamento",
    "confirmada": "Confirmada",
    "em_producao": "Em Produção",
    "em_montagem": "Em Montagem",
    "concluida": "Concluída",
    "cancelada": "Cancelada",
    "em_espera": "Em Espera"
}

ESTADOS_ATIVOS = ["orcamento", "confirmada", "em_producao", "em_montagem"]

# Transições permitidas. "concluida" e "cancelada" são estados finais.
TRANSICOES = {
    "orcamento":   ["confirmada", "em_espera", "cancelada"],
    "confirmada":  ["em_producao", "em_espera", "cancelada"],
    "em_producao": ["em_montagem", "em_espera", "cancelada"],
    "em_montagem": ["concluida", "em_espera", "cancelada"],
    "em_espera":   [],
    "concluida":   [],
    "cancelada":   [],
}


def transicoes_permitidas(estado_atual, estado_anterior=None):
    """Estados para onde a obra pode passar, a partir do estado actual."""
    if estado_atual == "em_espera":
        opcoes = [estado_anterior] if estado_anterior in ESTADOS_ATIVOS else list(ESTADOS_ATIVOS)
        return opcoes + ["cancelada"]
    return list(TRANSICOES.get(estado_atual, []))


def validar_transicao(estado_atual, novo_estado, estado_anterior=None):
    """Devolve None se a transição é válida, ou a mensagem de erro."""
    if novo_estado == estado_atual:
        return None
    if novo_estado in transicoes_permitidas(estado_atual, estado_anterior):
        return None
    if estado_atual in ("concluida", "cancelada"):
        return (f"A obra está «{ESTADOS_TEXTO.get(estado_atual, estado_atual)}» e já não pode "
                "mudar de estado.\n\nEstados finais não podem ser alterados.")
    return (f"Não é possível passar de «{ESTADOS_TEXTO.get(estado_atual, estado_atual)}» "
            f"para «{ESTADOS_TEXTO.get(novo_estado, novo_estado)}».")


TIPOS = ["porta", "janela", "marquise", "porta_de_correr", "gradeamento", "portao", "cobertura", "outro"]
TIPOS_TEXTO = {
    "porta": "Porta",
    "janela": "Janela",
    "marquise": "Marquise",
    "porta_de_correr": "Porta de Correr",
    "gradeamento": "Gradeamento",
    "portao": "Portão",
    "cobertura": "Cobertura",
    "outro": "Outro",
}
PRIORIDADES = ["normal", "urgente", "critica"]

ESTADO_COR = {
    "orcamento":    ("#e8edf2", "#4a6080"),
    "confirmada":   ("#fff3cd", "#b8700a"),
    "em_producao":  ("#d4edda", "#1e7e44"),
    "em_montagem":  ("#e8f0fa", "#1a6fa8"),
    "concluida":    ("#d4edda", "#1e7e44"),
    "cancelada":    ("#fde8e0", "#c0392b"),
    "em_espera":    ("#e8edf2", "#6b7c8e"),
}

PRI_COR = {
    "normal": ("#e8edf2", "#4a6080"),
    "urgente": ("#fff3cd", "#b8700a"),
    "critica": ("#fde8e0", "#c0392b")
}

def _btn(txt, obj):
    b = QPushButton(txt)
    b.setObjectName(obj)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


class ObraDialog(QDialog):
    def __init__(self, dao, user, obra=None, parent=None):
        super().__init__(parent)
        self.dao = dao
        self.user = user
        self.obra = obra
        self.setWindowTitle("Nova Obra" if not obra else f"Editar — {obra['numero']}")
        self.setMinimumWidth(620)
        self.resize(660, 640)
        self._build()
        if obra:
            self._preencher()

    def _build(self):
        from PyQt6.QtWidgets import QDialogButtonBox

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)

        tabs = QTabWidget()
        lay.addWidget(tabs)

        # Tab 1 — Dados gerais
        t1 = QWidget()
        t1l = QFormLayout(t1)
        t1l.setSpacing(10)

        self.inp_num = QLineEdit()
        self.inp_num.setReadOnly(bool(self.obra))
        self.inp_num.setText(self.dao.proximo_numero_obra() if not self.obra else self.obra["numero"])

        self.cmb_cli = QComboBox()
        self._load_clientes()

        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("Descrição da obra")

        self.cmb_tipo = QComboBox()
        for t in TIPOS:
            self.cmb_tipo.addItem(TIPOS_TEXTO.get(t, t), t)

        self.cmb_estado = QComboBox()
        self._preencher_estados()
        self.chk_notificar = QCheckBox("Enviar email ao cliente quando o estado mudar")
        self.chk_notificar.setToolTip("Se activo, o cliente recebe um email automático cada vez que o estado desta obra for alterado")

        self.cmb_pri = QComboBox()
        for p in PRIORIDADES:
            self.cmb_pri.addItem(p)

        self.dt_entrada = QDateEdit(QDate.currentDate())
        self.dt_entrada.setCalendarPopup(True)
        self.dt_prevista = QDateEdit(QDate.currentDate().addDays(30))
        self.dt_prevista.setCalendarPopup(True)

        t1l.addRow("Número", self.inp_num)

        if getattr(self, "_sem_clientes", False):
            cli_widget = QWidget()
            cli_lay = QVBoxLayout(cli_widget)
            cli_lay.setContentsMargins(0, 0, 0, 0)
            cli_lay.setSpacing(6)
            cli_lay.addWidget(self.cmb_cli)

            aviso_frame = QFrame()
            aviso_frame.setStyleSheet("background:#fde8e0;border:1px solid #c0392b;border-radius:6px;")
            af_lay = QHBoxLayout(aviso_frame)
            af_lay.setContentsMargins(10, 6, 10, 6)
            af_lay.setSpacing(10)

            lbl_av = QLabel("⚠️  Não existem clientes. Crie um cliente antes de registar uma obra.")
            lbl_av.setStyleSheet("font-size:11px;color:#c0392b;font-weight:600;background:transparent;")
            lbl_av.setWordWrap(True)

            btn_criar_cli = QPushButton("➕  Criar Cliente"); btn_criar_cli.setToolTip("Criar novo cliente")
            btn_criar_cli.setStyleSheet(
                "background:#c0392b;color:white;border:none;border-radius:6px;"
                "padding:4px 12px;font-weight:700;font-size:11px;"
            )
            btn_criar_cli.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_criar_cli.clicked.connect(self._criar_cliente_rapido)

            af_lay.addWidget(lbl_av, 1)
            af_lay.addWidget(btn_criar_cli)
            cli_lay.addWidget(aviso_frame)
            t1l.addRow("Cliente *", cli_widget)
        else:
            t1l.addRow("Cliente *", self.cmb_cli)

        for lbl, w in [
            ("Descrição *", self.inp_desc),
            ("Tipo", self.cmb_tipo),
            ("Estado", self.cmb_estado),
            ("Notificar cliente", self.chk_notificar),
            ("Prioridade", self.cmb_pri),
            ("Data entrada", self.dt_entrada),
            ("Data prevista", self.dt_prevista)
        ]:
            t1l.addRow(lbl, w)

        tabs.addTab(t1, "📋  Geral")

        # Tab 2 — Especificações
        t2 = QWidget()
        t2l = QFormLayout(t2)
        t2l.setSpacing(10)

        self.inp_cor = QLineEdit()
        self.inp_cor.setPlaceholderText("ex: RAL 9016 Branco")

        self.inp_acab = QLineEdit()
        self.inp_acab.setPlaceholderText("ex: Lacado, Termolacado, Anodizado")

        self.inp_vidro = QLineEdit()
        self.inp_vidro.setPlaceholderText("ex: Duplo 4/16/4")

        self.inp_medidas = QTextEdit()
        self.inp_medidas.setPlaceholderText("Medidas, quantidades, observações técnicas...")
        self.inp_medidas.setMaximumHeight(100)

        self.inp_morada = QLineEdit()
        self.inp_morada.setPlaceholderText("Morada da instalação")

        for lbl, w in [
            ("Cor / RAL", self.inp_cor),
            ("Acabamento", self.inp_acab),
            ("Vidro", self.inp_vidro),
            ("Medidas/Qtds", self.inp_medidas),
            ("Morada obra", self.inp_morada)
        ]:
            t2l.addRow(lbl, w)

        tabs.addTab(t2, "📐  Especificações")

        # Tab 3 — Financeiro
        t3 = QWidget()
        t3l = QFormLayout(t3)
        t3l.setSpacing(10)

        self.inp_orc = QDoubleSpinBox()
        self.inp_orc.setMaximum(999999)
        self.inp_orc.setSuffix(" €")
        self.inp_orc.setDecimals(2)

        self.inp_fat = QDoubleSpinBox()
        self.inp_fat.setMaximum(999999)
        self.inp_fat.setSuffix(" €")
        self.inp_fat.setDecimals(2)

        self.inp_pago = QDoubleSpinBox()
        self.inp_pago.setMaximum(999999)
        self.inp_pago.setSuffix(" €")
        self.inp_pago.setDecimals(2)

        self.inp_notas = QTextEdit()
        self.inp_notas.setPlaceholderText("Notas internas...")
        self.inp_notas.setMaximumHeight(80)

        for lbl, w in [
            ("Orçamento", self.inp_orc),
            ("Faturado", self.inp_fat),
            ("Pago", self.inp_pago),
            ("Notas", self.inp_notas)
        ]:
            t3l.addRow(lbl, w)

        tabs.addTab(t3, "💶  Financeiro")

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._guardar)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def _load_clientes(self):
        self.cmb_cli.addItem("— Seleccione um cliente —", None)
        try:
            clientes = self.dao.listar_clientes()
            for c in clientes:
                self.cmb_cli.addItem(c["nome"], c["id"])
        except:
            clientes = []

        if not clientes:
            self.cmb_cli.setStyleSheet("QComboBox { border: 1.5px solid #c0392b; color: #c0392b; }")
            self._sem_clientes = True
        else:
            self._sem_clientes = False

    def _criar_cliente_rapido(self):
        try:
            from modules.clientes import ClienteDialog
            d = ClienteDialog(self.dao, parent=self)
            if d.exec() == QDialog.DialogCode.Accepted:
                self.cmb_cli.clear()
                self._sem_clientes = False
                self.cmb_cli.setStyleSheet("")
                try:
                    clientes = self.dao.listar_clientes()
                    self.cmb_cli.addItem("— Seleccione um cliente —", None)
                    for c in clientes:
                        self.cmb_cli.addItem(c["nome"], c["id"])
                    if clientes:
                        self.cmb_cli.setCurrentIndex(self.cmb_cli.count() - 1)
                except:
                    pass
        except ImportError:
            QMessageBox.information(
                self,
                "Criar Cliente",
                "Feche esta janela, crie primeiro o cliente\ne depois registe a obra."
            )

    def _preencher_estados(self):
        """Mostra o estado actual e apenas as transições válidas."""
        self.cmb_estado.clear()
        if not self.obra:
            opcoes = ["orcamento", "confirmada"]
        else:
            actual = self.obra.get("estado", "orcamento")
            opcoes = [actual] + transicoes_permitidas(actual, self.obra.get("estado_anterior"))
        for estado in opcoes:
            self.cmb_estado.addItem(ESTADOS_TEXTO.get(estado, estado), estado)
        if self.obra:
            self.cmb_estado.setEnabled(bool(transicoes_permitidas(
                self.obra.get("estado", ""), self.obra.get("estado_anterior"))))

    def _preencher(self):
        o = self.obra
        self.inp_desc.setText(o.get("descricao", ""))

        if o.get("tipo_obra") in TIPOS:
            self.cmb_tipo.setCurrentIndex(TIPOS.index(o["tipo_obra"]))
        else:
            self.cmb_tipo.setCurrentIndex(0)

        for i in range(self.cmb_estado.count()):
            if self.cmb_estado.itemData(i) == o.get("estado"):
                self.cmb_estado.setCurrentIndex(i)
                break
        else:
            self.cmb_estado.setCurrentIndex(0)
        self.chk_notificar.setChecked(bool(o.get("notificar_cliente", 0)))

        if o.get("prioridade") in PRIORIDADES:
            self.cmb_pri.setCurrentIndex(PRIORIDADES.index(o["prioridade"]))
        else:
            self.cmb_pri.setCurrentIndex(0)

        if o.get("data_entrada"):
            try:
                self.dt_entrada.setDate(QDate.fromString(str(o["data_entrada"]), "yyyy-MM-dd"))
            except:
                pass

        if o.get("data_prevista"):
            try:
                self.dt_prevista.setDate(QDate.fromString(str(o["data_prevista"]), "yyyy-MM-dd"))
            except:
                pass

        self.inp_cor.setText(o.get("cor_perfil", ""))
        self.inp_acab.setText(o.get("acabamento", ""))
        self.inp_vidro.setText(o.get("vidro", ""))
        self.inp_medidas.setPlainText(o.get("medidas", ""))
        self.inp_morada.setText(o.get("morada_obra", ""))
        self.inp_orc.setValue(float(o.get("valor_orcamento", 0)))
        self.inp_fat.setValue(float(o.get("valor_faturado", 0)))
        self.inp_pago.setValue(float(o.get("valor_pago", 0)))
        self.inp_notas.setPlainText(o.get("notas", ""))

        for i in range(self.cmb_cli.count()):
            if self.cmb_cli.itemData(i) == o.get("cliente_id"):
                self.cmb_cli.setCurrentIndex(i)
                break

    def _guardar(self):
        if not self.inp_desc.text().strip():
            QMessageBox.warning(self, "Erro", "Preencha a descrição da obra.")
            return

        if self.cmb_cli.currentData() is None:
            self.cmb_cli.setStyleSheet("QComboBox { border: 2px solid #c0392b; color: #c0392b; }")
            QMessageBox.warning(
                self,
                "Cliente Obrigatório",
                "É obrigatório seleccionar um cliente antes de criar uma obra.\n\n"
                "Se ainda não existe, clique em '➕ Criar Cliente' para criar um."
            )
            return
        else:
            self.cmb_cli.setStyleSheet("")

        d = {
            "descricao": self.inp_desc.text().strip(),
            "numero": self.inp_num.text().strip(),
            "cliente_id": self.cmb_cli.currentData(),
            "tipo_obra": self.cmb_tipo.currentData(),
            "estado": self.cmb_estado.currentData(),
            "notificar_cliente": 1 if self.chk_notificar.isChecked() else 0,
            "prioridade": self.cmb_pri.currentText(),
            "data_entrada": self.dt_entrada.date().toString("yyyy-MM-dd"),
            "data_prevista": self.dt_prevista.date().toString("yyyy-MM-dd"),
            "cor_perfil": self.inp_cor.text(),
            "acabamento": self.inp_acab.text(),
            "vidro": self.inp_vidro.text(),
            "medidas": self.inp_medidas.toPlainText(),
            "morada_obra": self.inp_morada.text(),
            "valor_orcamento": self.inp_orc.value(),
            "valor_faturado": self.inp_fat.value(),
            "valor_pago": self.inp_pago.value(),
            "notas": self.inp_notas.toPlainText(),
            "responsavel_id": self.user.get("id")
        }

        if self.obra:
            d["id"] = self.obra["id"]

        try:
            obra_anterior = self.obra
            oid = self.dao.salvar_obra(d)
            if not obra_anterior:
                self.dao.criar_fases_obra(oid)

            from datetime import date as _date
            pago_novo = d["valor_pago"]

            if oid:
                existente = self.dao.fetchone(
                    "SELECT SUM(CASE WHEN tipo='receita' THEN valor ELSE 0 END) AS rec FROM financeiro WHERE obra_id=%s",
                    (oid,)
                )
                ja_recebido = float(existente["rec"] or 0) if existente else 0

                if pago_novo > ja_recebido:
                    delta = pago_novo - ja_recebido
                    cat = "Adiantamento" if ja_recebido == 0 else "Pagamento parcial"
                    self.dao.salvar_financeiro({
                        "tipo": "receita",
                        "categoria": cat,
                        "descricao": f"Recebimento obra {d['numero']}",
                        "valor": delta,
                        "data": str(_date.today()),
                        "obra_id": oid,
                        "pago": 1
                    })
            # Registar histórico
            try:
                user_nome = self.user.get("nome","") if self.user else None
                if not obra_anterior:
                    self.dao.registar_historico(oid, "Obra criada",
                        f"Nº {d['numero']} — {d.get('descricao','')}",
                        utilizador_nome=user_nome)
                else:
                    alteracoes = []
                    if obra_anterior.get("estado") != d.get("estado"):
                        alteracoes.append(f"Estado: {obra_anterior.get('estado','')} → {d.get('estado','')}")
                    if obra_anterior.get("prioridade") != d.get("prioridade"):
                        alteracoes.append(f"Prioridade: {obra_anterior.get('prioridade','')} → {d.get('prioridade','')}")
                    if obra_anterior.get("valor_orcamento") != d.get("valor_orcamento"):
                        alteracoes.append(f"Orçamento: {obra_anterior.get('valor_orcamento',0):.2f}€ → {d.get('valor_orcamento',0):.2f}€")
                    self.dao.registar_historico(oid, "Obra editada",
                        "; ".join(alteracoes) if alteracoes else "Dados actualizados",
                        utilizador_nome=user_nome)
            except: pass
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))


class ObrasWidget(QWidget):
    def __init__(self, dao, user):
        super().__init__()
        self.dao = dao
        self.user = user
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        fbar = QWidget()
        fbar.setStyleSheet(f"background:{CORES['branco']};border-bottom:1px solid {CORES['alum_mid']};")
        fl = QHBoxLayout(fbar)
        fl.setContentsMargins(16, 10, 16, 10)
        fl.setSpacing(10)

        self.inp_filtro = QLineEdit()
        self.inp_filtro.setPlaceholderText("🔍  Pesquisar obra, cliente...")
        self.inp_filtro.setMaximumWidth(400)
        self.inp_filtro.textChanged.connect(self._filtro_changed)

        self.cmb_estado = QComboBox()
        self.cmb_estado.addItem("Todos os estados", None)
        for estado in ESTADOS:
            self.cmb_estado.addItem(ESTADOS_TEXTO.get(estado, estado), estado)
        self.cmb_estado.currentIndexChanged.connect(self.refresh)

        fl.addWidget(self.inp_filtro)
        fl.addWidget(self.cmb_estado)
        btn_exp = _btn("📤 Exportar","btn_outline")
        btn_exp.clicked.connect(self._exportar)
        fl.addStretch()
        fl.addWidget(btn_exp)
        fl.addStretch()
        lay.addWidget(fbar)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Número", "Cliente", "Descrição", "Tipo",
            "Estado", "Prioridade", "Data Entrada", "Ações"
        ])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 105)   # Número
        self.table.setColumnWidth(1, 250)   # Cliente
        self.table.setColumnWidth(2, 200)   # Descrição — stretch
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(3, 110)   # Tipo
        self.table.setColumnWidth(4, 120)   # Estado
        self.table.setColumnWidth(5, 90)    # Prioridade
        self.table.setColumnWidth(6, 110)   # Data Entrada
        self.table.setColumnWidth(7, 140)   # Ações
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._abrir_detalhe)
        lay.addWidget(self.table)

    def _filtro_changed(self, texto):
        if texto.strip():
            self.cmb_estado.blockSignals(True)
            self.cmb_estado.setCurrentIndex(0)
            self.cmb_estado.blockSignals(False)
        self.refresh()

    def refresh(self):
        filtro = self.inp_filtro.text()
        estado = None if filtro.strip() else self.cmb_estado.currentData()

        try:
            obras = self.dao.listar_obras(filtro, estado)
        except:
            obras = []

        self.table.setRowCount(len(obras))

        for r, o in enumerate(obras):
            bg_e, fg_e = ESTADO_COR.get(o["estado"], ("#e8edf2", "#4a6080"))
            bg_p, fg_p = PRI_COR.get(o["prioridade"], ("#e8edf2", "#4a6080"))

            vals = [
                o["numero"],
                o.get("cliente_nome", "—"),
                o["descricao"],
                TIPOS_TEXTO.get(o.get("tipo_obra",""), o.get("tipo_obra","") or "—"),
                "",
                "",
                str(o["data_entrada"]) if o.get("data_entrada") else "—"
            ]

            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setData(Qt.ItemDataRole.UserRole, o["id"])
                self.table.setItem(r, c, item)

            est_lbl = QLabel(ESTADOS_TEXTO.get(o["estado"], o["estado"].replace("_", " ").title()))
            est_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            est_lbl.setStyleSheet(
                f"background:{bg_e};color:{fg_e};border-radius:10px;"
                f"padding:2px 8px;font-size:11px;font-weight:600;margin:4px;"
            )
            self.table.setCellWidget(r, 4, est_lbl)

            pri_lbl = QLabel(o["prioridade"])
            pri_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pri_lbl.setStyleSheet(
                f"background:{bg_p};color:{fg_p};border-radius:10px;"
                f"padding:2px 8px;font-size:11px;font-weight:600;margin:4px;"
            )
            self.table.setCellWidget(r, 5, pri_lbl)

            from PyQt6.QtWidgets import QMenu

            acoes = QWidget()
            al = QHBoxLayout(acoes)
            al.setContentsMargins(4, 2, 4, 2)

            bmenu = QPushButton("Ações ▾"); bmenu.setToolTip("Ver acções disponíveis para esta obra")
            bmenu.setFixedHeight(28)
            bmenu.setStyleSheet(
                "background:#e8edf2;border:1px solid #c8d4de;"
                "border-radius:6px;padding:0 10px;font-size:12px;"
                "font-weight:600;color:#1a2332;"
            )
            bmenu.setCursor(Qt.CursorShape.PointingHandCursor)

            def _show_menu(checked, oid=o["id"], estado=o["estado"], btn=bmenu):
                menu = QMenu(btn)
                menu.addAction("✏️  Editar", lambda: self._editar(oid))
                menu.addAction("🖨️  Imprimir Orçamento", lambda: self._imprimir_orcamento(oid))
                menu.addAction("📋  Fases de produção", lambda: self._fases(oid))
                menu.addSeparator()

                sub = menu.addMenu("🔄  Mudar estado")
                actual = sub.addAction("✓  " + ESTADOS_TEXTO.get(estado, estado))
                actual.setEnabled(False)
                permitidas = transicoes_permitidas(estado, o.get("estado_anterior"))
                if permitidas:
                    sub.addSeparator()
                    for est_key in permitidas:
                        a = sub.addAction("    " + ESTADOS_TEXTO.get(est_key, est_key))
                        a.triggered.connect(
                            lambda checked, ek=est_key, oid2=oid: self._mudar_estado_direto(ek, oid2)
                        )
                else:
                    fim = sub.addAction("    (estado final — sem alterações)")
                    fim.setEnabled(False)

                menu.addSeparator()
                menu.addAction("📎  Anexos", lambda: self._anexos(oid))
                menu.addAction("📜  Histórico", lambda: self._historico(oid))
                menu.addAction("🗑️  Eliminar", lambda: self._eliminar(oid))
                menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))

            bmenu.clicked.connect(_show_menu)

            # Botão notificação toggle
            notificar = bool(o.get("notificar_cliente", 0))
            btn_not = QPushButton("🔔" if notificar else "🔕")
            btn_not.setFixedSize(28, 28)
            btn_not.setCheckable(True)
            btn_not.setChecked(notificar)
            btn_not.setToolTip("Notificações por email activas — clique para desactivar" if notificar else "Notificações por email inactivas — clique para activar")
            btn_not.setStyleSheet(
                f"background:{'#d4f0dc' if notificar else '#e8edf2'};"
                "border:none;border-radius:6px;font-size:14px;"
            )
            btn_not.setCursor(Qt.CursorShape.PointingHandCursor)
            def _toggle_notif(checked, oid=o["id"], btn=btn_not):
                try:
                    self.dao.execute("UPDATE obras SET notificar_cliente=%s WHERE id=%s", (1 if checked else 0, oid))
                    btn.setText("🔔" if checked else "🔕")
                    btn.setToolTip("Notificações por email activas — clique para desactivar" if checked else "Notificações por email inactivas — clique para activar")
                    btn.setStyleSheet(
                        f"background:{'#d4f0dc' if checked else '#e8edf2'};"
                        "border:none;border-radius:6px;font-size:14px;"
                    )
                except Exception as e:
                    print(f"Erro toggle notif: {e}")
            btn_not.toggled.connect(_toggle_notif)
            al.addWidget(bmenu)
            al.addWidget(btn_not)
            self.table.setCellWidget(r, 7, acoes)

        self.table.resizeRowsToContents()

    def _mudar_estado_direto(self, novo_estado, oid):
        try:
            obra_antes = self.dao.get_obra(oid)
            if not obra_antes:
                return
            estado_antes = obra_antes.get("estado", "")

            erro = validar_transicao(estado_antes, novo_estado, obra_antes.get("estado_anterior"))
            if erro:
                QMessageBox.warning(self, "Estado inválido", erro)
                return

            if novo_estado == "em_espera":
                self.dao.execute(
                    "UPDATE obras SET estado=%s, estado_anterior=%s WHERE id=%s",
                    (novo_estado, estado_antes, oid))
            elif estado_antes == "em_espera":
                self.dao.execute(
                    "UPDATE obras SET estado=%s, estado_anterior=NULL WHERE id=%s",
                    (novo_estado, oid))
            else:
                self.dao.execute("UPDATE obras SET estado=%s WHERE id=%s", (novo_estado, oid))

            try:
                self.dao.registar_historico(oid, "Mudança de estado",
                    f"{ESTADOS_TEXTO.get(estado_antes, estado_antes)} → "
                    f"{ESTADOS_TEXTO.get(novo_estado, novo_estado)}",
                    utilizador_nome=self.user.get("nome", "") if self.user else None)
            except Exception:
                pass

            self.refresh()
            if obra_antes.get("notificar_cliente"):
                self._notificar_cliente_estado(oid, novo_estado)
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def _notificar_cliente_estado(self, oid, novo_estado):
        try:
            from modules.email_sender import _credenciais
            from modules.dao import get_cliente
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from modules.configuracao import carregar_oficina

            obra    = self.dao.get_obra(oid)
            cliente = self.dao.get_cliente(obra.get("cliente_id")) if obra else None
            if not cliente or not cliente.get("email"):
                return

            oficina   = carregar_oficina()
            nome_emp  = oficina.get("nome","Empresa")
            email_cli = cliente.get("email")
            nome_cli  = cliente.get("nome","")
            num_obra  = obra.get("numero","")
            descricao = obra.get("descricao","")

            ESTADOS_TEXTO = {
                "orcamento":   "Orçamento",
                "confirmada":  "Confirmada",
                "em_producao": "Em Produção",
                "em_montagem": "Em Montagem",
                "concluida":   "Concluída ✅",
                "cancelada":   "Cancelada ❌",
            }
            estado_txt = ESTADOS_TEXTO.get(novo_estado, novo_estado)

            smtp_user, smtp_pass = _credenciais()

            corpo_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/></head>
<body style="font-family:Arial,sans-serif;font-size:13px;color:#1a2332;max-width:600px;margin:0 auto;padding:20px;">
  <div style="background:#1a2332;padding:20px 24px;border-radius:8px 8px 0 0;">
    <h2 style="color:#d4560a;margin:0;">⚙️  {nome_emp}</h2>
    <p style="color:rgba(255,255,255,0.6);margin:4px 0 0;font-size:11px;">Actualização de estado da obra</p>
  </div>
  <div style="border:1px solid #e8edf2;border-top:none;padding:24px;border-radius:0 0 8px 8px;">
    <p>Exmo(a). Sr(a). <b>{nome_cli}</b>,</p>
    <p>Informamos que o estado da sua obra foi actualizado:</p>
    <div style="background:#f0f4f8;border-left:4px solid #d4560a;padding:12px 16px;margin:16px 0;border-radius:4px;">
      <b style="font-size:14px;">{descricao}</b><br/>
      <span style="color:#6b7c8e;font-size:12px;">Ref: {num_obra}</span><br/>
      <span style="font-size:14px;font-weight:700;color:#1a2332;">Estado: {estado_txt}</span>
    </div>
    <p>Para qualquer esclarecimento não hesite em contactar-nos.</p>
    <p>Com os melhores cumprimentos,<br/><b>{oficina.get('responsavel', nome_emp)}</b><br/>
    <span style="color:#6b7c8e;">{nome_emp}</span></p>
  </div>
</body></html>"""

            msg = MIMEMultipart("alternative")
            msg["From"]    = f"{nome_emp} <{smtp_user}>"
            msg["To"]      = f"{nome_cli} <{email_cli}>"
            msg["Subject"] = f"Actualização obra {num_obra} — {estado_txt}"

            msg.attach(MIMEText(corpo_html, "html", "utf-8"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as s:
                s.login(smtp_user, smtp_pass)
                s.send_message(msg)
            print(f"[EMAIL] Notificação enviada para {email_cli}")
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setWindowTitle("📧  Email Enviado")
            msg.setText(f"✅  Notificação enviada com sucesso!")
            msg.setInformativeText(f"O cliente <b>{nome_cli}</b> foi notificado por email sobre a actualização do estado da obra <b>{num_obra}</b>.")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.exec()
        except Exception as e:
            print(f"[EMAIL] Aviso: não foi possível enviar notificação: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(None, "⚠️  Email não enviado",
                f"Não foi possível enviar o email de notificação:\n{str(e)[:120]}")

    def _imprimir_orcamento(self, oid):
        try:
            obra = self.dao.get_obra(oid)
        except:
            return
        from modules.orcamento import OrcamentoDialog
        d = OrcamentoDialog(self.dao, obra, parent=self)
        d.exec()

    def _mudar_estado(self, oid, estado_atual):
        from PyQt6.QtWidgets import QInputDialog
        ESTADOS_LISTA = ["orcamento", "confirmada", "em_producao", "em_montagem", "concluida", "cancelada"]
        LABELS = {
            "orcamento": "Orçamento",
            "confirmada": "Confirmada",
            "em_producao": "Em Produção",
            "em_montagem": "Em Montagem",
            "concluida": "Concluída",
            "cancelada": "Cancelada"
        }
        idx = ESTADOS_LISTA.index(estado_atual) if estado_atual in ESTADOS_LISTA else 0
        opcoes = [LABELS[e] for e in ESTADOS_LISTA]
        escolha, ok = QInputDialog.getItem(self, "Mudar Estado", "Novo estado da obra:", opcoes, idx, False)
        if ok:
            novo = ESTADOS_LISTA[opcoes.index(escolha)]
            self._mudar_estado_direto(novo, oid)

    def _exportar(self):
        try:
            obras = self.dao.listar_obras()
            LABELS = {"orcamento":"Orçamento","confirmada":"Confirmada","em_producao":"Em Produção",
                      "em_montagem":"Em Montagem","concluida":"Concluída","cancelada":"Cancelada","em_espera":"Em Espera"}
            colunas = ["Número","Cliente","Descrição","Tipo","Estado","Prioridade","Data Entrada","Data Prevista","Orçamento (€)"]
            linhas = [[
                o["numero"], o.get("cliente_nome",""), o.get("descricao",""),
                o.get("tipo_obra",""), LABELS.get(o.get("estado",""),o.get("estado","")),
                o.get("prioridade",""), str(o.get("data_entrada",""))[:10],
                str(o.get("data_prevista",""))[:10], float(o.get("valor_orcamento",0))
            ] for o in obras]
            from modules.exportar import dialogo_exportar
            dialogo_exportar(self, "Obras", colunas, linhas)
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def novo(self):
        try:
            clientes = self.dao.listar_clientes()
        except:
            clientes = []

        if not clientes:
            resposta = QMessageBox.question(
                self,
                "Sem Clientes Registados",
                "Não existem clientes registados.\n\n"
                "É obrigatório ter pelo menos um cliente para criar uma obra.\n\n"
                "Deseja criar um cliente agora?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if resposta == QMessageBox.StandardButton.Yes:
                try:
                    from modules.clientes import ClienteDialog
                    d = ClienteDialog(self.dao, parent=self)
                    d.exec()
                    try:
                        clientes = self.dao.listar_clientes()
                    except:
                        clientes = []
                    if not clientes:
                        return
                except ImportError:
                    QMessageBox.information(
                        self,
                        "Criar Cliente",
                        "Aceda ao menu de Clientes para criar um cliente primeiro."
                    )
                    return
            else:
                return

        d = ObraDialog(self.dao, self.user, parent=self)
        if d.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _editar(self, oid):
        try:
            obra = self.dao.get_obra(oid)
        except:
            return
        d = ObraDialog(self.dao, self.user, obra, parent=self)
        if d.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _historico(self, oid):
        try:
            obra = self.dao.get_obra(oid)
            if not obra: return
            from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTableWidget,
                QTableWidgetItem, QHeaderView, QDialogButtonBox, QLabel)
            dlg = QDialog(self); dlg.setWindowTitle(f"📜  Histórico — {obra['numero']}")
            dlg.setMinimumSize(580, 380)
            lay = QVBoxLayout(dlg); lay.setContentsMargins(16,16,16,16)
            lay.addWidget(QLabel(f"<b>Histórico de alterações — {obra['numero']}</b>"))
            tbl = QTableWidget(); tbl.setColumnCount(4)
            tbl.setHorizontalHeaderLabels(["Data","Utilizador","Ação","Detalhe"])
            hh = tbl.horizontalHeader()
            hh.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
            hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
            tbl.setColumnWidth(0, 130); tbl.setColumnWidth(1, 120); tbl.setColumnWidth(2, 120)
            tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            tbl.verticalHeader().setVisible(False)
            tbl.setAlternatingRowColors(True)
            historico = self.dao.listar_historico(oid)
            tbl.setRowCount(len(historico))
            for r, h in enumerate(historico):
                for c, v in enumerate([str(h.get("criado_em",""))[:16],
                                        h.get("utilizador_nome","—") or "—",
                                        h.get("acao",""),
                                        h.get("detalhe","") or ""]):
                    tbl.setItem(r, c, QTableWidgetItem(v))
            if not historico:
                tbl.setRowCount(1)
                tbl.setItem(0, 0, QTableWidgetItem("Sem registos de alterações"))
            lay.addWidget(tbl)
            bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            bb.rejected.connect(dlg.reject); lay.addWidget(bb)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def _anexos(self, oid):
        try:
            obra = self.dao.get_obra(oid)
            if not obra: return
            from modules.obra_anexos import AnexosDialog
            d = AnexosDialog(self.dao, obra, parent=self)
            d.exec()
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def _eliminar(self, oid):
        r = QMessageBox.question(
            self,
            "Eliminar obra",
            "Tem a certeza? Esta acção não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if r == QMessageBox.StandardButton.Yes:
            try:
                self.dao.execute("DELETE FROM obras WHERE id=%s", (oid,))
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Erro", str(e))

    def _fases(self, oid):
        try:
            obra = self.dao.get_obra(oid)
            if obra:
                d = FasesDialog(self.dao, self.user, obra, parent=self)
                d.exec()
            else:
                QMessageBox.warning(self, "Erro", f"Obra {oid} não encontrada!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def _abrir_detalhe(self, idx):
        oid = self.table.item(idx.row(), 0).data(Qt.ItemDataRole.UserRole)
        if oid:
            self._editar(oid)


class FasesDialog(QDialog):
    FASE_ICO = {
        "corte": "✂️",
        "furação": "🔩",
        "montagem": "🔧",
        "vidro": "🪟",
        "acabamento": "🎨",
        "instalacao": "🏗️",
        "revisao": "🔍",
        "entrega": "🚚"
    }

    FASE_ESTADOS = [
        ("pendente", "Pendente"),
        ("em_curso", "Em Curso"),
        ("concluida", "Concluída"),
        ("bloqueada", "Bloqueada")
    ]

    FASE_COR = {
        "pendente": ("#e8edf2", "#4a6080"),
        "em_curso": ("#fff3cd", "#b8700a"),
        "concluida": ("#d4edda", "#1e7e44"),
        "bloqueada": ("#fde8e0", "#c0392b")
    }

    FASES_STD = ["corte", "furação", "montagem", "vidro", "acabamento", "instalacao", "revisao", "entrega"]

    def __init__(self, dao, user, obra, parent=None):
        super().__init__(parent)
        self.dao = dao
        self.user = user
        self.obra = obra
        self.setWindowTitle(f"Fases — {obra['numero']}")
        self.setMinimumWidth(560)
        self.resize(600, 520)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)

        tit = QLabel(f"🔨  {obra['descricao']}")
        tit.setStyleSheet(f"font-size:14px;font-weight:700;color:{CORES['aco']};")
        lay.addWidget(tit)

        self.fases_lay = QVBoxLayout()
        self.fases_lay.setSpacing(6)
        cw = QWidget()
        cw.setLayout(self.fases_lay)
        sa = QScrollArea()
        sa.setWidget(cw)
        sa.setWidgetResizable(True)
        sa.setFrameShape(QFrame.Shape.NoFrame)
        lay.addWidget(sa)

        self._garantir_fases()
        self._load()

        bw = QWidget()
        bl = QHBoxLayout(bw)
        bl.setContentsMargins(0, 4, 0, 0)

        info = QLabel("✅  As alterações são guardadas automaticamente.")
        info.setStyleSheet(f"font-size:11px;color:{CORES['cinza']};")

        btn_fechar = QPushButton("✔  Guardar e Fechar"); btn_fechar.setToolTip("Guardar alterações e fechar")
        btn_fechar.setFixedHeight(36)
        btn_fechar.setStyleSheet(
            f"background:{CORES['laranja']};color:white;border:none;"
            f"border-radius:8px;padding:0 20px;font-weight:600;font-size:13px;"
        )
        btn_fechar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_fechar.clicked.connect(self.accept)

        bl.addWidget(info)
        bl.addStretch()
        bl.addWidget(btn_fechar)
        lay.addWidget(bw)

    def _garantir_fases(self):
        from db.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()

        fases_padrao = [
            ("corte", 0),
            ("furação", 1),
            ("montagem", 2),
            ("vidro", 3),
            ("acabamento", 4),
            ("revisao", 5),
            ("instalacao", 6),
            ("entrega", 7)
        ]

        for fase, ordem in fases_padrao:
            cursor.execute(
                "INSERT IGNORE INTO obra_fases (obra_id, fase, estado, ordem) VALUES (%s, %s, 'pendente', %s)",
                (self.obra["id"], fase, ordem)
            )

        conn.commit()
        cursor.close()
        conn.close()

    def _load(self):
        while self.fases_lay.count():
            it = self.fases_lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        from db.database import get_connection
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM obra_fases WHERE obra_id=%s ORDER BY ordem", (self.obra["id"],))
        fases = cur.fetchall()
        cur.close()
        conn.close()

        for f in fases:
            card = QFrame()
            bg_c, _ = self.FASE_COR.get(f["estado"], ("#e8edf2", "#4a6080"))
            card.setStyleSheet(f"background:{bg_c};border:1px solid {CORES['alum_mid']};border-radius:10px;")
            cl = QHBoxLayout(card)
            cl.setContentsMargins(14, 10, 14, 10)

            ico = self.FASE_ICO.get(f["fase"], "⚙️")
            il = QLabel(f"{ico}  {f['fase'].replace('_', ' ').title()}")
            il.setStyleSheet(f"font-size:13px;font-weight:600;color:{CORES['aco']};min-width:160px;")

            bg, fg = self.FASE_COR.get(f["estado"], ("#e8edf2", "#4a6080"))
            sl = QLabel(f["estado"].replace("_", " ").title())
            sl.setStyleSheet(
                f"background:white;color:{fg};border-radius:10px;"
                f"padding:2px 9px;font-size:11px;font-weight:600;min-width:80px;"
            )
            sl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            cmb = QComboBox()
            for valor, texto in self.FASE_ESTADOS:
                print(f"📋 A adicionar ao combobox: valor='{valor}', texto='{texto}'")
                cmb.addItem(texto, valor)

            index = cmb.findData(f["estado"])
            if index >= 0:
                cmb.setCurrentIndex(index)

            cmb.setMaximumWidth(140)
            fid = f["id"]

            cmb.currentIndexChanged.connect(
                lambda idx, f=fid, cb=cmb: self._update_fase(f, cb.currentData())
            )

            cl.addWidget(il)
            cl.addWidget(sl)
            cl.addStretch()
            cl.addWidget(cmb)
            self.fases_lay.addWidget(card)

    def _update_fase(self, fid, estado):
        """Atualiza o estado de uma fase"""
        print(f"🔧 DEBUG _update_fase - INÍCIO")
        print(f"   - ID da fase: {fid}")
        print(f"   - Estado recebido: '{estado}'")
        print(f"   - Tipo do estado: {type(estado)}")
        
        from db.database import get_connection

        try:
            # Verificar se o estado é válido
            estados_validos = ["pendente", "em_curso", "concluida", "bloqueada"]
            print(f"   - Estados válidos: {estados_validos}")
            
            if estado not in estados_validos:
                print(f"❌ ERRO: Estado '{estado}' não está na lista de válidos!")
                QMessageBox.critical(self, "Erro", f"Estado '{estado}' não é válido!")
                return
            else:
                print(f"✅ Estado '{estado}' é válido")
            
            # Atualizar a fase
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE obra_fases SET estado=%s WHERE id=%s", (estado, fid))
            conn.commit()
            print(f"✅ Base de dados atualizada com sucesso para '{estado}'")
            cur.close()
            conn.close()

            # Verificar estado global da obra
            conn2 = get_connection()
            cur2 = conn2.cursor()
            cur2.execute("SELECT estado FROM obra_fases WHERE obra_id=%s", (self.obra["id"],))
            rows = cur2.fetchall()
            estados = [r[0] for r in rows]
            print(f"📊 Estados atuais das fases: {estados}")

            if all(e == "concluida" for e in estados):
                cur2.execute("UPDATE obras SET estado='concluida' WHERE id=%s", (self.obra["id"],))
                print("✅ Todas as fases concluídas")
            elif any(e == "em_curso" for e in estados):
                cur2.execute(
                    "UPDATE obras SET estado='em_producao' WHERE id=%s AND estado NOT IN ('concluida','cancelada')",
                    (self.obra["id"],)
                )
                print("⚙️ Obra em produção")

            conn2.commit()
            cur2.close()
            conn2.close()

            self._load()
            print("✅ Interface recarregada")

        except Exception as e:
            print(f"❌ EXCEÇÃO: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Erro", str(e))
        
        print("🔧 DEBUG _update_fase - FIM")