"""AluminioManager — Ligação MySQL e schema"""
import mysql.connector
from mysql.connector import Error
import hashlib, json
from datetime import datetime

DEFAULT_CONFIG = {"host":"localhost","port":3306,"database":"aluminio_manager","user":"aluminio_user","password":"aluminio_pass"}
CONFIG_FILE = "db_config.json"

def load_config():
    try:
        with open(CONFIG_FILE) as f: return json.load(f)
    except: return DEFAULT_CONFIG.copy()

def save_config(cfg):
    with open(CONFIG_FILE,"w") as f: json.dump(cfg,f,indent=2)

def get_connection():
    cfg = load_config()
    return mysql.connector.connect(host=cfg["host"],port=cfg["port"],database=cfg["database"],
        user=cfg["user"],password=cfg["password"],charset="utf8mb4",collation="utf8mb4_unicode_ci",autocommit=False)

def test_connection(cfg):
    try:
        c = mysql.connector.connect(host=cfg["host"],port=cfg["port"],user=cfg["user"],
            password=cfg["password"],charset="utf8mb4",connection_timeout=5)
        c.close(); return True,"Ligação bem-sucedida!"
    except Error as e: return False,str(e)

def hash_password(pwd): return hashlib.sha256(pwd.encode()).hexdigest()

