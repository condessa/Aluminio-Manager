#!/usr/bin/env bash
# Copia os ficheiros da última release para a pasta partilhada (Windows/VM).
# Uso: scripts/copiar_para_partilha.sh [destino]
set -euo pipefail

REPO="condessa/Aluminio-Manager"
DESTINO="${1:-$HOME/PartilhaWindows}"
TOKEN="${GITHUB_TOKEN:-$(cat "$HOME/.config/hcgestao-github-token" 2>/dev/null || true)}"

mkdir -p "$DESTINO"

INFO=$(curl -fsSL -H "Authorization: Bearer $TOKEN" \
    "https://api.github.com/repos/$REPO/releases/latest")

TAG=$(printf '%s' "$INFO" | python3 -c 'import json,sys; print(json.load(sys.stdin)["tag_name"])')
echo "Última release: $TAG"

printf '%s' "$INFO" | python3 -c '
import json, sys
for a in json.load(sys.stdin)["assets"]:
    print(a["size"], a["browser_download_url"])
' | while read -r tamanho url; do
    nome=$(basename "$url")
    if [ -f "$DESTINO/$nome" ] && [ "$(stat -c%s "$DESTINO/$nome")" = "$tamanho" ]; then
        echo "  = $nome (já existe)"
        continue
    fi
    echo "  ↓ $nome"
    curl -fL --retry 3 --progress-bar -o "$DESTINO/$nome.part" "$url"
    mv "$DESTINO/$nome.part" "$DESTINO/$nome"
done

echo "Concluído: $DESTINO"
ls -lh "$DESTINO"/AluminioManager-Setup-*.exe "$DESTINO"/aluminio-manager_*_amd64.deb 2>/dev/null | tail -4
