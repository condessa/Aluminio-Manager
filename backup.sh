#!/bin/bash
# Copia a base de dados SQLite para a pasta de backups.
ORIGEM="$HOME/.config/aluminio-manager/aluminio.db"
DESTINO="$HOME/Backups/aluminio"
mkdir -p "$DESTINO"
cp "$ORIGEM" "$DESTINO/db-$(date +%Y%m%d-%H%M%S).db"
echo "Backup guardado em $DESTINO"
