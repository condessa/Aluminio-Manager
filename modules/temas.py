"""Paleta e cores da aplicação.

O Alumínio Manager foi desenhado com páginas claras e barra lateral escura.
Forçar a paleta clara evita que o modo escuro do Windows transforme as tabelas
em fundo escuro com texto escuro.
"""

from PyQt6.QtGui import QColor, QPalette


def aplicar_paleta_clara(app):
    paleta = QPalette()
    paleta.setColor(QPalette.ColorRole.Window, QColor("#f0f4f8"))
    paleta.setColor(QPalette.ColorRole.WindowText, QColor("#1a2332"))
    paleta.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
    paleta.setColor(QPalette.ColorRole.AlternateBase, QColor("#eef2f7"))
    paleta.setColor(QPalette.ColorRole.Text, QColor("#1a2332"))
    paleta.setColor(QPalette.ColorRole.Button, QColor("#f0f4f8"))
    paleta.setColor(QPalette.ColorRole.ButtonText, QColor("#1a2332"))
    paleta.setColor(QPalette.ColorRole.BrightText, QColor("#c0392b"))
    paleta.setColor(QPalette.ColorRole.Highlight, QColor("#d4560a"))
    paleta.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    paleta.setColor(QPalette.ColorRole.ToolTipBase, QColor("#ffffff"))
    paleta.setColor(QPalette.ColorRole.ToolTipText, QColor("#1a2332"))
    paleta.setColor(QPalette.ColorRole.PlaceholderText, QColor("#8a97a6"))
    app.setPalette(paleta)


def cor_texto():
    from PyQt6.QtWidgets import QApplication
    return QApplication.palette().color(QPalette.ColorRole.WindowText).name()


def cor_fundo():
    from PyQt6.QtWidgets import QApplication
    return QApplication.palette().color(QPalette.ColorRole.Window).name()
