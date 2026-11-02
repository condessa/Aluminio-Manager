#!/usr/bin/env python3
"""Reset completo à base de dados"""
from db.database import load_config, SCHEMA_SQL
import mysql.connector

def reset_bd():
    print("\n⚠️  ATENÇÃO: Isto vai APAGAR TODOS OS DADOS!\n")
    resposta = input("Tens a certeza? (escreve 'SIM' para confirmar): ").strip()
    
    if resposta != 'SIM':
        print("Operação cancelada.")
        return
    
    cfg = load_config()
    
    try:
        # Ligar ao MySQL
        conn = mysql.connector.connect(
            host=cfg["host"],
            user=cfg["user"],
            password=cfg["password"]
        )
        cursor = conn.cursor()
        
        # Apagar base de dados se existir
        cursor.execute(f"DROP DATABASE IF EXISTS {cfg['database']}")
        print(f"✓ Base de dados {cfg['database']} apagada.")
        
        # Criar base de dados nova
        cursor.execute(f"CREATE DATABASE {cfg['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"✓ Base de dados {cfg['database']} criada.")
        
        cursor.execute(f"USE {cfg['database']}")
        
        # Criar tabelas
        print("✓ A criar tabelas...")
        for stmt in SCHEMA_SQL.strip().split(";"):
            s = stmt.strip()
            if s and not s.upper().startswith('USE') and not s.upper().startswith('CREATE DATABASE'):
                try:
                    cursor.execute(s)
                    conn.commit()
                except Exception as e:
                    print(f"  Aviso: {e}")
        
        # Verificar se as tabelas foram criadas
        cursor.execute("SHOW TABLES")
        tabelas = cursor.fetchall()
        print(f"\n✓ {len(tabelas)} tabelas criadas:")
        for tabela in tabelas:
            print(f"   - {tabela[0]}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Base de dados recriada com sucesso!")
        print("\nA conta de administrador é criada no primeiro arranque.")
        print("\n🚀 Agora executa: python main.py")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")

if __name__ == "__main__":
    reset_bd()
