"""DAO — métodos de acesso à base de dados para todos os módulos"""
import hashlib
from db.database import get_connection

def _conn():
    return get_connection()

def _hash(p): return hashlib.sha256(p.encode()).hexdigest()

# ── Clientes ──────────────────────────────────────────────────────────────────
def listar_clientes(filtro=""):
    conn=_conn(); cur=conn.cursor(dictionary=True)
    f=f"%{filtro}%"
    cur.execute("SELECT * FROM clientes WHERE nome LIKE %s OR nif LIKE %s ORDER BY nome",(f,f))
    r=cur.fetchall(); cur.close(); conn.close(); return r

def get_cliente(cid):
    conn=_conn(); cur=conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM clientes WHERE id=%s",(cid,))
    r=cur.fetchone(); cur.close(); conn.close(); return r

def salvar_cliente(d):
    conn=_conn(); cur=conn.cursor()
    if d.get("id"):
        cur.execute("UPDATE clientes SET nome=%s,nif=%s,morada=%s,localidade=%s,cp=%s,telefone=%s,telemovel=%s,email=%s,notas=%s WHERE id=%s",
            (d["nome"],d.get("nif",""),d.get("morada",""),d.get("localidade",""),d.get("cp",""),
             d.get("telefone",""),d.get("telemovel",""),d.get("email",""),d.get("notas",""),d["id"]))
    else:
        cur.execute("INSERT INTO clientes (nome,nif,morada,localidade,cp,telefone,telemovel,email,notas) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (d["nome"],d.get("nif",""),d.get("morada",""),d.get("localidade",""),d.get("cp",""),
             d.get("telefone",""),d.get("telemovel",""),d.get("email",""),d.get("notas","")))
    conn.commit(); cur.close(); conn.close()

def eliminar_cliente(cid):
    conn=_conn(); cur=conn.cursor()
    cur.execute("DELETE FROM clientes WHERE id=%s",(cid,))
    conn.commit(); cur.close(); conn.close()

# ── Stock ─────────────────────────────────────────────────────────────────────
def listar_stock(filtro="", baixo_stock=False):
    conn=_conn(); cur=conn.cursor(dictionary=True)
    sql="SELECT s.*,c.nome AS categoria_nome FROM stock s LEFT JOIN stock_categorias c ON s.categoria_id=c.id WHERE 1=1"
    p=[]
    if filtro: sql+=" AND (s.referencia LIKE %s OR s.nome LIKE %s)"; f=f"%{filtro}%"; p+=[f,f]
    if baixo_stock: sql+=" AND s.quantidade<=s.stock_minimo"
    sql+=" ORDER BY s.nome"
    cur.execute(sql,p); r=cur.fetchall(); cur.close(); conn.close(); return r

def get_stock(sid):
    conn=_conn(); cur=conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM stock WHERE id=%s",(sid,))
    r=cur.fetchone(); cur.close(); conn.close(); return r

def salvar_stock(d):
    conn=_conn(); cur=conn.cursor()
    if d.get("id"):
        cur.execute("UPDATE stock SET referencia=%s,nome=%s,categoria_id=%s,unidade=%s,quantidade=%s,stock_minimo=%s,preco_custo=%s,preco_venda=%s,fornecedor=%s,localizacao=%s,notas=%s WHERE id=%s",
            (d["referencia"],d["nome"],d.get("categoria_id"),d.get("unidade","un"),d.get("quantidade",0),
             d.get("stock_minimo",0),d.get("preco_custo",0),d.get("preco_venda",0),
             d.get("fornecedor",""),d.get("localizacao",""),d.get("notas",""),d["id"]))
    else:
        cur.execute("INSERT INTO stock (referencia,nome,categoria_id,unidade,quantidade,stock_minimo,preco_custo,preco_venda,fornecedor,localizacao,notas) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (d["referencia"],d["nome"],d.get("categoria_id"),d.get("unidade","un"),d.get("quantidade",0),
             d.get("stock_minimo",0),d.get("preco_custo",0),d.get("preco_venda",0),
             d.get("fornecedor",""),d.get("localizacao",""),d.get("notas","")))
    conn.commit(); cur.close(); conn.close()

