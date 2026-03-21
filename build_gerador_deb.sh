#!/bin/bash
VERSION="1.0.0"
PKG="gerador-licencas"
DIR="/tmp/${PKG}_${VERSION}"

# Estrutura do pacote
mkdir -p "${DIR}/DEBIAN"
mkdir -p "${DIR}/usr/bin"
mkdir -p "${DIR}/usr/share/${PKG}"
mkdir -p "${DIR}/usr/share/applications"

# Copiar ficheiros necessários
cp GeradorLicencas.py "${DIR}/usr/share/${PKG}/"
cp modules/licenca.py "${DIR}/usr/share/${PKG}/"
cp credentials.json "${DIR}/usr/share/${PKG}/" 2>/dev/null || true

# Script de arranque
cat > "${DIR}/usr/bin/gerador-licencas" << 'SCRIPT'
#!/bin/bash
cd /usr/share/gerador-licencas
python3 GeradorLicencas.py
SCRIPT
chmod +x "${DIR}/usr/bin/gerador-licencas"

# Ficheiro .desktop
cat > "${DIR}/usr/share/applications/gerador-licencas.desktop" << 'DESK'
[Desktop Entry]
Version=1.0
Type=Application
Name=Gerador de Licenças
Comment=AluminioManager — Gerador de Licenças HCsoftware
Exec=gerador-licencas
Terminal=false
Categories=Utility;
DESK

# Controlo do pacote
cat > "${DIR}/DEBIAN/control" << CTRL
Package: ${PKG}
Version: ${VERSION}
Architecture: amd64
Maintainer: HCsoftware <condessasilva@gmail.com>
Depends: python3, python3-pyqt6
Description: Gerador de Licenças — AluminioManager
 Ferramenta do programador para gerar códigos de activação
 do AluminioManager by HCsoftware.
CTRL

# Construir .deb
dpkg-deb --build "${DIR}" "dist/${PKG}_${VERSION}.deb"
echo "Pacote criado: dist/${PKG}_${VERSION}.deb"
