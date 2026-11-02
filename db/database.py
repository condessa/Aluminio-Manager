"""AluminioManager — base de dados SQLite.

Um único ficheiro local, sem servidor nem credenciais. A interface mantém os
nomes usados pelo resto do programa (``get_connection``, ``hash_password``…).
"""

import hashlib
import os
import sqlite3
from pathlib import Path

from .ligacao import Ligacao

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS utilizadores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    perfil TEXT NOT NULL DEFAULT 'producao',
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em TEXT DEFAULT (datetime('now','localtime')),
    telemovel TEXT,
    email TEXT,
    especialidade TEXT,
    data_admissao TEXT,
    data_nascimento TEXT,
    salario_base REAL DEFAULT 0,
    nif TEXT,
    num_seg_social TEXT,
    notas TEXT
);

CREATE TABLE IF NOT EXISTS oficina (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chave TEXT NOT NULL UNIQUE,
    valor TEXT
);

CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    nif TEXT,
    morada TEXT,
    localidade TEXT,
    cp TEXT,
    telefone TEXT,
    telemovel TEXT,
    email TEXT,
    notas TEXT,
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS obras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT NOT NULL UNIQUE,
    cliente_id INTEGER REFERENCES clientes(id) ON DELETE SET NULL,
    descricao TEXT,
    morada_obra TEXT,
    estado TEXT NOT NULL DEFAULT 'orcamento',
    prioridade TEXT NOT NULL DEFAULT 'normal',
    data_entrada TEXT,
    data_prevista TEXT,
    data_conclusao TEXT,
    valor_orcamento REAL DEFAULT 0,
    valor_faturado REAL DEFAULT 0,
    notas TEXT,
    criado_por INTEGER REFERENCES utilizadores(id) ON DELETE SET NULL,
    criado_em TEXT DEFAULT (datetime('now','localtime')),
    atualizado_em TEXT DEFAULT (datetime('now','localtime')),
    tipo_obra TEXT,
    estado_anterior TEXT,
    notificar_cliente INTEGER NOT NULL DEFAULT 0,
    valor_pago REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS obra_itens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    obra_id INTEGER NOT NULL REFERENCES obras(id) ON DELETE CASCADE,
    tipo TEXT DEFAULT 'outro',
    descricao TEXT,
    largura_mm INTEGER DEFAULT 0,
    altura_mm INTEGER DEFAULT 0,
    quantidade INTEGER DEFAULT 1,
    cor_perfil TEXT,
    serie_perfil TEXT,
    vidro TEXT,
    estado_item TEXT DEFAULT 'pendente',
    notas TEXT
);

CREATE TABLE IF NOT EXISTS producao_fases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    obra_item_id INTEGER NOT NULL REFERENCES obra_itens(id) ON DELETE CASCADE,
    fase TEXT NOT NULL,
    estado TEXT DEFAULT 'pendente',
    funcionario_id INTEGER REFERENCES utilizadores(id) ON DELETE SET NULL,
    inicio_em TEXT,
    fim_em TEXT,
    notas TEXT
);

CREATE TABLE IF NOT EXISTS stock_categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    cor TEXT DEFAULT '#607d8b'
);

