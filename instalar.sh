#!/bin/bash
echo "🔧 A instalar AluminioManager..."

# Instalar dependências do sistema
sudo apt update
sudo apt install -y mariadb-server mariadb-client python3 python3-pip python3-venv

# Iniciar MariaDB
sudo systemctl start mariadb
sudo systemctl enable mariadb

# Criar base de dados
sudo mysql -e "CREATE DATABASE IF NOT EXISTS aluminio_manager CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mysql -e "CREATE USER IF NOT EXISTS 'aluminio_user'@'localhost' IDENTIFIED BY 'aluminio_pass';"
sudo mysql -e "GRANT ALL PRIVILEGES ON aluminio_manager.* TO 'aluminio_user'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"

# Criar venv e instalar dependências Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo ""
echo "✅ Instalação concluída!"
echo "   Para iniciar: source venv/bin/activate && python3 main.py"
