# Estudo — migração do MySQL/MariaDB para SQLite

**Data:** 2026-11-02 · **Versão em análise:** 1.5.8

## 1. Porquê

Hoje o Alumínio Manager obriga a ter um servidor MySQL/MariaDB instalado e configurado.
Para uma oficina sem técnico de informática isso é o maior obstáculo de instalação:
XAMPP, utilizador, palavra-passe, porta, firewall. Foi a origem de quase todos os erros
reportados (1045, 2003, «não encontrou o mysql.exe»).

O HC-Gestão Stocks já usa SQLite e nunca deu este tipo de problema. O objetivo é o mesmo:
**instalar e usar, sem servidor e sem configuração**.

## 2. O que existe hoje (inventário real)

| Item | Número |
|---|---|
| Ficheiros com SQL | 11 |
| Marcadores `%s` (estilo mysql-connector) | 403 |
| Cursores `dictionary=True` | 38 |
| `conn.commit()` | 33 |
| `AUTO_INCREMENT` / `ENUM` no schema | 19 / 15 |
| `CURDATE`, `YEAR`, `MONTH` em consultas | 2, 3, 3 |
| `ON DUPLICATE KEY UPDATE` | 2 |
| `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` | 15+ |

Conclusão: a maioria das 403 consultas é SQL simples e portável. O trabalho está
concentrado em **placeholders**, **cursores com dicionário**, **schema** e **meia dúzia
de consultas**.

## 3. Abordagens possíveis

### A. SQLite puro (recomendada para um só posto)

- Base de dados num ficheiro `aluminio_manager.db` na pasta do utilizador.
- Zero configuração, zero servidor, backup por cópia.
- **Limitação:** não serve para vários postos a trabalhar ao mesmo tempo sobre a mesma base
  num servidor (SQLite em pasta partilhada não é seguro).

### B. MySQL embutido (MariaDB portátil dentro do instalador)

- Mantém tudo o que existe e o multi-posto.
- O instalador passa a trazer um MariaDB portátil e arranca-o em segundo plano.
- **Custo:** +200–300 MB, processo extra, mais falhas possíveis (portas, antivírus),
  e continua a ser um servidor para manter.

### C. Camada de acesso agnóstica, SQLite por omissão e MySQL opcional

- Introduz uma camada fina que fala com os dois motores.
- Instalação normal: SQLite, sem servidor.
- Quem precisa de multi-posto muda a configuração para MySQL.
- **Custo:** um pouco mais de trabalho inicial, mas preserva a funcionalidade atual.

### Comparação

| Critério | A. SQLite | B. MariaDB embutido | C. Híbrido |
|---|---|---|---|
| Instalação para leigos | ★★★★★ | ★★★ | ★★★★★ |
| Tamanho do instalador | ~100 MB | ~350 MB | ~100 MB |
| Multi-posto | ✗ | ✓ | ✓ (MySQL) |
| Manutenção | ★★★★★ | ★★ | ★★★ |
| Esforço de migração | Médio | Médio | Médio-alto |

**Recomendação: C.** SQLite por omissão (resolve o problema de 95% das oficinas) e a
possibilidade de continuar em MySQL para quem já tem vários postos. A camada de
compatibilidade é o que torna as duas opções sustentáveis.

## 4. Como fazer sem reescrever 403 consultas

Criar `db/ligacao.py` com um adaptador que imita a interface atual do `mysql.connector`:

```python
class Ligacao:
    def cursor(self, dictionary=False, ...): ...
    def commit(self): ...
    def close(self): ...

class Cursor:
    def execute(self, sql, params=()):
        sql = sql.replace("%s", "?")      # tradução dos marcadores
        self._cur.execute(sql, params)
    def fetchone(self): ...               # devolve dict se dictionary=True
    def fetchall(self): ...
```

