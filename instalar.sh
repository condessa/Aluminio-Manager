#!/bin/bash
echo "🔧 A instalar AluminioManager..."

sudo apt update
sudo apt install -y python3 python3-pip python3-venv

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo ""
echo "✅ Instalação concluída!"
echo "   Para iniciar: source venv/bin/activate && python3 main.py"
echo "   A base de dados é criada automaticamente em ~/.config/aluminio-manager/aluminio.db"
