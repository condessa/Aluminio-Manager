"""Registo de erros e de arranque em ficheiro, para diagnóstico."""

import datetime
import traceback
from pathlib import Path


def pasta():
    """Pasta de configuração do programa (onde fica o erro.log)."""
    try:
        from db.database import caminho_config
        return caminho_config().parent
    except Exception:
        return Path.home() / ".config" / "aluminio-manager"


def registar(texto):
    try:
        destino = pasta()
        destino.mkdir(parents=True, exist_ok=True)
        with open(destino / "erro.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {texto}\n")
    except Exception:
        pass


def registar_excecao(exc=None):
    exc = exc or traceback.format_exc()
    registar("ERRO NÃO TRATADO:\n" + str(exc))


def ficheiro():
    return pasta() / "erro.log"
