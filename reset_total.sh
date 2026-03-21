#!/bin/bash
echo "⚠️  RESET TOTAL DO ALUMINIOMANAGER ⚠️"
echo "Isto vai apagar TODOS os dados e configurações!"
echo
read -p "Tens a certeza? (escreve 'SIM' para confirmar): " confirmacao

if [ "$confirmacao" != "SIM" ]; then
    echo "Operação cancelada."
    exit 1
fi

echo
echo "1. Apagar base de dados MySQL..."
mysql -u aluminio_user -paluminio_pass -e "DROP DATABASE IF EXISTS aluminio_manager;" 2>/dev/null
echo "   ✓ Base de dados apagada"

echo "2. Apagar ficheiros de configuração locais..."
rm -rf ~/.config/aluminio-manager/
rm -rf ~/.local/share/aluminio-manager/
rm -f ~/Programas/Aluminio-Manager/*.json
rm -f ~/Programas/Aluminio-Manager/*.db
rm -f ~/Programas/Aluminio-Manager/.env
rm -f /tmp/aluminio*.json
echo "   ✓ Ficheiros apagados"

echo "3. Apagar cache do Python..."
find ~/Programas/Aluminio-Manager -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
echo "   ✓ Cache apagada"

echo
echo "✅ Reset total concluído!"
echo "Agora executa: cd ~/Programas/Aluminio-Manager && python main.py"
