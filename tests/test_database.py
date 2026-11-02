"""Testes da base de dados SQLite."""

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

import db.database as bd


class BaseDadosTest(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self._antes = os.environ.get("ALUMINIO_DB")
        os.environ["ALUMINIO_DB"] = str(Path(self.pasta.name) / "teste.db")
        bd.garantir_schema()

    def tearDown(self):
        if self._antes is None:
            os.environ.pop("ALUMINIO_DB", None)
        else:
            os.environ["ALUMINIO_DB"] = self._antes

    def test_cria_tabelas_principais(self):
        conn = bd.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas = {linha[0] for linha in cur.fetchall()}
        cur.close()
        conn.close()
        for esperada in ("utilizadores", "oficina", "clientes", "obras", "stock", "financeiro"):
            self.assertIn(esperada, tabelas)

    def test_categorias_iniciais(self):
        conn = bd.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM stock_categorias")
        total = cur.fetchone()[0]
        cur.close()
        conn.close()
        self.assertEqual(total, 7)

    def test_marcadores_e_dicionario(self):
        conn = bd.get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("INSERT INTO clientes (nome, localidade) VALUES (%s, %s)", ("Ana", "Silves"))
        conn.commit()
        cur.execute("SELECT * FROM clientes WHERE nome=%s", ("Ana",))
        linha = cur.fetchone()
        cur.close()
        conn.close()
        self.assertEqual(linha["localidade"], "Silves")

    def test_ultimo_id_inserido(self):
        conn = bd.get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO fornecedores (nome) VALUES (%s)", ("Fornecedor X",))
        conn.commit()
        self.assertIsNotNone(cur.lastrowid)
        cur.close()
        conn.close()

    def test_username_unico(self):
        conn = bd.get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO utilizadores (nome, username, password_hash) VALUES (%s,%s,%s)",
            ("A", "ana", bd.hash_password("segredo")))
        conn.commit()
        with self.assertRaises(sqlite3.IntegrityError):
            cur.execute(
                "INSERT INTO utilizadores (nome, username, password_hash) VALUES (%s,%s,%s)",
                ("B", "ana", bd.hash_password("outro")))
        cur.close()
        conn.close()

    def test_chave_oficina_actualizada(self):
        conn = bd.get_connection()
        cur = conn.cursor()
        for valor in ("Empresa A", "Empresa B"):
            cur.execute(
                "INSERT INTO oficina (chave, valor) VALUES (%s, %s) "
                "ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor",
                ("nome", valor))
        conn.commit()
        cur.execute("SELECT valor FROM oficina WHERE chave='nome'")
        self.assertEqual(cur.fetchone()[0], "Empresa B")
        cur.close()
        conn.close()

    def test_garantir_schema_e_idempotente(self):
        bd.garantir_schema()
        bd.garantir_schema()
        conn = bd.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM stock_categorias")
        self.assertEqual(cur.fetchone()[0], 7)
        cur.close()
        conn.close()

    def test_hash_password(self):
        self.assertEqual(bd.hash_password("abc"), bd.hash_password("abc"))
        self.assertNotEqual(bd.hash_password("abc"), bd.hash_password("abd"))


class ErrosTest(unittest.TestCase):
    def test_ficheiro_sem_permissao(self):
        erro = sqlite3.OperationalError("unable to open database file")
        self.assertIn("ficheiro", bd.descrever_erro(erro))

    def test_base_bloqueada(self):
        erro = sqlite3.OperationalError("database is locked")
        self.assertIn("outro processo", bd.descrever_erro(erro))


if __name__ == "__main__":
    unittest.main()