CREATE TABLE IF NOT EXISTS stock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referencia TEXT NOT NULL UNIQUE,
    nome TEXT NOT NULL,
    categoria_id INTEGER REFERENCES stock_categorias(id) ON DELETE SET NULL,
    unidade TEXT DEFAULT 'un',
    quantidade REAL DEFAULT 0,
    stock_minimo REAL DEFAULT 0,
    preco_custo REAL DEFAULT 0,
    preco_venda REAL DEFAULT 0,
    fornecedor TEXT,
    localizacao TEXT,
    notas TEXT,
    ativo INTEGER NOT NULL DEFAULT 1,
    atualizado_em TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS stock_movimentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id INTEGER NOT NULL REFERENCES stock(id) ON DELETE CASCADE,
    obra_id INTEGER REFERENCES obras(id) ON DELETE SET NULL,
    tipo TEXT NOT NULL,
    quantidade REAL NOT NULL,
    quantidade_anterior REAL,
    motivo TEXT,
    utilizador_id INTEGER REFERENCES utilizadores(id) ON DELETE SET NULL,
    criado_em TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS sobras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id INTEGER REFERENCES stock(id) ON DELETE SET NULL,
    obra_id INTEGER REFERENCES obras(id) ON DELETE SET NULL,
    descricao TEXT,
    comprimento_mm INTEGER DEFAULT 0,
    quantidade REAL DEFAULT 1,
    unidade TEXT DEFAULT 'un',
    aproveitavel INTEGER DEFAULT 1,
    localizacao TEXT,
    estado TEXT DEFAULT 'reutilizavel',
    criado_em TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS financeiro (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,
    categoria TEXT,
    descricao TEXT NOT NULL,
    valor REAL NOT NULL,
    data TEXT NOT NULL,
    obra_id INTEGER REFERENCES obras(id) ON DELETE SET NULL,
    documento TEXT,
    pago INTEGER DEFAULT 0,
    notas TEXT,
    utilizador_id INTEGER REFERENCES utilizadores(id) ON DELETE SET NULL,
    criado_em TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS funcionarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    funcao TEXT,
    telefone TEXT,
    email TEXT,
    nif TEXT,
    data_entrada TEXT,
    salario REAL DEFAULT 0,
    ativo INTEGER DEFAULT 1,
    notas TEXT,
    criado_em TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS tarefas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    descricao TEXT,
    categoria TEXT,
    prioridade TEXT DEFAULT 'media',
    estado TEXT DEFAULT 'pendente',
    data_limite TEXT,
    obra_id INTEGER REFERENCES obras(id) ON DELETE SET NULL,
    atribuido_a INTEGER REFERENCES utilizadores(id) ON DELETE SET NULL,
    criado_por INTEGER REFERENCES utilizadores(id) ON DELETE SET NULL,
    concluido_em TEXT,
    criado_em TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS obra_anexos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    obra_id INTEGER NOT NULL REFERENCES obras(id) ON DELETE CASCADE,
    nome_ficheiro TEXT,
    caminho TEXT,
    tipo TEXT,
    tamanho INTEGER DEFAULT 0,
    criado_em TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS obra_historico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    obra_id INTEGER NOT NULL REFERENCES obras(id) ON DELETE CASCADE,
    utilizador_id INTEGER,
    utilizador_nome TEXT,
    acao TEXT,
    detalhe TEXT,
    criado_em TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS obra_fases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    obra_id INTEGER NOT NULL REFERENCES obras(id) ON DELETE CASCADE,
    nome TEXT,
    estado TEXT DEFAULT 'pendente',
    responsavel_id INTEGER,
    data_inicio TEXT,
    data_fim TEXT,
    notas TEXT,
    criado_em TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS fornecedores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    nif TEXT,
    telefone TEXT,
    telemovel TEXT,
    email TEXT,
    morada TEXT,
    localidade TEXT,
    cp TEXT,
    notas TEXT,
    ativo INTEGER DEFAULT 1,
    criado_em TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS stock_fornecedores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id INTEGER NOT NULL REFERENCES stock(id) ON DELETE CASCADE,
    fornecedor_id INTEGER NOT NULL REFERENCES fornecedores(id) ON DELETE CASCADE,
    referencia_fornecedor TEXT,
    preco_compra REAL DEFAULT 0,
    prazo_entrega_dias INTEGER DEFAULT 0,
    fornecedor_principal INTEGER DEFAULT 0,
    UNIQUE (stock_id, fornecedor_id)
);

CREATE TABLE IF NOT EXISTS eventos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    tipo TEXT DEFAULT 'outro',
    data TEXT NOT NULL,
    descricao TEXT,
    utilizador_id INTEGER REFERENCES utilizadores(id) ON DELETE SET NULL,
    criado_em TEXT DEFAULT (datetime('now','localtime'))
);

