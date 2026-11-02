"""AluminioManager — Programa principal"""
import sys
import importlib
import mysql.connector
from PyQt6.QtWidgets import QApplication, QMessageBox, QDialog
from db.database import get_connection as conectar, load_config, SCHEMA_SQL

def inicializar_bd():
    """Inicializa a base de dados - cria tudo se não existir ou estiver incompleta"""
    from db.database import criar_base_dados
    
    print("[DB] A verificar base de dados...")
    cfg = load_config()
    
    try:
        # Tenta ligar à base de dados específica
        conn = conectar()
        cursor = conn.cursor()
        
        # Verificar se as tabelas principais existem
        cursor.execute("SHOW TABLES LIKE 'utilizadores'")
        tem_utilizadores = cursor.fetchone() is not None
        
        cursor.execute("SHOW TABLES LIKE 'oficina'")
        tem_oficina = cursor.fetchone() is not None
        
        cursor.close()
        conn.close()
        
        # Se faltar alguma tabela principal, recria tudo
        if not tem_utilizadores or not tem_oficina:
            print("[DB] Base de dados incompleta. A recriar estrutura...")
            
            # Recriar a base de dados do zero
            conn = mysql.connector.connect(
                host=cfg["host"],
                port=cfg["port"],
                user=cfg["user"],
                password=cfg["password"],
                charset="utf8mb4"
            )
            cursor = conn.cursor()
            
            # Apagar e recriar a base de dados
            cursor.execute(f"DROP DATABASE IF EXISTS {cfg['database']}")
            cursor.execute(f"CREATE DATABASE {cfg['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.execute(f"USE {cfg['database']}")
            
            # Executar todo o schema
            print("[DB] A criar tabelas...")
            for stmt in SCHEMA_SQL.strip().split(";"):
                s = stmt.strip()
                if s and not s.upper().startswith('USE'):
                    try:
                        cursor.execute(s)
                        conn.commit()
                    except Exception as e:
                        print(f"[DB] Aviso: {e}")
            
            cursor.close()
            conn.close()
            print("[DB] Base de dados criada com sucesso!")
        else:
            print("[DB] Base de dados OK.")
            
    except mysql.connector.Error as e:
        # Se a base de dados não existir, cria tudo
        if "Unknown database" in str(e) or "database doesn't exist" in str(e):
            print("[DB] Base de dados não existe. A criar...")
            criar_base_dados()
        else:
            # Outro erro de ligação
            print(f"[DB] Erro de ligação: {e}")
            print("[DB] Verifique se o MySQL/MariaDB está a correr:")
            print("    sudo systemctl status mysql")
            print("    sudo systemctl start mysql")
            raise e
    except Exception as e:
        print(f"[DB] Erro inesperado: {e}")
        raise e

def _verificar_aniversarios(parent):
    from datetime import date, timedelta
    from PyQt6.QtWidgets import QMessageBox
    try:
        from modules.dao import listar_utilizadores
        hoje = date.today()
        amanha = hoje + timedelta(days=1)
        msgs_hoje = []
        msgs_amanha = []
        for f in listar_utilizadores():
            dn = f.get("data_nascimento")
            if not dn or str(dn) == "None": continue
            dn = str(dn)[:10]
            if len(dn) < 10: continue
            try:
                mes, dia = int(dn[5:7]), int(dn[8:10])
                idade = hoje.year - int(dn[:4])
                nome = f.get("nome","")
                if mes == hoje.month and dia == hoje.day:
                    msgs_hoje.append(f"🎂 <b>{nome}</b> faz hoje <b>{idade} anos</b>!")
                elif mes == amanha.month and dia == amanha.day:
                    msgs_amanha.append(f"🎂 <b>{nome}</b> faz amanhã <b>{idade} anos</b>.")
            except: continue
        if msgs_hoje or msgs_amanha:
            texto = ""
            if msgs_hoje:
                texto += "<h3 style='color:#d4560a;'>🎉 Hoje</h3>" + "<br>".join(msgs_hoje)
            if msgs_amanha:
                if texto: texto += "<br><br>"
                texto += "<h3 style='color:#1a56db;'>📅 Amanhã</h3>" + "<br>".join(msgs_amanha)
            msg = QMessageBox(parent)
            msg.setWindowTitle("🎂 Lembretes de Aniversário")
            from PyQt6.QtCore import Qt
            msg.setTextFormat(Qt.TextFormat.RichText)
            msg.setText(texto)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.exec()
    except Exception as e:
        print(f"[Aniversários] Erro: {e}")


def _migrar_estrutura():
    """Acrescenta colunas novas a bases de dados já existentes."""
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("ALTER TABLE obras ADD COLUMN IF NOT EXISTS estado_anterior VARCHAR(30) DEFAULT NULL")
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[DB] Migração: {e}")


def _tem_utilizadores():
    """True se já existe pelo menos uma conta; False numa instalação nova."""
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM utilizadores")
        total = cur.fetchone()[0]
        cur.close(); conn.close()
        return total > 0
    except Exception:
        return True


def _obter_utilizador(username):
    """Vai buscar o utilizador criado no assistente inicial."""
    try:
        conn = conectar()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM utilizadores WHERE username=%s AND ativo=1", (username,))
        user = cur.fetchone()
        cur.close(); conn.close()
        return user
    except Exception:
        return None


def main():
    # Configura backup automático silenciosamente
    try:
        from modules.backup_manager import configurar_backup_automatico
        configurar_backup_automatico()
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("Aluminios Manager by HCsoftware")
    app.setStyle("Fusion")
    app.setStyleSheet("""
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit {
            background-color: #ffffff; color: #1a2332;
            border: 1px solid #c8d4de; border-radius: 4px;
            padding: 4px 8px; min-height: 26px;
        }
        QLineEdit:focus, QTextEdit:focus, QDateEdit:focus { border-color: #d4560a; }
        QComboBox {
            background-color: #ffffff; color: #1a2332;
            border: 1px solid #c8d4de; border-radius: 4px;
            padding: 4px 8px; min-height: 26px;
        }
        QComboBox:hover { border-color: #d4560a; }
        QComboBox::drop-down { border: none; width: 20px; }
        QComboBox QAbstractItemView {
            background-color: #ffffff; color: #1a2332;
            selection-background-color: #d4560a; selection-color: #ffffff;
            border: 1px solid #c8d4de;
        }
        QTableWidget { gridline-color: #e8edf2; }
        QHeaderView::section {
            background-color: #f0f4f8; color: #1a2332;
            font-weight: 600; padding: 6px;
            border: none; border-bottom: 2px solid #c8d4de;
        }
    """)

    # Inicializar BD — se falhar, pedir os dados de ligação ao utilizador
    from modules.db_setup import DialogoBaseDados

    while True:
        try:
            inicializar_bd()
            break
        except Exception as e:
            print(f"[DB] Erro de ligação: {e}")
            dialogo = DialogoBaseDados(e)
            if dialogo.exec() != QDialog.DialogCode.Accepted:
                sys.exit(1)



    _migrar_estrutura()

    # Forçar reload do dao
    import modules.dao as dao
    importlib.reload(dao)

    # Configuração da oficina (primeira execução)
    from modules.configuracao import oficina_configurada, ConfiguracaoInicialDialog
    
    # Verificar se a oficina precisa de configuração
    # Sem contas criadas, é sempre primeira utilização — mesmo que a base de
    # dados já tenha dados da empresa de uma instalação anterior.
    precisa_config = not oficina_configurada() or not _tem_utilizadores()
    utilizador_inicial = None

    if precisa_config:
        print("[CONFIG] Primeira execução — a mostrar wizard...")
        cfg = ConfiguracaoInicialDialog()
        if cfg.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)
        # A conta foi criada agora: entrar sem pedir login outra vez.
        utilizador_inicial = getattr(cfg, "utilizador_criado", None)
        print("[CONFIG] Configuração guardada com sucesso!")
    
    from modules.login import LoginDialog
    from modules.main_window import MainWindow

    while True:
        if utilizador_inicial:
            utilizador = _obter_utilizador(utilizador_inicial)
            utilizador_inicial = None
            if utilizador is None:
                continue  # conta não encontrada: volta ao login normal
        else:
            dlg = LoginDialog()
            if dlg.exec() != QDialog.DialogCode.Accepted:
                break
            utilizador = dlg.utilizador

        # Janela principal
        win = MainWindow(utilizador)
        win.show()

        # Lembretes de aniversário
        _verificar_aniversarios(win)

        app.exec()

        # Se fechou por logout volta ao login, se fechou normalmente sai
        if not getattr(win, "logout_signal", False):
            break

    sys.exit(0)

if __name__ == "__main__":
    main()
