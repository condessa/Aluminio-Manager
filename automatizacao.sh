#!/bin/bash

echo "Criar ambiente virtual..."
python3 -m venv venv

echo "Ativar ambiente..."
source venv/bin/activate

echo "Instalar dependências..."
pip install -r requirements.txt

echo "Iniciar aplicação..."
python main.py
