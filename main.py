"""AluminioManager — Programa principal"""
import sys
import importlib
from PyQt6.QtWidgets import QApplication, QMessageBox, QDialog
from db.database import get_connection as conectar, criar_base_dados

def inicializar_bd():
    try:
        conn = conectar(); conn.close()
        print("[DB] Base de dados encontrada.")
    except Exception:
        print("[DB] A criar base de dados...")
        try:
            criar_base_dados()
            print("[DB] Base de dados criada com sucesso.")
        except Exception as err:
            print("[DB] Erro:", err); raise err

def verificar_licenca_arranque(app):
    """Verifica licença no arranque — regista trial ou bloqueia se expirado"""
    from modules.licenca import verificar, inicializar, licenca_valida
    from modules.licenca_dialog import LicencaDialog

    estado = verificar()

    # Primeira execução — registar trial
    if estado.get("estado") == "nao_registado":
        inicializar()
        estado = verificar()

    s = estado.get("estado","")
    dias = estado.get("dias_restantes", 0)

    # Trial com poucos dias — avisar mas deixar entrar
    if s == "trial" and dias <= 5:
        dlg = LicencaDialog("trial", dias)
        dlg.exec()
        # Verificar se activou
        estado = verificar()
        if estado.get("estado") == "expirado":
            return False

    # Trial expirado — bloquear
    elif s == "expirado":
        dlg = LicencaDialog("expirado", 0)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return False
        estado = verificar()
        if estado.get("estado") != "ativo":
            return False

    return True

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Aluminios Manager by HCsoftware")
    app.setStyleSheet("""
        QComboBox {
            background-color: #ffffff; color: #1a2332;
            border: 1px solid #c8d4de; border-radius: 4px;
            padding: 4px 8px; min-height: 26px;
        }
        QComboBox:hover { border-color: #d4560a; }
        QComboBox::drop-down { border: none; width: 20px; }
        QComboBox QAbstractItemView {
            background-color: #ffffff; color: #1a2332;
            selection-background-color: #d4560a;
            selection-color: #ffffff;
            border: 1px solid #c8d4de; outline: 0px;
        }
        QComboBox QAbstractItemView::item {
            background-color: #ffffff; color: #1a2332;
            padding: 6px 12px; min-height: 28px;
        }
        QComboBox QAbstractItemView::item:hover {
            background-color: #f0f4f8; color: #1a2332;
        }
        QComboBox QAbstractItemView::item:selected {
            background-color: #d4560a; color: #ffffff;
        }
        QLineEdit {
            background-color: #ffffff; color: #1a2332;
            border: 1px solid #c8d4de; border-radius: 4px;
            padding: 4px 8px; min-height: 26px;
        }
        QLineEdit:focus { border-color: #d4560a; }
        QTableWidget { gridline-color: #e8edf2; }
        QHeaderView::section {
            background-color: #f0f4f8; color: #1a2332;
            font-weight: 600; padding: 6px;
            border: none; border-bottom: 2px solid #c8d4de;
        }
    """)

    # Inicializar BD
    try:
        inicializar_bd()
    except Exception as e:
        QMessageBox.critical(None, "Erro", f"Erro na base de dados:\n{e}")
        sys.exit(1)

    # Forçar reload do dao
    import modules.dao as dao
    importlib.reload(dao)

    # Configuração inicial — só na primeira vez
    # Verificar licença
    if not verificar_licenca_arranque(app):
        sys.exit(0)

    from modules.configuracao import oficina_configurada, ConfiguracaoInicialDialog
    if not oficina_configurada():
        print("[CONFIG] Primeira execução — a mostrar wizard...")
        cfg = ConfiguracaoInicialDialog()
        if cfg.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)

    from modules.login import LoginDialog
    from modules.main_window import MainWindow

    while True:
        # Login
        dlg = LoginDialog()
        if dlg.exec() != QDialog.DialogCode.Accepted:
            break

        utilizador = dlg.utilizador

        # Janela principal
        win = MainWindow(utilizador)
        win.show()
        app.exec()

        # Se fechou por logout volta ao login, se fechou normalmente sai
        if not getattr(win, "logout_signal", False):
            break

    sys.exit(0)

if __name__ == "__main__":
    main()