SCHEMA_SQL = """
CREATE DATABASE IF NOT EXISTS `aluminio_manager` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `aluminio_manager`;
CREATE TABLE IF NOT EXISTS utilizadores (id INT AUTO_INCREMENT PRIMARY KEY, nome VARCHAR(120) NOT NULL, username VARCHAR(60) NOT NULL UNIQUE, password_hash VARCHAR(64) NOT NULL, perfil ENUM('admin','gestor','producao','vendas') DEFAULT 'producao', ativo TINYINT(1) DEFAULT 1, criado_em DATETIME DEFAULT CURRENT_TIMESTAMP) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS oficina (id INT AUTO_INCREMENT PRIMARY KEY, chave VARCHAR(80) NOT NULL UNIQUE, valor TEXT) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS clientes (id INT AUTO_INCREMENT PRIMARY KEY, nome VARCHAR(180) NOT NULL, nif VARCHAR(20), morada TEXT, localidade VARCHAR(100), cp VARCHAR(10), telefone VARCHAR(20), telemovel VARCHAR(20), email VARCHAR(120), notas TEXT, ativo TINYINT(1) DEFAULT 1, criado_em DATETIME DEFAULT CURRENT_TIMESTAMP) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS obras (id INT AUTO_INCREMENT PRIMARY KEY, numero VARCHAR(30) NOT NULL UNIQUE, cliente_id INT, descricao TEXT, morada_obra TEXT, estado ENUM('orcamento','confirmada','em_producao','em_montagem','concluida','cancelada') DEFAULT 'orcamento', prioridade ENUM('normal','urgente','critica') DEFAULT 'normal', data_entrada DATE, data_prevista DATE, data_conclusao DATE, valor_orcamento DECIMAL(10,2) DEFAULT 0, valor_faturado DECIMAL(10,2) DEFAULT 0, notas TEXT, criado_por INT, criado_em DATETIME DEFAULT CURRENT_TIMESTAMP, atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE SET NULL, FOREIGN KEY (criado_por) REFERENCES utilizadores(id) ON DELETE SET NULL) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS obra_itens (id INT AUTO_INCREMENT PRIMARY KEY, obra_id INT NOT NULL, tipo ENUM('porta','janela','marquise','porta_seccionada','gradeamento','outro') DEFAULT 'outro', descricao VARCHAR(250), largura_mm INT DEFAULT 0, altura_mm INT DEFAULT 0, quantidade INT DEFAULT 1, cor_perfil VARCHAR(60), serie_perfil VARCHAR(60), vidro VARCHAR(100), estado_item ENUM('pendente','em_corte','em_montagem','concluido') DEFAULT 'pendente', notas TEXT, FOREIGN KEY (obra_id) REFERENCES obras(id) ON DELETE CASCADE) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS producao_fases (id INT AUTO_INCREMENT PRIMARY KEY, obra_item_id INT NOT NULL, fase ENUM('corte','furacao','montagem','ferragens','vidro','acabamento','embalagem') NOT NULL, estado ENUM('pendente','em_curso','concluido') DEFAULT 'pendente', funcionario_id INT, inicio_em DATETIME, fim_em DATETIME, notas TEXT, FOREIGN KEY (obra_item_id) REFERENCES obra_itens(id) ON DELETE CASCADE, FOREIGN KEY (funcionario_id) REFERENCES utilizadores(id) ON DELETE SET NULL) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS stock_categorias (id INT AUTO_INCREMENT PRIMARY KEY, nome VARCHAR(100) NOT NULL, cor VARCHAR(20) DEFAULT '#607d8b') ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS stock (id INT AUTO_INCREMENT PRIMARY KEY, referencia VARCHAR(80) NOT NULL UNIQUE, nome VARCHAR(200) NOT NULL, categoria_id INT, unidade ENUM('un','m','m2','kg','lt','barra','rolo','caixa') DEFAULT 'un', quantidade DECIMAL(10,3) DEFAULT 0, stock_minimo DECIMAL(10,3) DEFAULT 0, preco_custo DECIMAL(10,2) DEFAULT 0, preco_venda DECIMAL(10,2) DEFAULT 0, fornecedor VARCHAR(150), localizacao VARCHAR(80), notas TEXT, ativo TINYINT(1) DEFAULT 1, atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, FOREIGN KEY (categoria_id) REFERENCES stock_categorias(id) ON DELETE SET NULL) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS stock_movimentos (id INT AUTO_INCREMENT PRIMARY KEY, stock_id INT NOT NULL, obra_id INT, tipo ENUM('entrada','saida','ajuste','sobra') NOT NULL, quantidade DECIMAL(10,3) NOT NULL, quantidade_anterior DECIMAL(10,3), motivo VARCHAR(200), utilizador_id INT, criado_em DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (stock_id) REFERENCES stock(id) ON DELETE CASCADE, FOREIGN KEY (obra_id) REFERENCES obras(id) ON DELETE SET NULL, FOREIGN KEY (utilizador_id) REFERENCES utilizadores(id) ON DELETE SET NULL) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS sobras (id INT AUTO_INCREMENT PRIMARY KEY, stock_id INT, obra_id INT, descricao VARCHAR(200), comprimento_mm INT DEFAULT 0, quantidade DECIMAL(10,3) DEFAULT 1, unidade VARCHAR(20) DEFAULT 'un', aproveitavel TINYINT(1) DEFAULT 1, localizacao VARCHAR(80), criado_em DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (stock_id) REFERENCES stock(id) ON DELETE SET NULL, FOREIGN KEY (obra_id) REFERENCES obras(id) ON DELETE SET NULL) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS financeiro (id INT AUTO_INCREMENT PRIMARY KEY, tipo ENUM('receita','despesa') NOT NULL, categoria VARCHAR(80), descricao VARCHAR(250) NOT NULL, valor DECIMAL(10,2) NOT NULL, data DATE NOT NULL, obra_id INT, documento VARCHAR(80), pago TINYINT(1) DEFAULT 0, notas TEXT, utilizador_id INT, criado_em DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (obra_id) REFERENCES obras(id) ON DELETE SET NULL, FOREIGN KEY (utilizador_id) REFERENCES utilizadores(id) ON DELETE SET NULL) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS funcionarios (id INT AUTO_INCREMENT PRIMARY KEY, nome VARCHAR(150) NOT NULL, funcao VARCHAR(80), telefone VARCHAR(20), email VARCHAR(120), nif VARCHAR(20), data_entrada DATE, salario DECIMAL(8,2) DEFAULT 0, ativo TINYINT(1) DEFAULT 1, notas TEXT, criado_em DATETIME DEFAULT CURRENT_TIMESTAMP) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS tarefas (id INT AUTO_INCREMENT PRIMARY KEY, titulo VARCHAR(250) NOT NULL, descricao TEXT, categoria VARCHAR(80), prioridade ENUM('baixa','media','alta','urgente') DEFAULT 'media', estado ENUM('pendente','em_curso','concluida','cancelada') DEFAULT 'pendente', data_limite DATE, obra_id INT, atribuido_a INT, criado_por INT, concluido_em DATETIME, criado_em DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (obra_id) REFERENCES obras(id) ON DELETE SET NULL, FOREIGN KEY (atribuido_a) REFERENCES utilizadores(id) ON DELETE SET NULL, FOREIGN KEY (criado_por) REFERENCES utilizadores(id) ON DELETE SET NULL) ENGINE=InnoDB;
INSERT IGNORE INTO utilizadores (nome,username,password_hash,perfil) VALUES ('Administrador','admin',SHA2('admin123',256),'admin');
INSERT IGNORE INTO stock_categorias (nome,cor) VALUES ('Perfis de Alumínio','#607d8b'),('Vidros','#29b6f6'),('Ferragens','#8d6e63'),('Borrachas e Vedantes','#66bb6a'),('Parafusos e Fixações','#ffa726'),('Tintas e Acabamentos','#ab47bc'),('Consumíveis','#ef5350');
INSERT IGNORE INTO oficina (chave,valor) VALUES ('nome','Alumínios'),('nif',''),('morada',''),('telefone',''),('email',''),('responsavel','');
"""

def criar_base_dados():
    cfg = load_config()
    conn = mysql.connector.connect(host=cfg["host"],port=cfg["port"],user=cfg["user"],password=cfg["password"],charset="utf8mb4")
    cursor = conn.cursor()
    for stmt in SCHEMA_SQL.strip().split(";"):
        s = stmt.strip()
        if s:
            try: cursor.execute(s); conn.commit()
            except Error as e:
                if "already exists" not in str(e).lower() and "Duplicate entry" not in str(e): print(f"[DB] {e}")
    cursor.close(); conn.close()
