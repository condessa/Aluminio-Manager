"""
obra_anexos.py — Gestão de anexos por obra (fotos, plantas, documentos)
"""
import os
import shutil
from pathlib import Path
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QMessageBox, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

ANEXOS_DIR = Path.home() / ".config" / "aluminio-manager" / "anexos"
from modules.temas import PALETA as CORES
ICONES_TIPO = {
    "imagem": "🖼️", "pdf": "📄", "documento": "📝", "outro": "📎"
}

def _tipo_ficheiro(nome):
    ext = Path(nome).suffix.lower()
    if ext in (".jpg",".jpeg",".png",".gif",".bmp",".webp"): return "imagem"
    if ext == ".pdf": return "pdf"
    if ext in (".doc",".docx",".odt",".txt"): return "documento"
    return "outro"

def _tamanho_str(bytes):
    if bytes < 1024: return f"{bytes} B"
    if bytes < 1024*1024: return f"{bytes/1024:.1f} KB"
    return f"{bytes/1024/1024:.1f} MB"

def _btn(t, obj):
    from PyQt6.QtWidgets import QPushButton
    b = QPushButton(t); b.setObjectName(obj)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


class AnexosDialog(QDialog):
    def __init__(self, dao, obra, parent=None):
        super().__init__(parent)
        self.dao = dao
        self.obra = obra
        self.setWindowTitle(f"📎  Anexos — {obra['numero']}")
        self.setMinimumSize(640, 420)
        self._build()
        self._carregar()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(16,16,16,16); lay.setSpacing(10)

        # Cabeçalho
        top = QHBoxLayout()
        tit = QLabel(f"📎  Anexos da obra <b>{self.obra['numero']}</b> — {self.obra.get('descricao','')[:50]}")
        tit.setStyleSheet(f"font-size:13px;color:{CORES['aco']};")
        top.addWidget(tit); top.addStretch()
        btn_add = _btn("➕  Adicionar Ficheiro", "btn_primary")
        btn_add.clicked.connect(self._adicionar)
        top.addWidget(btn_add)
        lay.addLayout(top)

        # Tabela
        self.table = QTableWidget(); self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Tipo","Nome","Tamanho","Data","Ações"])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 55)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 110)
        self.table.setColumnWidth(4, 110)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._abrir)
        lay.addWidget(self.table)

        # Rodapé
        bot = QHBoxLayout()
        bot.addWidget(QLabel("💡 Duplo clique para abrir o ficheiro"))
        bot.addStretch()
        btn_fechar = _btn("Fechar", "btn_outline")
        btn_fechar.clicked.connect(self.accept)
        bot.addWidget(btn_fechar)
        lay.addLayout(bot)

    def _carregar(self):
        self._anexos = self.dao.listar_anexos(self.obra["id"])
        self.table.setRowCount(len(self._anexos))
        for r, a in enumerate(self._anexos):
            tipo = a.get("tipo","outro")
            ico = ICONES_TIPO.get(tipo, "📎")
            for c, v in enumerate([ico, a["nome_ficheiro"],
                                    _tamanho_str(a.get("tamanho",0)),
                                    str(a.get("criado_em",""))[:10], ""]):
                item = QTableWidgetItem(v)
                item.setData(Qt.ItemDataRole.UserRole, a["id"])
                if c == 0: item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(r, c, item)

            # Botões de ação
            w = QWidget(); wl = QHBoxLayout(w); wl.setContentsMargins(4,2,4,2); wl.setSpacing(4)
            ba = _btn("📂","btn_outline"); ba.setFixedHeight(26); ba.setToolTip("Abrir")
            ba.clicked.connect(lambda _, aid=a["id"]: self._abrir_por_id(aid))
            bd = _btn("🗑️","btn_danger"); bd.setFixedHeight(26); bd.setToolTip("Eliminar")
            bd.clicked.connect(lambda _, aid=a["id"]: self._eliminar(aid))
            wl.addWidget(ba); wl.addWidget(bd)
            self.table.setCellWidget(r, 4, w)
        self.table.resizeRowsToContents()

    def _adicionar(self):
        ficheiros, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar ficheiros", "",
            "Todos os ficheiros (*);;Imagens (*.jpg *.jpeg *.png *.gif);;PDF (*.pdf);;Documentos (*.doc *.docx *.odt *.txt)")
        if not ficheiros:
            return
        pasta = ANEXOS_DIR / str(self.obra["id"])
        pasta.mkdir(parents=True, exist_ok=True)
        adicionados = 0
        for src in ficheiros:
            try:
                nome = Path(src).name
                destino = pasta / nome
                # Evitar sobreposição
                contador = 1
                while destino.exists():
                    destino = pasta / f"{Path(src).stem}_{contador}{Path(src).suffix}"
                    contador += 1
                shutil.copy2(src, destino)
                tipo = _tipo_ficheiro(nome)
                tamanho = destino.stat().st_size
                self.dao.adicionar_anexo(self.obra["id"], destino.name, str(destino), tipo, tamanho)
                adicionados += 1
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Não foi possível adicionar {Path(src).name}:\n{e}")
        if adicionados:
            self._carregar()

    def _abrir(self, index):
        row = index.row()
        if row < len(self._anexos):
            self._abrir_por_id(self._anexos[row]["id"])

    def _abrir_por_id(self, aid):
        a = next((x for x in self._anexos if x["id"] == aid), None)
        if not a: return
        caminho = a.get("caminho","")
        if not Path(caminho).exists():
            QMessageBox.warning(self, "Ficheiro não encontrado",
                f"O ficheiro não existe:\n{caminho}"); return
        import subprocess, platform
        try:
            if platform.system() == "Windows":
                os.startfile(caminho)
            else:
                subprocess.Popen(["xdg-open", caminho])
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def _eliminar(self, aid):
        r = QMessageBox.question(self, "Eliminar anexo",
            "Eliminar este ficheiro permanentemente?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if r == QMessageBox.StandardButton.Yes:
            try:
                caminho = self.dao.eliminar_anexo(aid)
                if caminho and Path(caminho).exists():
                    Path(caminho).unlink()
                self._carregar()
            except Exception as e:
                QMessageBox.critical(self, "Erro", str(e))
