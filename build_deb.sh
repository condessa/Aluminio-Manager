#!/bin/bash
set -e

VERSION=${1:-1.5.8}
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
cp packaging/configurar_bd.sh "$INSTALL_DIR/"
if [ -d wheels ]; then cp -r wheels "$INSTALL_DIR/wheels"; fi
if [ -f credentials.json ]; then cp credentials.json "$INSTALL_DIR/"; fi
chmod 755 "$INSTALL_DIR/configurar_bd.sh"
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

# As dependências Python são instaladas no pós-instalação, com a versão
# de Python do sistema (evita binários incompatíveis).

# Script de arranque
cat > "${BIN_DIR}/aluminio-manager" << 'EOF'
#!/bin/bash
cd /usr/share/aluminio-manager
PYVER="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null)"
export PYTHONPATH="/usr/share/aluminio-manager/lib/${PYVER}${PYTHONPATH:+:$PYTHONPATH}"
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
# Dependências Python extraídas dos wheels incluídos (sem Internet e sem pip).
PYVER="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || echo "")"
PYNUM="$(printf '%s' "$PYVER" | tr -d '.')"
LIB="/usr/share/aluminio-manager/lib/${PYVER}"
WHEELS="/usr/share/aluminio-manager/wheels"
if [ -n "$PYVER" ] && ! PYTHONPATH="$LIB" python3 -c "import PyQt6, numpy, matplotlib, mysql.connector, cryptography, reportlab, openpyxl, dateutil, pyhanko" >/dev/null 2>&1; then
    if [ -d "$WHEELS" ]; then
        echo "   A instalar bibliotecas Python (${PYVER}) a partir do pacote…"
        mkdir -p "$LIB"
        for wheel in "$WHEELS"/*.whl; do
            [ -f "$wheel" ] || continue
            case "$(basename "$wheel")" in
                *-abi3-*.whl|*-none-any.whl|*-cp${PYNUM}-*.whl)
                    python3 -m zipfile -e "$wheel" "$LIB" 2>/dev/null || true
                    ;;
            esac
        done
    fi
    if ! PYTHONPATH="$LIB" python3 -c "import PyQt6, numpy, matplotlib" >/dev/null 2>&1; then
        echo "   AVISO: faltam bibliotecas para Python ${PYVER}."
        echo "   O pacote inclui wheels para Python 3.10, 3.11, 3.12 e 3.13."
    fi
fi

# Criar directório de config
mkdir -p /etc/aluminio-manager
chmod 755 /etc/aluminio-manager

# Actualizar cache de ícones
gtk-update-icon-cache -f -t /usr/share/icons/hicolor/ 2>/dev/null || true
update-desktop-database /usr/share/applications/ 2>/dev/null || true

# ── Base de dados ────────────────────────────────────────────────────────
# Cria a base de dados e deixa a configuração legível para a aplicação.
if [ -x /usr/share/aluminio-manager/configurar_bd.sh ]; then
    /usr/share/aluminio-manager/configurar_bd.sh "${SUDO_USER:-}" || {
        echo "   AVISO: a base de dados não pôde ser preparada automaticamente."
        echo "   Abra o programa e use «Configurar automaticamente»."
    }
fi

echo ""
echo "✅ AluminioManager instalado com sucesso!"
echo "   Execute: aluminio-manager"
echo "   Crie a conta de administrador no primeiro arranque."
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
Depends: python3 (>= 3.10), mariadb-server | default-mysql-server, mariadb-client | mysql-client
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
echo "   Crie a conta de administrador no primeiro arranque."
