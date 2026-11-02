#!/bin/bash
set -e

VERSION=${1:-1.2.0}
APP=aluminio-manager
BUILD_DIR="/tmp/${APP}_${VERSION}"
INSTALL_DIR="${BUILD_DIR}/usr/share/aluminio-manager"
BIN_DIR="${BUILD_DIR}/usr/local/bin"
DESKTOP_DIR="${BUILD_DIR}/usr/share/applications"
ICONS_DIR="${BUILD_DIR}/usr/share/icons/hicolor" 
DEBIAN_DIR="${BUILD_DIR}/DEBIAN"

echo "🔨 A construir AluminioManager v${VERSION}..."

# Limpar build anterior
rm -rf "$BUILD_DIR"
mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$DESKTOP_DIR" "$DEBIAN_DIR"
mkdir -p "$ICONS_DIR/16x16/apps" "$ICONS_DIR/32x32/apps" "$ICONS_DIR/48x48/apps"
mkdir -p "$ICONS_DIR/64x64/apps" "$ICONS_DIR/128x128/apps" "$ICONS_DIR/256x256/apps"
mkdir -p "$ICONS_DIR/512x512/apps"

# Copiar ficheiros da aplicação
cp main.py version.py requirements.txt "$INSTALL_DIR/"
cp -r db modules "$INSTALL_DIR/"

# Copiar ícones
if [ -d icons ]; then
    cp icons/aluminio_16.png   "$ICONS_DIR/16x16/apps/aluminio-manager.png"
    cp icons/aluminio_32.png   "$ICONS_DIR/32x32/apps/aluminio-manager.png"
    cp icons/aluminio_48.png   "$ICONS_DIR/48x48/apps/aluminio-manager.png"
    cp icons/aluminio_64.png   "$ICONS_DIR/64x64/apps/aluminio-manager.png"
    cp icons/aluminio_128.png  "$ICONS_DIR/128x128/apps/aluminio-manager.png"
    cp icons/aluminio_256.png  "$ICONS_DIR/256x256/apps/aluminio-manager.png"
    cp icons/aluminio_512.png  "$ICONS_DIR/512x512/apps/aluminio-manager.png"
    cp -r icons "$INSTALL_DIR/"
fi

# Copiar certificado se existir
if [ -d cert ]; then
    cp -r cert "$INSTALL_DIR/"
fi

# Instalar dependências Python no pacote
echo "📦 A instalar dependências Python..."
pip install --quiet --target="${INSTALL_DIR}/lib" \
    mysql-connector-python \
    pyhanko \
    pyhanko-certvalidator \
    Pillow \
    cryptography \
    PyQt6 \
    PyQt6-Qt6 \
    PyQt6-sip \
    openpyxl \
    python-dateutil \
    matplotlib \
    reportlab 2>/dev/null || true

# Script de arranque
cat > "${BIN_DIR}/aluminio-manager" << 'EOF'
#!/bin/bash
cd /usr/share/aluminio-manager
export PYTHONPATH="/usr/share/aluminio-manager/lib:$PYTHONPATH"
python3 main.py "$@"
EOF
chmod +x "${BIN_DIR}/aluminio-manager"

# Ficheiro .desktop
cat > "${DESKTOP_DIR}/aluminio-manager.desktop" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Aluminios Manager
GenericName=Gestão de Alumínios
Comment=Sistema de gestão para oficinas de alumínio e caixilharia
Exec=aluminio-manager
Icon=/usr/share/icons/hicolor/256x256/apps/aluminio-manager.png
Categories=Office;ProjectManagement;
Terminal=false
StartupNotify=true
StartupWMClass=aluminio-manager
EOF

# Script pós-instalação
cat > "${DEBIAN_DIR}/postinst" << 'EOF'
#!/bin/bash
set -e
# Instalar PyQt6 via apt se não existir
if ! python3 -c "import PyQt6" 2>/dev/null; then
    apt-get install -y python3-pyqt6 python3-pyqt6.qtprintsupport 2>/dev/null || \
    pip3 install PyQt6 --break-system-packages 2>/dev/null || true
