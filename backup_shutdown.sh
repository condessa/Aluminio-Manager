#!/bin/bash
cd "/home/herculano/Programas/Aluminio-Manager"
source venv/bin/activate 2>/dev/null || true
python3 -c "from modules.backup_manager import fazer_backup; fazer_backup()"