def mover_stock(stock_id, tipo, qtd, motivo="", obra_id=None, user_id=None, criar_financeiro=True):
    conn=_conn(); cur=conn.cursor()
    delta = qtd if tipo=="entrada" else -qtd
    cur.execute("UPDATE stock SET quantidade=quantidade+%s WHERE id=%s",(delta,stock_id))
    cur.execute("INSERT INTO stock_movimentos (stock_id,tipo,quantidade,motivo,obra_id,utilizador_id) VALUES(%s,%s,%s,%s,%s,%s)",
        (stock_id,tipo,qtd,motivo,obra_id,user_id))
    conn.commit(); cur.close(); conn.close()

def listar_categorias_stock():
    conn=_conn(); cur=conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM stock_categorias ORDER BY nome")
    r=cur.fetchall(); cur.close(); conn.close(); return r

# ── Obras ─────────────────────────────────────────────────────────────────────
def listar_obras(filtro="", estado=None):
    conn=_conn(); cur=conn.cursor(dictionary=True)
    sql="SELECT o.*,c.nome AS cliente_nome FROM obras o LEFT JOIN clientes c ON o.cliente_id=c.id WHERE 1=1"
    p=[]
    if filtro: sql+=" AND (o.numero LIKE %s OR o.descricao LIKE %s OR c.nome LIKE %s)"; f=f"%{filtro}%"; p+=[f,f,f]
    if estado: sql+=" AND o.estado=%s"; p.append(estado)
    sql+=" ORDER BY o.criado_em DESC"
    cur.execute(sql,p); r=cur.fetchall(); cur.close(); conn.close(); return r

def get_obra(oid):
    conn=_conn(); cur=conn.cursor(dictionary=True)
    cur.execute("SELECT o.*,c.nome AS cliente_nome FROM obras o LEFT JOIN clientes c ON o.cliente_id=c.id WHERE o.id=%s",(oid,))
    r=cur.fetchone(); cur.close(); conn.close(); return r

def proximo_numero_obra():
    from datetime import date
    conn=_conn(); cur=conn.cursor()
    cur.execute("SELECT COUNT(*)+1 AS n FROM obras"); n=cur.fetchone()[0]
    cur.close(); conn.close()
    return f"OBR-{date.today().year}-{n:04d}"

def salvar_obra(d):
    conn=_conn(); cur=conn.cursor()
    if d.get("id"):
        cur.execute("UPDATE obras SET numero=%s,cliente_id=%s,descricao=%s,morada_obra=%s,estado=%s,prioridade=%s,data_entrada=%s,data_prevista=%s,valor_orcamento=%s,valor_faturado=%s,valor_pago=%s,notas=%s WHERE id=%s",
            (d["numero"],d.get("cliente_id"),d.get("descricao",""),d.get("morada_obra",""),
             d.get("estado","orcamento"),d.get("prioridade","normal"),d.get("data_entrada"),
             d.get("data_prevista"),d.get("valor_orcamento",0),d.get("valor_faturado",0),d.get("valor_pago",0),d.get("notas",""),d["id"]))
        oid=d["id"]
    else:
        cur.execute("INSERT INTO obras (numero,cliente_id,descricao,morada_obra,estado,prioridade,data_entrada,data_prevista,valor_orcamento,notas,criado_por) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (d["numero"],d.get("cliente_id"),d.get("descricao",""),d.get("morada_obra",""),
             d.get("estado","orcamento"),d.get("prioridade","normal"),d.get("data_entrada"),
             d.get("data_prevista"),d.get("valor_orcamento",0),d.get("notas",""),d.get("criado_por")))
        oid=cur.lastrowid
    conn.commit(); cur.close(); conn.close(); return oid

def eliminar_obra(oid):
    conn=_conn(); cur=conn.cursor()
    cur.execute("DELETE FROM obras WHERE id=%s",(oid,))
    conn.commit(); cur.close(); conn.close()

