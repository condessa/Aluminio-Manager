# ⚙️ Aluminios Manager v1.3.0
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
sudo dpkg -i aluminio-manager_1.3.0_amd64.deb
```

Na primeira instalação, as bibliotecas Python são descarregadas para a versão de Python
do sistema (é preciso ligação à Internet; demora alguns minutos).

A base de dados e o utilizador MySQL são criados durante a instalação. Se a ligação
falhar, o programa mostra um botão **«Configurar automaticamente»** — pede a palavra-passe
do sistema, cria tudo e guarda a configuração, sem terminal. Os dados também podem ser
introduzidos à mão, e há comandos SQL prontos a copiar para administradores.

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
| **Debian/Ubuntu** | [aluminio-manager_1.3.0_amd64.deb](https://github.com/condessa/Aluminio-Manager/releases/download/v1.3.0/aluminio-manager_1.3.0_amd64.deb) |

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

O AluminioManager é **gratuito, sem prazo e sem chaves de ativação**.  
É software livre, distribuído nos termos da **GNU General Public License v3** — pode usar,
estudar, alterar e redistribuir, desde que as versões derivadas mantenham a mesma licença.

---

## 📧 Suporte

condessasilva@gmail.com

---

© 2026 HCsoftware — Todos os direitos reservados
