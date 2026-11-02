from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QMessageBox, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
def _btn(t,o): b=QPushButton(t); b.setObjectName(o); b.setCursor(Qt.CursorShape.PointingHandCursor); return b

CORES = {
    "branco": "#f8fafc",
    "alum_mid": "#c8d4de",
    "alum": "#e8edf2",
    "laranja": "#d4560a",
    "aco": "#1a2332",
    "cinza": "#6b7c8e"
}

class ClientesWidget(QWidget):
    def __init__(self, dao, user):
        super().__init__()
        self.dao = dao
        self.user = user
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        
        # Barra de ferramentas com pesquisa
        fb = QWidget()
        fb.setStyleSheet(f"background:{CORES['branco']};border-bottom:1px solid {CORES['alum_mid']};")
        fl = QHBoxLayout(fb)
        fl.setContentsMargins(16, 10, 16, 10)
        
        self.inp_f = QLineEdit()
        self.inp_f.setPlaceholderText("🔍  Pesquisar por nome ou NIF...")
        self.inp_f.setMaximumWidth(300)
        self.inp_f.textChanged.connect(self.refresh)
        
        btn_exp = _btn("📤 Exportar","btn_outline")
        btn_exp.clicked.connect(self._exportar)
        fl.addWidget(self.inp_f); fl.addStretch()
        fl.addWidget(btn_exp)
        lay.addWidget(fb)
        
        # Tabela de clientes
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        
        # Cabeçalhos
        headers = ["Nome", "NIF", "Localidade", "Telefone", "Email", "Ações"]
        self.table.setHorizontalHeaderLabels(headers)
        
        # Ajuste das larguras das colunas
        from PyQt6.QtWidgets import QHeaderView
        
        # Nome: 250px (fixo para caber nomes completos)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 250)
        
        # NIF: 90px (9 dígitos)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 90)
        
        # Localidade: 200px (para "Armação de Pêra")
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 200)
        
        # Telefone: 110px
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 110)
        
        # Email: 300px (para emails completos)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 300)
        
        # Ações: 100px
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 100)
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(
            lambda idx: self._editar(
                self.table.item(idx.row(), 0).data(Qt.ItemDataRole.UserRole)
            )
        )
        
        lay.addWidget(self.table)
        self.refresh()

    def _exportar(self):
        try:
            clientes = self.dao.listar_clientes(self.inp_f.text())
            colunas = ["Nome","NIF","Telefone","Telemóvel","Email","Morada","Localidade","C. Postal"]
            linhas = [[
                c.get("nome",""), c.get("nif",""), c.get("telefone",""),
                c.get("telemovel",""), c.get("email",""), c.get("morada",""),
                c.get("localidade",""), c.get("cp","")
            ] for c in clientes]
            from modules.exportar import dialogo_exportar
            dialogo_exportar(self, "Clientes", colunas, linhas)
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Erro", str(e))

    def refresh(self):
        filtro = self.inp_f.text()
        try:
            clientes = self.dao.listar_clientes(filtro)
        except:
            clientes = []

        self.table.setRowCount(len(clientes))

        # Cor única para todas as colunas
        COR_TEXTO  = "#1a2332"
        COR_LARANJA = "#d4560a"

        for r, c in enumerate(clientes):
            # Coluna Nome - centralizado
            item_nome = QTableWidgetItem(c.get("nome", ""))
            item_nome.setData(Qt.ItemDataRole.UserRole, c["id"])
            item_nome.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            item_nome.setForeground(QColor(COR_TEXTO))
            self.table.setItem(r, 0, item_nome)

            # Coluna NIF - centralizado
            item_nif = QTableWidgetItem(c.get("nif", ""))
            item_nif.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_nif.setForeground(QColor(COR_TEXTO))
            self.table.setItem(r, 1, item_nif)

            # Coluna Localidade - centralizado
            item_local = QTableWidgetItem(c.get("localidade", ""))
            item_local.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            item_local.setForeground(QColor(COR_TEXTO))
            self.table.setItem(r, 2, item_local)

            # Coluna Telefone - centralizado
            telefone = c.get("telefone", "")
            item_tel = QTableWidgetItem(telefone)
            item_tel.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_tel.setForeground(QColor(COR_TEXTO))
            self.table.setItem(r, 3, item_tel)

            # Coluna Email - centralizado
            email = c.get("email", "")
            item_email = QTableWidgetItem(email)
            item_email.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_email.setToolTip(email)
            item_email.setForeground(QColor(COR_TEXTO))
            self.table.setItem(r, 4, item_email)

            # Coluna Ações - ESTILO IGUAL A FUNCIONÁRIOS
            acoes = QWidget()
            layout = QHBoxLayout(acoes)
            layout.setContentsMargins(4, 2, 4, 2)
            layout.setSpacing(8)

            # Botão Editar - igual a funcionários
            btn_editar = QPushButton("✏️")
            btn_editar.setFixedHeight(26)  # 26px como em funcionários
            btn_editar.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_editar.setToolTip("Editar cliente")
            btn_editar.setStyleSheet(
                "QPushButton {"
                "   background:#e8edf2;"
                "   border:1px solid #c8d4de;"
                "   border-radius:4px;"
                "   padding:0 8px;"
                "   font-size:12px;"
                "}"
                "QPushButton:hover {"
                "   background:#d4dde6;"
                "}"
            )
            btn_editar.clicked.connect(lambda checked, x=c["id"]: self._editar(x))

            # Botão Eliminar - igual a funcionários
            btn_eliminar = QPushButton("🗑️")
            btn_eliminar.setFixedHeight(26)  # 26px como em funcionários
            btn_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_eliminar.setToolTip("Eliminar cliente")
            btn_eliminar.setStyleSheet(
                "QPushButton {"
                "   background:#fde8e0;"
                "   border:1px solid #c0392b;"
                "   border-radius:4px;"
                "   padding:0 8px;"
                "   font-size:12px;"
                "   color:#c0392b;"
                "}"
                "QPushButton:hover {"
                "   background:#fcd5c9;"
                "}"
            )
            btn_eliminar.clicked.connect(lambda checked, x=c["id"]: self._eliminar(x))

            layout.addWidget(btn_editar)
            layout.addWidget(btn_eliminar)
            layout.addStretch()

            self.table.setCellWidget(r, 5, acoes)

        self.table.resizeRowsToContents()

    def novo(self):
        try:
            from modules.cliente_dialog import ClienteDialog
            dlg = ClienteDialog(self.dao, parent=self)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                self.refresh()
        except ImportError:
            QMessageBox.information(self, "Módulo não encontrado", "Módulo cliente_dialog não encontrado.")

    def _editar(self, cliente_id):
        try:
            from modules.cliente_dialog import ClienteDialog
            cliente = self.dao.get_cliente(cliente_id)
            if cliente:
                dlg = ClienteDialog(self.dao, cliente, parent=self)
                if dlg.exec() == QDialog.DialogCode.Accepted:
                    self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao editar cliente: {str(e)}")

    def _eliminar(self, cliente_id):
        resposta = QMessageBox.question(
            self,
            "Confirmar eliminação",
            "Tem a certeza que pretende eliminar este cliente?\n"
            "Esta ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resposta == QMessageBox.StandardButton.Yes:
            try:
                self.dao.eliminar_cliente(cliente_id)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Não foi possível eliminar o cliente: {str(e)}")