# ── Financeiro ────────────────────────────────────────────────────────────────
def listar_financeiro(filtro="", tipo=None, obra_id=None):
    conn=_conn(); cur=conn.cursor(dictionary=True)
    sql="SELECT f.*,o.numero AS obra_numero FROM financeiro f LEFT JOIN obras o ON f.obra_id=o.id WHERE 1=1"
    p=[]
    if filtro: sql+=" AND f.descricao LIKE %s"; p.append(f"%{filtro}%")
    if tipo: sql+=" AND f.tipo=%s"; p.append(tipo)
    if obra_id: sql+=" AND f.obra_id=%s"; p.append(obra_id)
    sql+=" ORDER BY f.data DESC"
    cur.execute(sql,p); r=cur.fetchall(); cur.close(); conn.close(); return r

def resumo_financeiro():
    conn=_conn(); cur=conn.cursor(dictionary=True)
    cur.execute("SELECT SUM(CASE WHEN tipo='receita' THEN valor ELSE 0 END) AS receitas, SUM(CASE WHEN tipo='despesa' THEN valor ELSE 0 END) AS despesas FROM financeiro")
    r=cur.fetchone(); cur.close(); conn.close()
    rec=float(r["receitas"] or 0); des=float(r["despesas"] or 0)
    return {"receitas":rec,"despesas":des,"saldo":rec-des}

def salvar_financeiro(d):
    conn=_conn(); cur=conn.cursor()
    if d.get("id"):
        cur.execute("UPDATE financeiro SET tipo=%s,categoria=%s,descricao=%s,valor=%s,data=%s,obra_id=%s,documento=%s,pago=%s,notas=%s WHERE id=%s",
            (d["tipo"],d.get("categoria",""),d["descricao"],d["valor"],d["data"],
             d.get("obra_id"),d.get("documento",""),d.get("pago",0),d.get("notas",""),d["id"]))
    else:
        cur.execute("INSERT INTO financeiro (tipo,categoria,descricao,valor,data,obra_id,documento,pago,notas) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (d["tipo"],d.get("categoria",""),d["descricao"],d["valor"],d["data"],
             d.get("obra_id"),d.get("documento",""),d.get("pago",0),d.get("notas","")))
    # Actualizar valor_pago e valor_faturado na obra automaticamente
    if d.get("obra_id"):
        cur.execute("""UPDATE obras SET
            valor_pago=(SELECT COALESCE(SUM(valor),0) FROM financeiro WHERE obra_id=%s AND tipo='receita'),
            valor_faturado=(SELECT COALESCE(SUM(valor),0) FROM financeiro WHERE obra_id=%s AND tipo='receita')
            WHERE id=%s""", (d["obra_id"], d["obra_id"], d["obra_id"]))
        # Se valor recebido >= orçamento, marcar obra como concluída
        cur.execute("""UPDATE obras SET estado='concluida'
            WHERE id=%s AND valor_orcamento>0
            AND valor_pago>=valor_orcamento
            AND estado NOT IN ('cancelada')""", (d["obra_id"],))
    conn.commit(); cur.close(); conn.close()

# ── Tarefas ───────────────────────────────────────────────────────────────────
def listar_tarefas(estado=None):
    conn=_conn(); cur=conn.cursor(dictionary=True)
    sql="SELECT t.*,u.nome AS atribuido_nome,o.numero AS obra_numero FROM tarefas t LEFT JOIN utilizadores u ON t.atribuido_a=u.id LEFT JOIN obras o ON t.obra_id=o.id WHERE 1=1"
    p=[]
    if estado: sql+=" AND t.estado=%s"; p.append(estado)
    sql+=" ORDER BY FIELD(t.prioridade,'urgente','alta','media','baixa'),t.data_limite"
    cur.execute(sql,p); r=cur.fetchall(); cur.close(); conn.close(); return r

