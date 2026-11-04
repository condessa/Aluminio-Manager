"""Paleta e tema (claro/escuro) da aplicação.

O tema é guardado em ~/.config/aluminio-manager/tema.json e lido no arranque.
Mudar de tema requer reiniciar o programa (as páginas leem a paleta ao importar).
"""

import json
import os
from pathlib import Path

from PyQt6.QtGui import QColor, QPalette


def _pasta():
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return Path(base) / "aluminio-manager"


def _ficheiro():
    return _pasta() / "tema.json"


def tema_atual():
    try:
        return json.loads(_ficheiro().read_text(encoding="utf-8")).get("tema", "claro")
    except Exception:
        return "claro"


def guardar_tema(nome):
    nome = "escuro" if nome == "escuro" else "claro"
    pasta = _pasta()
    pasta.mkdir(parents=True, exist_ok=True)
    _ficheiro().write_text(json.dumps({"tema": nome}), encoding="utf-8")
    return nome


TEMA = tema_atual()

_CLARO = {
    "fundo": "#f0f4f8", "cartao": "#ffffff", "cartao2": "#f0f4f8",
    "aco": "#1a2332", "aco_mid": "#2c3e55",
    "alum": "#e8edf2", "alum_mid": "#c8d4de", "branco": "#ffffff",
    "cinza": "#6b7c8e", "laranja": "#d4560a",
    "danger": "#c0392b", "success": "#1e7e44", "warning": "#b8700a", "info": "#1a6fa8",
}

_ESCURO = {
    "fundo": "#1e1e1e", "cartao": "#2b2b2b", "cartao2": "#333333",
    "aco": "#e8e8e8", "aco_mid": "#c9d3dd",
    "alum": "#3a3a3a", "alum_mid": "#4a4a4a", "branco": "#2b2b2b",
    "cinza": "#a0a0a0", "laranja": "#e0702a",
    "danger": "#e06c60", "success": "#5fbf7f", "warning": "#e0a44a", "info": "#6aa9d8",
}

PALETA = _ESCURO if TEMA == "escuro" else _CLARO


def aplicar_tema(app):
    paleta = QPalette()
    paleta.setColor(QPalette.ColorRole.Window, QColor(PALETA["fundo"]))
    paleta.setColor(QPalette.ColorRole.WindowText, QColor(PALETA["aco"]))
    paleta.setColor(QPalette.ColorRole.Base, QColor(PALETA["cartao"]))
    paleta.setColor(QPalette.ColorRole.AlternateBase, QColor(PALETA["cartao2"]))
    paleta.setColor(QPalette.ColorRole.Text, QColor(PALETA["aco"]))
    paleta.setColor(QPalette.ColorRole.Button, QColor(PALETA["fundo"]))
    paleta.setColor(QPalette.ColorRole.ButtonText, QColor(PALETA["aco"]))
    paleta.setColor(QPalette.ColorRole.BrightText, QColor(PALETA["danger"]))
    paleta.setColor(QPalette.ColorRole.Highlight, QColor(PALETA["laranja"]))
    paleta.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    paleta.setColor(QPalette.ColorRole.ToolTipBase, QColor(PALETA["cartao"]))
    paleta.setColor(QPalette.ColorRole.ToolTipText, QColor(PALETA["aco"]))
    paleta.setColor(QPalette.ColorRole.PlaceholderText, QColor(PALETA["cinza"]))
    app.setPalette(paleta)


def cor_texto():
    return PALETA["aco"]


def cor_fundo():
    return PALETA["fundo"]


def cor_cartao():
    return PALETA["cartao"]


def cor_borda():
    return PALETA["alum_mid"]
