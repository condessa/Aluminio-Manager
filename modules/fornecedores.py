from modules.validacoes import aplicar_mascara_cp, aplicar_mascara_telefone, aplicar_mascara_nif, aplicar_validacao_email
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QFormLayout,
    QMessageBox, QTextEdit, QCheckBox, QDoubleSpinBox, QSpinBox, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

def _btn(t,o): b=QPushButton(t); b.setObjectName(o); b.setCursor(Qt.CursorShape.PointingHandCursor); return b

class FornecedorDialog(QDialog):
    def __init__(self, dao, parent=None, forn=None):
        super().__init__(parent)
        self.dao = dao
        self.forn = forn
        self.setWindowTitle("Novo Fornecedor" if not forn else "Editar Fornecedor")
        self.setMinimumWidth(480)
        self._build()
        aplicar_mascara_cp(self.inp_cp)
        aplicar_mascara_telefone(self.inp_tel)
        aplicar_mascara_telefone(self.inp_tlm)
        aplicar_mascara_nif(self.inp_nif)
        aplicar_validacao_email(self.inp_email)
        if forn:
            self._preencher()

    def _build(self):
        lay = QVBoxLayout(self)
        form = QFormLayout()

        self.inp_nome = QLineEdit(); self.inp_nome.setPlaceholderText("Nome do fornecedor")
        self.inp_nif = QLineEdit(); self.inp_nif.setPlaceholderText("NIF")
        self.inp_tel = QLineEdit(); self.inp_tel.setPlaceholderText("Telefone")
        self.inp_tlm = QLineEdit(); self.inp_tlm.setPlaceholderText("Telemóvel")
        self.inp_email = QLineEdit(); self.inp_email.setPlaceholderText("Email")
        aplicar_validacao_email(self.inp_email)
        self.inp_morada = QLineEdit(); self.inp_morada.setPlaceholderText("Morada")
        self.inp_localidade = QLineEdit(); self.inp_localidade.setPlaceholderText("Localidade")
        self.inp_cp = QLineEdit(); self.inp_cp.setPlaceholderText("0000-000")
        self.inp_notas = QTextEdit(); self.inp_notas.setFixedHeight(70)

        form.addRow("Nome *", self.inp_nome)
        form.addRow("NIF", self.inp_nif)
        form.addRow("Telefone", self.inp_tel)
        form.addRow("Telemóvel", self.inp_tlm)
        form.addRow("Email", self.inp_email)
        form.addRow("Morada", self.inp_morada)
        form.addRow("Localidade", self.inp_localidade)
        form.addRow("Cód. Postal", self.inp_cp)
        form.addRow("Notas", self.inp_notas)
        lay.addLayout(form)

        bt = QHBoxLayout()
        bt.addStretch()
        btn_c = _btn("Cancelar", "btn_secondary"); btn_c.clicked.connect(self.reject)
        btn_g = _btn("💾 Guardar", "btn_primary"); btn_g.clicked.connect(self._guardar)
        bt.addWidget(btn_c); bt.addWidget(btn_g)
        lay.addLayout(bt)

    def _preencher(self):
        f = self.forn
        self.inp_nome.setText(f.get("nome",""))
        self.inp_nif.setText(f.get("nif","") or "")
        self.inp_tel.setText(f.get("telefone","") or "")
        self.inp_tlm.setText(f.get("telemovel","") or "")
        self.inp_email.setText(f.get("email","") or "")
        self.inp_morada.setText(f.get("morada","") or "")
        self.inp_localidade.setText(f.get("localidade","") or "")
        self.inp_cp.setText(f.get("cp","") or "")
        self.inp_notas.setPlainText(f.get("notas","") or "")

    def _guardar(self):
        nome = self.inp_nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Atenção", "O nome é obrigatório."); return
        email = self.inp_email.text().strip()
        if email and "@" not in email:
            QMessageBox.warning(self, "Atenção", "O email não é válido."); return
        tel = self.inp_tel.text().strip()
        if tel and (len(tel) != 9 or not tel.isdigit()):
            QMessageBox.warning(self, "Atenção", "O telefone deve ter 9 dígitos."); return
        tlm = self.inp_tlm.text().strip()
        if tlm and (len(tlm) != 9 or not tlm.isdigit()):
            QMessageBox.warning(self, "Atenção", "O telemóvel deve ter 9 dígitos."); return
        d = {
            "id": self.forn["id"] if self.forn else None,
            "nome": nome, "nif": self.inp_nif.text().strip(),
            "telefone": self.inp_tel.text().strip(), "telemovel": self.inp_tlm.text().strip(),
            "email": self.inp_email.text().strip(), "morada": self.inp_morada.text().strip(),
            "localidade": self.inp_localidade.text().strip(), "cp": self.inp_cp.text().strip(),
            "notas": self.inp_notas.toPlainText().strip()
        }
        self.dao.salvar_fornecedor(d)
        self.accept()


