# ⚙️ Aluminios Manager v2.2.3
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
- Instalador `AluminioManager-Setup-*.exe` (não precisa de XAMPP nem MySQL)

### Passos
1. Descarregar e executar o instalador `AluminioManager-Setup-*.exe`
2. Seguir o assistente de instalação (não pede administrador)
3. Executar o **AluminioManager** a partir do atalho criado

---

## 🐧 Instalação Debian/Ubuntu

### Requisitos
- Debian 12+ / Ubuntu 22.04+ (64-bit)
- Python 3.10+
- Nenhum servidor de base de dados (SQLite incluído)

### Passos
```bash
sudo dpkg -i aluminio-manager_2.2.3_amd64.deb
```

O pacote inclui as bibliotecas Python para as versões 3.10 a 3.13, por isso a instalação
funciona **sem Internet**. O ficheiro é maior (~340 MB) e pode ser copiado para USB.

A base de dados é criada automaticamente na primeira execução, em
`~/.config/aluminio-manager/aluminio.db`. Não é preciso MySQL, MariaDB nem XAMPP.

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
| **Windows 10/11** | [AluminioManager-Setup-2.2.3.exe](https://github.com/condessa/Aluminio-Manager/releases/download/v2.2.3/AluminioManager-Setup-2.2.3.exe) |
| **Debian/Ubuntu** | [aluminio-manager_2.2.3_amd64.deb](https://github.com/condessa/Aluminio-Manager/releases/download/v2.2.3/aluminio-manager_2.2.3_amd64.deb) |

---

## 🔧 Perfis de utilizador

| Perfil | Acesso |
|--------|--------|
| **Admin** | Acesso total |
| **Gestor** | Obras, Clientes, Stock, Financeiro, Relatórios |
| **Produção** | Obras, Stock, Sobras, Tarefas |
| **Vendas** | Obras, Clientes, Tarefas |

---

## 📧 Enviar pela conta Google da oficina (OAuth)

Por omissão, os orçamentos saem pela conta da aplicação. Para usarem o email da oficina:

1. Criar um projeto em <https://console.cloud.google.com> e ativar a **Gmail API**.
2. No **OAuth consent screen**, escolher *External*, modo *Testing*, e acrescentar o email da
   oficina como *test user*.
3. Em **Credentials → Create credentials → OAuth client ID → Desktop app**, descarregar o JSON
   e guardá-lo como `credentials.json` na pasta do programa (o `build_deb.sh` inclui-o no pacote).
4. Na aplicação: **Ajuda → Como configurar o Email → Ligar conta Google da oficina**.

Enquanto a aplicação estiver em modo *Testing*, a autorização expira ao fim de 7 dias (limite
da Google). Para uso permanente é preciso publicar/verificar a aplicação na Google.

## 🔑 Licença

O AluminioManager é **gratuito, sem prazo e sem chaves de ativação**.  
É software livre, distribuído nos termos da **GNU General Public License v3** — pode usar,
estudar, alterar e redistribuir, desde que as versões derivadas mantenham a mesma licença.

---

## 📧 Suporte

condessasilva@gmail.com

---

© 2026 HCsoftware — Todos os direitos reservados
