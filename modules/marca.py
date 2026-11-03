"""Logótipos do HCsoftware usados na interface."""

import sys
from pathlib import Path


def _bases():
    bases = []
    if getattr(sys, "_MEIPASS", None):
        bases.append(Path(sys._MEIPASS))
    aqui = Path(__file__).resolve().parent.parent
    bases += [aqui, aqui / "packaging"]
    return bases


def caminho(nome):
    for base in _bases():
        ficheiro = base / nome
        if ficheiro.exists():
            return str(ficheiro)
    return ""


def _pixmap(nome, largura):
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QPixmap

    ficheiro = caminho(nome)
    if not ficheiro:
        return QPixmap()
    return QPixmap(ficheiro).scaledToWidth(largura, Qt.TransformationMode.SmoothTransformation)


def logo_tile(largura=96):
    """Quadrado âmbar com «HC» (bom para fundos claros)."""
    return _pixmap("hcsoftware.png", largura)


def logo_wordmark(largura=150):
    """Assinatura «HCsoftware» (bom para fundos escuros)."""
    return _pixmap("hcsoftware-logo.png", largura)