def salvar_tarefa(d):
    conn=_conn(); cur=conn.cursor()
    if d.get("id"):
        cur.execute("UPDATE tarefas SET titulo=%s,descricao=%s,categoria=%s,prioridade=%s,estado=%s,atribuido_a=%s,obra_id=%s,data_limite=%s WHERE id=%s",
            (d["titulo"],d.get("descricao",""),d.get("categoria",""),d.get("prioridade","media"),
             d.get("estado","pendente"),d.get("atribuido_a"),d.get("obra_id"),d.get("data_limite"),d["id"]))
    else:
        cur.execute("INSERT INTO tarefas (titulo,descricao,categoria,prioridade,estado,atribuido_a,obra_id,data_limite,criado_por) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (d["titulo"],d.get("descricao",""),d.get("categoria",""),d.get("prioridade","media"),
             d.get("estado","pendente"),d.get("atribuido_a"),d.get("obra_id"),d.get("data_limite"),d.get("criado_por")))
    conn.commit(); cur.close(); conn.close()

def concluir_tarefa(tid):
    from datetime import datetime
    conn=_conn(); cur=conn.cursor()
    cur.execute("UPDATE tarefas SET estado='concluida',concluido_em=%s WHERE id=%s",(datetime.now(),tid))
    conn.commit(); cur.close(); conn.close()

# ── Sobras ────────────────────────────────────────────────────────────────────
def listar_sobras(aproveitavel=None):
    conn=_conn(); cur=conn.cursor(dictionary=True)
    sql="SELECT sb.*,s.nome AS material,s.referencia,o.numero AS obra_numero FROM sobras sb JOIN stock s ON sb.stock_id=s.id LEFT JOIN obras o ON sb.obra_id=o.id WHERE 1=1"
    p=[]
    if aproveitavel is not None: sql+=" AND sb.aproveitavel=%s"; p.append(aproveitavel)
    sql+=" ORDER BY sb.criado_em DESC"
    cur.execute(sql,p); r=cur.fetchall(); cur.close(); conn.close(); return r

def salvar_sobra(d):
    conn=_conn(); cur=conn.cursor()
    if d.get("id"):
        cur.execute("UPDATE sobras SET stock_id=%s,obra_id=%s,descricao=%s,comprimento_mm=%s,quantidade=%s,unidade=%s,aproveitavel=%s,localizacao=%s WHERE id=%s",
            (d["stock_id"],d.get("obra_id"),d.get("descricao",""),d.get("comprimento_mm",0),
             d.get("quantidade",1),d.get("unidade","un"),d.get("aproveitavel",1),d.get("localizacao",""),d["id"]))
    else:
        cur.execute("INSERT INTO sobras (stock_id,obra_id,descricao,comprimento_mm,quantidade,unidade,aproveitavel,localizacao) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
            (d["stock_id"],d.get("obra_id"),d.get("descricao",""),d.get("comprimento_mm",0),
             d.get("quantidade",1),d.get("unidade","un"),d.get("aproveitavel",1),d.get("localizacao","")))
    conn.commit(); cur.close(); conn.close()

# ── Funcionários ──────────────────────────────────────────────────────────────
def listar_funcionarios():
    conn=_conn(); cur=conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM funcionarios WHERE ativo=1 ORDER BY nome")
    r=cur.fetchall(); cur.close(); conn.close(); return r

def salvar_funcionario(d):
    conn=_conn(); cur=conn.cursor()
    if d.get("id"):
        cur.execute("UPDATE funcionarios SET nome=%s,funcao=%s,telefone=%s,email=%s,nif=%s,data_entrada=%s,salario=%s,notas=%s WHERE id=%s",
            (d["nome"],d.get("funcao",""),d.get("telefone",""),d.get("email",""),d.get("nif",""),
             d.get("data_entrada"),d.get("salario",0),d.get("notas",""),d["id"]))
    else:
        cur.execute("INSERT INTO funcionarios (nome,funcao,telefone,email,nif,data_entrada,salario,notas) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
            (d["nome"],d.get("funcao",""),d.get("telefone",""),d.get("email",""),d.get("nif",""),
             d.get("data_entrada"),d.get("salario",0),d.get("notas","")))
    conn.commit(); cur.close(); conn.close()

def listar_utilizadores():
    conn=_conn(); cur=conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM utilizadores ORDER BY nome")
    r=cur.fetchall(); cur.close(); conn.close(); return r