CREATE INDEX IF NOT EXISTS idx_obras_estado ON obras(estado);
CREATE INDEX IF NOT EXISTS idx_movimentos_stock ON stock_movimentos(stock_id);
CREATE INDEX IF NOT EXISTS idx_eventos_data ON eventos(data);

CREATE TRIGGER IF NOT EXISTS trg_obras_atualizado
AFTER UPDATE ON obras
BEGIN
    UPDATE obras SET atualizado_em = datetime('now','localtime') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_stock_atualizado
AFTER UPDATE ON stock
BEGIN
    UPDATE stock SET atualizado_em = datetime('now','localtime') WHERE id = NEW.id;
END;

INSERT OR IGNORE INTO stock_categorias (nome, cor) VALUES
    ('Perfis de Alumínio', '#607d8b'),
    ('Vidros', '#29b6f6'),
    ('Ferragens', '#8d6e63'),
    ('Borrachas e Vedantes', '#66bb6a'),
    ('Parafusos e Fixações', '#ffa726'),
    ('Tintas e Acabamentos', '#ab47bc'),
    ('Consumíveis', '#ef5350');

INSERT OR IGNORE INTO oficina (chave, valor) VALUES
    ('nome', ''), ('nif', ''), ('morada', ''), ('localidade', ''),
    ('telefone', ''), ('telemovel', ''), ('email', ''), ('responsavel', ''),
    ('iban', ''), ('smtp_host', ''), ('smtp_port', '');
"""


def pasta_config():
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return Path(base) / "aluminio-manager"


def caminho_config():
    """Ficheiro de configuração (compatibilidade com o resto do programa)."""
    return pasta_config() / "config.json"


def caminho_bd():
    escolhido = os.environ.get("ALUMINIO_DB")
    if escolhido:
        return Path(escolhido).expanduser()
    return pasta_config() / "aluminio.db"


def get_connection():
    return Ligacao(caminho_bd())


def garantir_schema():
    """Cria as tabelas (se faltarem) e aplica migrações simples."""
    caminho = caminho_bd()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(caminho))
    try:
        conn.executescript(SCHEMA_SQL)
        _migrar(conn)
        conn.commit()
    finally:
        conn.close()
    return caminho


def _migrar(conn):
    """Acrescenta colunas novas a bases de dados criadas por versões antigas."""
    novas = {
        "obras": [("estado_anterior", "TEXT"), ("valor_pago", "REAL DEFAULT 0"),
                  ("notificar_cliente", "INTEGER DEFAULT 0")],
        "clientes": [("telemovel", "TEXT")],
    }
    for tabela, colunas in novas.items():
        existentes = {linha[1] for linha in conn.execute(f"PRAGMA table_info({tabela})")}
        for nome, tipo in colunas:
            if nome not in existentes:
                conn.execute(f"ALTER TABLE {tabela} ADD COLUMN {nome} {tipo}")


def criar_base_dados(cfg=None):
    return garantir_schema()


def test_connection(*args, **kwargs):
    try:
        conn = get_connection()
        conn.execute("SELECT 1")
        conn.close()
        return True, "Ligação bem-sucedida!"
    except Exception as erro:
        return False, descrever_erro(erro)


def descrever_erro(erro):
    texto = str(erro)
    if "unable to open database file" in texto:
        return ("Não foi possível abrir o ficheiro da base de dados.\n\n"
                "Verifique as permissões da pasta e o espaço em disco.")
    if "database is locked" in texto:
        return ("A base de dados está a ser usada por outro processo.\n\n"
                "Feche outras janelas do programa e tente novamente.")
    if "no such table" in texto:
        return "A base de dados parece incompleta. Execute o programa novamente para a reparar."
    return texto


def pasta_certificado():
    """Pasta persistente para o certificado da empresa."""
    pasta = pasta_config() / "cert"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()