fi
# Instalar dependências Python
pip3 install --quiet --break-system-packages \
    mysql-connector-python pyhanko pyhanko-certvalidator Pillow cryptography openpyxl python-dateutil matplotlib reportlab 2>/dev/null || true

# Criar directório de config
mkdir -p /etc/aluminio-manager
chmod 755 /etc/aluminio-manager

# Actualizar cache de ícones
gtk-update-icon-cache -f -t /usr/share/icons/hicolor/ 2>/dev/null || true
update-desktop-database /usr/share/applications/ 2>/dev/null || true

# ── Base de dados ────────────────────────────────────────────────────────
# Numa instalação nova, cria a base de dados e o utilizador para o programa
# arrancar logo. Nunca mexe numa configuração já existente.
DB_CONFIG=/etc/aluminio-manager/db_config.json
if command -v mysql >/dev/null 2>&1 && [ ! -f "$DB_CONFIG" ]; then
    systemctl start mariadb 2>/dev/null || systemctl start mysql 2>/dev/null || true
    DB_PASS="$(head -c 32 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 24)"
    if mysql --protocol=socket -uroot -e "SELECT 1" >/dev/null 2>&1; then
        if mysql --protocol=socket -uroot <<SQL
CREATE DATABASE IF NOT EXISTS aluminio_manager CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'aluminio_user'@'localhost' IDENTIFIED BY '${DB_PASS}';
ALTER USER 'aluminio_user'@'localhost' IDENTIFIED BY '${DB_PASS}';
GRANT ALL PRIVILEGES ON aluminio_manager.* TO 'aluminio_user'@'localhost';
FLUSH PRIVILEGES;
SQL
        then
            mkdir -p /etc/aluminio-manager
            umask 077
            cat > "$DB_CONFIG" <<JSON
{"host": "localhost", "port": 3306, "database": "aluminio_manager", "user": "aluminio_user", "password": "${DB_PASS}"}
JSON
            if [ -n "${SUDO_USER:-}" ] && id "$SUDO_USER" >/dev/null 2>&1; then
                chown "$SUDO_USER":"$SUDO_USER" "$DB_CONFIG"
            fi
            chmod 600 "$DB_CONFIG"
            umask 022
            echo "   Base de dados preparada (utilizador aluminio_user)."
        else
            echo "   AVISO: não foi possível preparar a base de dados."
            echo "   Ao abrir, o programa pede os dados de ligação."
        fi
    else
        echo "   AVISO: o MySQL/MariaDB não respondeu como root."
        echo "   Ao abrir, o programa pede os dados de ligação."
    fi
fi

echo ""
echo "✅ AluminioManager instalado com sucesso!"
echo "   Execute: aluminio-manager"
echo "   Login inicial: admin / admin123"
EOF
chmod 755 "${DEBIAN_DIR}/postinst"

# Script pré-remoção
cat > "${DEBIAN_DIR}/prerm" << 'EOF'
#!/bin/bash
echo "A remover AluminioManager..."
EOF
chmod 755 "${DEBIAN_DIR}/prerm"

# Calcular tamanho
SIZE=$(du -sk "$BUILD_DIR" | cut -f1)

# Ficheiro control
cat > "${DEBIAN_DIR}/control" << EOF
Package: ${APP}
Version: ${VERSION}
Section: office
Priority: optional
Architecture: amd64
Installed-Size: ${SIZE}
Depends: python3 (>= 3.10), python3-pip, mariadb-server | default-mysql-server, mariadb-client | mysql-client
Recommends: python3-pyqt6
Maintainer: HCsoftware <hcsoftware@hcsoftware.pt>
Description: Aluminios Manager by HCsoftware
 Sistema de gestão completo para oficinas de alumínio e caixilharia.
 Gestão de obras, clientes, stock, financeiro, tarefas e muito mais.
 Inclui envio de orçamentos por email com assinatura digital.
EOF

# Construir .deb
mkdir -p dist
dpkg-deb --root-owner-group --build "$BUILD_DIR" "dist/${APP}_${VERSION}_amd64.deb"

echo ""
echo "✅ Pacote criado: dist/${APP}_${VERSION}_amd64.deb"
echo "   Para instalar: sudo dpkg -i dist/${APP}_${VERSION}_amd64.deb"
echo "   Login inicial: admin / admin123"
