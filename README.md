# ⚙️ Aluminios Manager v1.1.1
**by HCsoftware**

Sistema de gestão completo para oficinas de alumínio e caixilharia.

---

## 📋 Funcionalidades

- **Dashboard** — resumo de obras, alertas de prazo e stock baixo, gráficos de receitas/despesas
- **Obras** — gestão completa com estados, histórico, anexos e orçamentos PDF com assinatura digital
- **Clientes** — ficha completa com histórico de obras
- **Stock** — controlo de materiais com histórico de movimentos e alertas de stock mínimo
- **Fornecedores** — registo e associação a artigos de stock
- **Sobras** — gestão de material excedente
- **Funcionários** — fichas completas com especialidade, dados pessoais e aniversários
- **Financeiro** — registo de receitas e despesas com resumo mensal
- **Calendário** — visualização de obras, tarefas e eventos com lembretes de aniversário
- **Tarefas** — gestão de tarefas com prioridades e atribuição a funcionários
- **Relatórios** — relatórios HTML e PDF com gráficos
- **Exportação** — exportação para Excel e CSV em todas as listas

---

## 💻 Instalação Windows

### Requisitos
- Windows 10/11 (64-bit)
- [XAMPP](https://www.apachefriends.org) com MySQL/MariaDB

### Passos
1. Descarregar e instalar o [XAMPP](https://www.apachefriends.org)
2. Abrir o XAMPP Control Panel e iniciar o **MySQL**
3. Descarregar e executar o instalador `AluminioManager_Setup_v1.1.0.exe`
4. Seguir o assistente de instalação
5. Executar o **AluminioManager** a partir do atalho criado

---

## 🐧 Instalação Debian/Ubuntu

### Requisitos
- Debian 12+ / Ubuntu 22.04+ (64-bit)
- Python 3.10+
- MySQL 8.0+ ou MariaDB 10.6+

### Passos
```bash
sudo dpkg -i aluminio-manager_1.1.1_amd64.deb
```

A base de dados e o utilizador MySQL são criados durante a instalação. Se a ligação
falhar (por exemplo, num sistema onde o `mysql` root não está acessível), o programa
abre um assistente para indicar os dados de ligação, com os comandos SQL prontos a copiar.

Na primeira execução será apresentado um assistente de configuração para:
1. Definir os dados da empresa
2. Criar a conta de administrador
3. Configurar o email (opcional)

### Iniciar
```bash
aluminio-manager
```

---

## ⬇️ Download

| Plataforma | Ficheiro |
|------------|---------|
| **Windows 10/11** | [AluminioManager_Setup_v1.1.0.exe](https://github.com/condessa/Aluminio-Manager/releases/download/v1.1.0/AluminioManager_Setup_v1.1.0.exe) |
| **Debian/Ubuntu** | [aluminio-manager_1.1.1_amd64.deb](https://github.com/condessa/Aluminio-Manager/releases/download/v1.1.1/aluminio-manager_1.1.1_amd64.deb) |

---

## 🔧 Perfis de utilizador

| Perfil | Acesso |
|--------|--------|
| **Admin** | Acesso total |
| **Gestor** | Obras, Clientes, Stock, Financeiro, Relatórios |
| **Produção** | Obras, Stock, Sobras, Tarefas |
| **Vendas** | Obras, Clientes, Tarefas |

---

## 🔑 Licença

O AluminioManager funciona em modo de avaliação gratuita durante **30 dias**.  
Para adquirir uma licença permanente contacte:

- 📧 **Email:** condessasilva@gmail.com  
- 📱 **MBWay:** 936 203 512  

---

## 📧 Suporte

condessasilva@gmail.com

---

© 2026 HCsoftware — Todos os direitos reservados
