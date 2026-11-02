#!/bin/bash
# Configura a base de dados do AluminioManager.
#
# Corre como root (pelo postinst do pacote ou pelo botão «Configurar
# automaticamente» da aplicação, através de pkexec).
#
#   configurar_bd.sh [utilizador]
#
# Deixa a configuração em /etc/aluminio-manager/db_config.json (legível, para
# qualquer utilizador do computador) e uma cópia privada em
# ~/.config/aluminio-manager/db_config.json do utilizador indicado.
set -u

UTILIZADOR="${1:-${SUDO_USER:-}}"
CONFIG_ETC="${ALUMINIO_DB_CONFIG:-/etc/aluminio-manager/db_config.json}"

erro() { echo "ERRO: $*" >&2; exit 1; }

command -v mysql >/dev/null 2>&1 || erro "cliente MySQL/MariaDB não encontrado."

# Garantir que o servidor está a correr.
systemctl start mariadb 2>/dev/null || systemctl start mysql 2>/dev/null || \
    service mariadb start 2>/dev/null || true
sleep 1

mysql --protocol=socket -uroot -e "SELECT 1" >/dev/null 2>&1 || \
    erro "o MySQL/MariaDB não respondeu como root."

mkdir -p /etc/aluminio-manager

senha_actual() {
    [ -f "$CONFIG_ETC" ] || return 1
    python3 - "$CONFIG_ETC" <<'PY' 2>/dev/null
import json, sys
try:
    print(json.load(open(sys.argv[1])).get("password", ""))
except Exception:
    raise SystemExit(1)
PY
}

config_valida() {
    local senha
    senha="$(senha_actual)" || return 1
    [ -n "$senha" ] || return 1
    MYSQL_PWD="$senha" mysql -u aluminio_user -h localhost -e "SELECT 1" >/dev/null 2>&1
}

criar_config() {
    local senha="$1"
    python3 - "$CONFIG_ETC" "$senha" <<'PY'
import json, sys
caminho, senha = sys.argv[1], sys.argv[2]
with open(caminho, "w", encoding="utf-8") as f:
    json.dump({"host": "localhost", "port": 3306, "database": "aluminio_manager",
               "user": "aluminio_user", "password": senha}, f, indent=2, ensure_ascii=False)
PY
    chmod 644 "$CONFIG_ETC"
}

if [ -f "$CONFIG_ETC" ]; then
    chmod 644 "$CONFIG_ETC"
fi

if config_valida; then
    echo "Base de dados já configurada."
else
    echo "A criar a base de dados e o utilizador…"
    SENHA="$(head -c 32 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 24)"
    mysql --protocol=socket -uroot <<SQL || erro "não foi possível criar a base de dados."
CREATE DATABASE IF NOT EXISTS aluminio_manager CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'aluminio_user'@'localhost' IDENTIFIED BY '${SENHA}';
ALTER USER 'aluminio_user'@'localhost' IDENTIFIED BY '${SENHA}';
GRANT ALL PRIVILEGES ON aluminio_manager.* TO 'aluminio_user'@'localhost';
FLUSH PRIVILEGES;
SQL
    criar_config "$SENHA"
    config_valida || erro "a base de dados foi criada mas a ligação ainda falha."
fi

# Cópia privada no lar do utilizador que instalou / pediu a configuração.
if [ -n "$UTILIZADOR" ] && id "$UTILIZADOR" >/dev/null 2>&1; then
    CASA="$(getent passwd "$UTILIZADOR" | cut -d: -f6)"
    if [ -n "${CASA:-}" ] && [ -d "$CASA" ]; then
        DESTINO="$CASA/.config/aluminio-manager"
        mkdir -p "$DESTINO"
        cp "$CONFIG_ETC" "$DESTINO/db_config.json"
        chown -R "$UTILIZADOR":"$UTILIZADOR" "$DESTINO"
        chmod 600 "$DESTINO/db_config.json"
    fi
fi

echo "Configuração concluída."
exit 0