- `get_connection()` passa a devolver `Ligacao` (SQLite ou MySQL, conforme a configuração).
- Os 11 módulos e as 403 consultas **ficam como estão**.
- As ~10 consultas com `CURDATE()`, `YEAR()`, `MONTH()` e `ON DUPLICATE KEY` são revistas
  uma a uma.
- Os erros (`mysql.connector.Error`) passam a ser normalizados para uma exceção própria,
  com `errno` equivalente, para `descrever_erro()` continuar a funcionar.

## 5. Schema

Traduções necessárias:

| MySQL | SQLite |
|---|---|
| `INT AUTO_INCREMENT PRIMARY KEY` | `INTEGER PRIMARY KEY AUTOINCREMENT` |
| `ENUM('a','b')` | `TEXT CHECK (col IN ('a','b'))` |
| `DATETIME DEFAULT CURRENT_TIMESTAMP` | `TEXT DEFAULT (datetime('now','localtime'))` |
| `ON UPDATE CURRENT_TIMESTAMP` | trigger `AFTER UPDATE` |
| `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` | tabela de migrações (`PRAGMA user_version`) |
| `DECIMAL(10,2)` | `NUMERIC` (o Python trata como float/Decimal) |
| `INSERT IGNORE` | `INSERT OR IGNORE` |
| `ON DUPLICATE KEY UPDATE` | `ON CONFLICT(...) DO UPDATE SET` |
| `CURDATE()`, `YEAR(x)`, `MONTH(x)` | `date('now','localtime')`, `strftime('%Y',x)`, `strftime('%m',x)` |

Criar um sistema simples de migrações:

```python
MIGRACOES = [
    (1, "CREATE TABLE ..."),
    (2, "ALTER TABLE obras ADD COLUMN estado_anterior TEXT"),
]
```

## 6. Dados existentes

Ferramenta única `ferramentas/importar_mysql.py`:

1. liga ao MySQL antigo (config atual);
2. cria o ficheiro SQLite e o schema;
3. copia tabela a tabela, convertendo tipos (datas, decimais, NULL);
4. verifica contagens e somas por tabela;
5. guarda um relatório antes/depois.

Na aplicação: primeira execução deteta MySQL configurado e oferece «Importar dados antigos».

## 7. Backup

- SQLite: cópia do ficheiro com a API `backup()` (segura com a base aberta).
- Mantém-se a pasta `Backups/aluminio-auto` e a cópia antes de desligar.
- Exportação/restauro passam a ser um único `.db` (mais simples de enviar por email).

## 8. Multi-posto

- Omissão: SQLite local.
- Opção avançada (Definições): «Base de dados partilhada (MySQL)» com os campos atuais.
- Documentar que SQLite em pasta de rede **não** é suportado.

## 9. Fases e esforço (estimativa)

| Fase | Trabalho | Esforço |
|---|---|---|
| 0 | Camada `db/ligacao.py` + testes com os dois motores | 1 dia |
| 1 | Schema SQLite + migrações + testes | 1 dia |
| 2 | Portar consultas específicas (CURDATE, upserts, datas) | 1 dia |
| 3 | Importador MySQL → SQLite + validação com dados reais | 1–2 dias |
| 4 | Backup/restauro, Definições, deteção na primeira execução | 1 dia |
| 5 | Instalador sem MariaDB, testes em Windows/Linux, documentação | 1 dia |

**Total estimado:** 6 a 8 dias de trabalho efectivo.

Riscos principais: dados reais com tipos inesperados (mitigado pelo importador com
relatório), e clientes que usam multi-posto (mitigado pela opção MySQL).

## 10. Decisão proposta

1. Implementar a **camada de compatibilidade** e o **schema SQLite**.
2. Passar a **SQLite por omissão**; MySQL fica como opção para multi-posto.
3. Manter o instalador atual até a migração estar validada; depois o instalador deixa de
   depender de MariaDB e passa a ser um duplo clique, como o HC-Gestão Stocks.
