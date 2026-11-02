"""Ligação SQLite com a mesma interface que o programa usava com o MySQL.

Os módulos chamam ``cursor(dictionary=True)`` e usam marcadores ``%s``.
Este adaptador traduz essas chamadas para o ``sqlite3``, para não ser
necessário reescrever as consultas existentes.
"""

import sqlite3
from pathlib import Path


class Cursor:
    def __init__(self, cursor, dictionary=False):
        self._cursor = cursor
        self._dictionary = dictionary

    def execute(self, sql, params=None):
        self._cursor.execute(sql.replace("%s", "?"), params or ())
        return self

    def executemany(self, sql, sequencia):
        self._cursor.executemany(sql.replace("%s", "?"), sequencia)
        return self

    def fetchone(self):
        linha = self._cursor.fetchone()
        if linha is None:
            return None
        return dict(linha) if self._dictionary else linha

    def fetchall(self):
        linhas = self._cursor.fetchall()
        if self._dictionary:
            return [dict(linha) for linha in linhas]
        return linhas

    def __iter__(self):
        for linha in self._cursor:
            yield dict(linha) if self._dictionary else linha

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def close(self):
        self._cursor.close()


class Ligacao:
    def __init__(self, caminho):
        self.caminho = Path(caminho)
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.caminho), timeout=15)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.execute("PRAGMA synchronous = NORMAL")

    def cursor(self, dictionary=False, **ignorados):
        return Cursor(self._conn.cursor(), dictionary)

    def execute(self, sql, params=None):
        return self._conn.execute(sql.replace("%s", "?"), params or ())

    def executescript(self, script):
        self._conn.executescript(script)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    @property
    def raw(self):
        return self._conn
