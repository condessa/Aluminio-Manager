#!/usr/bin/env python3
"""Reset completo à base de dados SQLite."""

from pathlib import Path

from db.database import caminho_bd, garantir_schema


def reset_bd():
    print("\n⚠️  ATENÇÃO: Isto vai APAGAR TODOS OS DADOS!\n")
    resposta = input("Tens a certeza? (escreve 'SIM' para confirmar): ").strip()
    if resposta != "SIM":
        print("Operação cancelada.")
        return

    caminho = caminho_bd()
    for ficheiro in (caminho, Path(str(caminho) + "-wal"), Path(str(caminho) + "-shm")):
        try:
            ficheiro.unlink()
        except FileNotFoundError:
            pass
        except OSError as e:
            print(f"Não foi possível apagar {ficheiro}: {e}")
            return

    garantir_schema()
    print(f"\n✅ Base de dados recriada em: {caminho}")
    print("\nA conta de administrador é criada no próximo arranque.")


if __name__ == "__main__":
    reset_bd()