class FornecedoresWidget(QWidget):
    def __init__(self, dao, utilizador):
        super().__init__()
        self.dao = dao
        self.utilizador = utilizador
        self._build()
        self.refresh()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24,24,24,24); lay.setSpacing(16)

        # Título
        tit = QLabel("🏭  Fornecedores")
        tit.setStyleSheet("font-size:22px;font-weight:700;color:#1a2332;")
        lay.addWidget(tit)

        # Barra de filtros
        fb = QWidget(); fl = QHBoxLayout(fb); fl.setContentsMargins(0,0,0,0)
        self.inp_f = QLineEdit()
        self.inp_f.setPlaceholderText("🔍  Pesquisar fornecedor...")
        self.inp_f.setMaximumWidth(300)
        self.inp_f.textChanged.connect(self.refresh)

        btn_exp = _btn("📤 Exportar", "btn_outline")
        btn_exp.clicked.connect(self._exportar)
        fl.addWidget(self.inp_f); fl.addStretch()
        fl.addWidget(btn_exp)
        lay.addWidget(fb)

        # Tabela
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Nome","NIF","Telefone","Telemóvel","Email","Localidade","Ações"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 160)
        self.table.setColumnWidth(5, 120)
        self.table.setColumnWidth(6, 90)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        lay.addWidget(self.table)

    def refresh(self):
        forns = self.dao.listar_fornecedores(self.inp_f.text())
        self.table.setRowCount(len(forns))
        for r, f in enumerate(forns):
            for c, v in enumerate([
                f.get("nome",""), f.get("nif","") or "",
                f.get("telefone","") or "", f.get("telemovel","") or "",
                f.get("email","") or "", f.get("localidade","") or ""
            ]):
                self.table.setItem(r, c, QTableWidgetItem(v))

            w = QWidget(); wl = QHBoxLayout(w); wl.setContentsMargins(4,2,4,2); wl.setSpacing(4)
            be = _btn("✏️","btn_outline"); be.setFixedHeight(26); be.setToolTip("Editar")
            be.clicked.connect(lambda _, fid=f["id"]: self._editar(fid))
            bd = _btn("🗑️","btn_danger"); bd.setFixedHeight(26); bd.setToolTip("Eliminar")
            bd.clicked.connect(lambda _, fid=f["id"]: self._eliminar(fid))
            wl.addWidget(be); wl.addWidget(bd)
            self.table.setCellWidget(r, 6, w)
        self.table.resizeRowsToContents()

    def novo(self):
        self._novo()

    def _novo(self):
        dlg = FornecedorDialog(self.dao, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _editar(self, fid):
        f = self.dao.get_fornecedor(fid)
        if f:
            dlg = FornecedorDialog(self.dao, self, f)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                self.refresh()

    def _eliminar(self, fid):
        r = QMessageBox.question(self, "Eliminar", "Tem a certeza?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if r == QMessageBox.StandardButton.Yes:
            self.dao.eliminar_fornecedor(fid)
            self.refresh()

    def _exportar(self):
        try:
            forns = self.dao.listar_fornecedores(self.inp_f.text())
            colunas = ["Nome","NIF","Telefone","Telemóvel","Email","Morada","Localidade","C. Postal"]
            linhas = [[f.get("nome",""),f.get("nif",""),f.get("telefone",""),
                f.get("telemovel",""),f.get("email",""),f.get("morada",""),
                f.get("localidade",""),f.get("cp","")] for f in forns]
            from modules.exportar import dialogo_exportar
            dialogo_exportar(self, "Fornecedores", colunas, linhas)
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))