# ── Dashboard stats ───────────────────────────────────────────────────────────
def stats_dashboard():
    conn=_conn(); cur=conn.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) AS n FROM obras WHERE estado IN ('confirmada','em_producao','em_montagem')"); obras_ativas=cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) AS n FROM obras WHERE prioridade='urgente' AND estado NOT IN ('concluida','cancelada')"); urgentes=cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) AS n FROM tarefas WHERE estado='pendente'"); tarefas=cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) AS n FROM stock WHERE quantidade<=stock_minimo"); stock_baixo=cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) AS n FROM obras WHERE MONTH(criado_em)=MONTH(CURDATE()) AND YEAR(criado_em)=YEAR(CURDATE())"); obras_mes=cur.fetchone()["n"]
    cur.execute("SELECT SUM(CASE WHEN tipo='receita' THEN valor ELSE 0 END) AS rec, SUM(CASE WHEN tipo='despesa' THEN valor ELSE 0 END) AS des FROM financeiro"); fin=cur.fetchone()
    cur.close(); conn.close()
    rec=float(fin["rec"] or 0); des=float(fin["des"] or 0)
    return {"obras_ativas":obras_ativas,"obras_urgentes":urgentes,"tarefas_pendentes":tarefas,
            "stock_baixo":stock_baixo,"obras_mes":obras_mes,"saldo":rec-des,"receitas":rec,"despesas":des}

# ── Fases de obra ─────────────────────────────────────────────────────────────
def criar_fases_obra(obra_id):
    conn=_conn(); cur=conn.cursor()
    fases=["corte","furacao","montagem","ferragens","vidro","acabamento","embalagem"]
    for f in fases:
        cur.execute("INSERT IGNORE INTO producao_fases (obra_item_id, fase) SELECT id, %s FROM obra_itens WHERE obra_id=%s",(f, obra_id))
    conn.commit(); cur.close(); conn.close()

def listar_fases_obra(obra_id):
    conn=_conn(); cur=conn.cursor(dictionary=True)
    cur.execute("""SELECT pf.*, oi.descricao AS item_desc,
                   u.nome AS operador_nome, u.nome AS funcionario_nome
                   FROM producao_fases pf
                   JOIN obra_itens oi ON pf.obra_item_id=oi.id
                   LEFT JOIN utilizadores u ON pf.funcionario_id=u.id
                   WHERE oi.obra_id=%s ORDER BY pf.id""",(obra_id,))
    r=cur.fetchall(); cur.close(); conn.close(); return r

def fases_diretas_obra(obra_id):
    """Fases sem depender de obra_itens — usa fases standard da obra"""
    FASES_STD=["corte","furação","montagem","vidro","acabamento","instalacao","revisao","entrega"]
    conn=_conn(); cur=conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM obras WHERE id=%s",(obra_id,))
    obra=cur.fetchone()
    if not obra: cur.close(); conn.close(); return []
    # Verificar se há fases em obra_itens
    cur.execute("SELECT COUNT(*) AS n FROM obra_itens WHERE obra_id=%s",(obra_id,))
    tem_itens=cur.fetchone()["n"]>0
    if tem_itens:
        cur.execute("""SELECT pf.id, pf.fase, pf.estado, pf.funcionario_id,
                       u.nome AS operador_nome
                       FROM producao_fases pf
                       JOIN obra_itens oi ON pf.obra_item_id=oi.id
                       LEFT JOIN utilizadores u ON pf.funcionario_id=u.id
                       WHERE oi.obra_id=%s
                       GROUP BY pf.fase ORDER BY FIELD(pf.fase,'corte','furacao','montagem','vidro','acabamento','instalacao','revisao','entrega')""",(obra_id,))
        r=cur.fetchall()
    else:
        # Criar fases virtuais baseadas nos estados standard
        r=[{"id":None,"fase":f,"estado":"pendente","operador_nome":None} for f in FASES_STD]
    cur.close(); conn.close(); return r

