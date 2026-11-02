# AluminioManager — Guia de Instalação

## Requisitos
- Python 3.10 ou superior (apenas para instalação a partir do código)
- Windows 10/11 ou Linux (Debian/Ubuntu)

A base de dados é **SQLite**: fica num único ficheiro local, não é preciso
instalar nem configurar nenhum servidor.

---

## Instalação a partir do código

```bash
pip install -r requirements.txt
python main.py
```

Na primeira execução o programa cria a base de dados e pede os dados da empresa
e a conta de administrador.

---

## Onde ficam os dados

| Sistema | Ficheiro |
|---|---|
| Linux | `~/.config/aluminio-manager/aluminio.db` |
| Windows | `%USERPROFILE%\.config\aluminio-manager\aluminio.db` |

Para backup basta copiar esse ficheiro (o programa também guarda cópias em
`~/Backups/aluminio-auto`).

---

## Instalador Windows

Descarregar `AluminioManager-Setup-*.exe` das releases e executar. Instala por
utilizador, cria atalhos e desinstalador.
