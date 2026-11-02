# AluminioManager — Guia de Instalação

## Requisitos
- Python 3.10 ou superior
- MySQL Server 8.0+ (instalado localmente)
- Windows 10/11 ou Linux

---

## 1. Instalar Python
Descarregar em https://www.python.org/downloads/
✅ Marcar "Add Python to PATH" durante a instalação

## 2. Instalar MySQL Server
Descarregar em https://dev.mysql.com/downloads/mysql/
Durante a instalação criar utilizador root com palavra-passe.

## 3. Criar utilizador MySQL para a aplicação
Abrir MySQL Workbench ou terminal MySQL e executar:

```sql
CREATE USER 'aluminio_user'@'localhost' IDENTIFIED BY 'aluminio_pass';
GRANT ALL PRIVILEGES ON aluminio_manager.* TO 'aluminio_user'@'localhost';
FLUSH PRIVILEGES;
```

## 4. Instalar dependências Python
Abrir terminal/cmd na pasta do programa e executar:

```
pip install -r requirements.txt
```

## 5. Iniciar o programa
```
python main.py
```
Na primeira execução, o programa cria automaticamente a base de dados e todas as tabelas.

## 6. Primeira execução
O programa não traz contas pré-definidas. Ao abrir pela primeira vez, pede os dados da
empresa e a conta de administrador que quiseres criar.

---

## Configurar credenciais MySQL
Se usar credenciais diferentes, editar o ficheiro `database.py`:

```python
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "aluminio_user",      # ← alterar
    "password": "aluminio_pass",   # ← alterar
    "database": "aluminio_manager",
}
```

## Multi-posto (vários computadores)
1. Instalar MySQL apenas num PC (servidor)
2. Nos restantes PCs, alterar o `host` em `database.py` para o IP do servidor
3. Garantir que a porta 3306 está acessível na rede local

---

## Módulos incluídos
- ⊞ **Dashboard** — Visão geral da oficina
- 🔨 **Obras** — Gestão completa de encomendas com fases de produção
- 👥 **Clientes** — Base de dados de clientes
- 📦 **Stock** — Inventário de perfis, vidros e acessórios
- 💶 **Financeiro** — Receitas e despesas
- ✓ **Tarefas** — Agenda e tarefas da equipa
- ♻️ **Sobras** — Controlo de desperdícios e reutilizáveis
- 👷 **Funcionários** — Gestão da equipa
- 📊 **Relatórios** — Impressão e exportação HTML