def atualizar_fase(fase_id, estado, funcionario_id=None):
    from datetime import datetime
    conn=_conn(); cur=conn.cursor()
    if estado=="em_curso":
        cur.execute("UPDATE producao_fases SET estado=%s,funcionario_id=%s,inicio_em=%s WHERE id=%s",
            (estado,funcionario_id,datetime.now(),fase_id))
    elif estado=="concluido":
        cur.execute("UPDATE producao_fases SET estado=%s,fim_em=%s WHERE id=%s",
            (estado,datetime.now(),fase_id))
    else:
        cur.execute("UPDATE producao_fases SET estado=%s WHERE id=%s",(estado,fase_id))
    conn.commit(); cur.close(); conn.close()

# ── Utilizadores ──────────────────────────────────────────────────────────────
def salvar_utilizador(d):
    conn=_conn(); cur=conn.cursor()
    if d.get("id"):
        if d.get("password"):
            cur.execute("UPDATE utilizadores SET nome=%s,username=%s,password_hash=%s,perfil=%s,ativo=%s WHERE id=%s",
                (d["nome"],d["username"],_hash(d["password"]),d.get("perfil","producao"),d.get("ativo",1),d["id"]))
        else:
            cur.execute("UPDATE utilizadores SET nome=%s,username=%s,perfil=%s,ativo=%s WHERE id=%s",
                (d["nome"],d["username"],d.get("perfil","producao"),d.get("ativo",1),d["id"]))
        uid=d["id"]
    else:
        cur.execute("INSERT INTO utilizadores (nome,username,password_hash,perfil) VALUES(%s,%s,%s,%s)",
            (d["nome"],d["username"],_hash(d.get("password","changeme")),d.get("perfil","producao")))
        uid=cur.lastrowid
    conn.commit(); cur.close(); conn.close()
    return uid

# ── Execute genérico ──────────────────────────────────────────────────────────
def execute(sql, params=None):
    conn=_conn(); cur=conn.cursor()
    cur.execute(sql, params or ())
    conn.commit(); lid=cur.lastrowid
    cur.close(); conn.close(); return lid

def fetchone(sql, params=None):
    conn=_conn(); cur=conn.cursor(dictionary=True)
    cur.execute(sql, params or ())
    r=cur.fetchone(); cur.close(); conn.close(); return r

def fetchall(sql, params=None):
    conn=_conn(); cur=conn.cursor(dictionary=True)
    cur.execute(sql, params or ())
    r=cur.fetchall(); cur.close(); conn.close(); return r

# ── Movimento de stock com registo financeiro automático ──────────────────────
def mover_stock_completo(stock_id, tipo, qtd, motivo="", obra_id=None, user_id=None):
    from datetime import date
    # 1. buscar material
    item = fetchone("SELECT * FROM stock WHERE id=%s", (stock_id,))
    if not item: raise Exception("Material não encontrado.")

    # 2. actualizar quantidade
    delta = qtd if tipo == "entrada" else -qtd
    execute("UPDATE stock SET quantidade=quantidade+%s WHERE id=%s", (delta, stock_id))

    # 3. registar movimento
    execute("INSERT INTO stock_movimentos (stock_id,tipo,quantidade,motivo,obra_id,utilizador_id) VALUES(%s,%s,%s,%s,%s,%s)",
        (stock_id, tipo, qtd, motivo, obra_id, user_id))

    # 4. registo financeiro automático
    if tipo == "entrada":
        valor = float(item.get("preco_custo") or 0) * float(qtd)
        if valor > 0:
            desc = f"Compra stock: {item['nome']} ({qtd} {item['unidade']})"
            if motivo: desc += f" — {motivo}"
            execute("INSERT INTO financeiro (tipo,categoria,descricao,valor,data,obra_id,pago) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                ("despesa", "Material", desc, valor, str(date.today()), obra_id, 1))

    elif tipo == "saida":
        valor = float(item.get("preco_venda") or 0) * float(qtd)
        if valor > 0:
            desc = f"Saída stock: {item['nome']} ({qtd} {item['unidade']})"
            if motivo: desc += f" — {motivo}"
            execute("INSERT INTO financeiro (tipo,categoria,descricao,valor,data,obra_id,pago) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                ("receita", "Material", desc, valor, str(date.today()), obra_id, 1))
