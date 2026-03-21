#!/bin/bash
BACKUP_DIR="$HOME/Backups/aluminio-auto"
mkdir -p "$BACKUP_DIR"
DATA=$(date +%Y%m%d-%H%M%S)
mysqldump -u aluminio_user -paluminio_pass aluminio_manager > "$BACKUP_DIR/db-$DATA.sql"
# Manter apenas os últimos 30 backups
ls -t "$BACKUP_DIR"/db-*.sql | tail -n +31 | xargs -r rm
echo "[$(date)] Backup concluído: db-$DATA.sql" >> "$BACKUP_DIR/backup.log"
