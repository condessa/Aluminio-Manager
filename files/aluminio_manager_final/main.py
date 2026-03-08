#!/usr/bin/env python3
"""AluminioManager — Ponto de entrada principal"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QFont

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("AluminioManager")
    app.setFont(QFont("Segoe UI", 12))

    from db.database import carregar_config, conectar
    bd_ok = False
    try:
        conn = conectar(); conn.close(); bd_ok = True
    except:
        bd_ok = False

    if not bd_ok:
        from ui.setup_wizard import SetupWizard
        wiz = SetupWizard()
        if wiz.exec() != 1:
            sys.exit(0)

    try:
        from ui.login import LoginDialog
        login = LoginDialog()
        if login.exec() != 1:
            sys.exit(0)
        utilizador = login.utilizador
    except Exception as e:
        QMessageBox.critical(None,"Erro",f"Erro ao iniciar:\n{e}")
        sys.exit(1)

    from ui.main_window import MainWindow
    win = MainWindow(utilizador)
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
