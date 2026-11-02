"""Testes da configuração da base de dados (sem servidor MySQL)."""

import json
import os
import tempfile
import unittest
from pathlib import Path

import db.database as bd


class ErroFalso(Exception):
    def __init__(self, errno):
        super().__init__("erro simulado")
        self.errno = errno


class ConfiguracaoTest(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.ficheiro = Path(self.pasta.name) / "config" / "db_config.json"
        self._antes = os.environ.get("ALUMINIO_DB_CONFIG")
        os.environ["ALUMINIO_DB_CONFIG"] = str(self.ficheiro)

    def tearDown(self):
        if self._antes is None:
            os.environ.pop("ALUMINIO_DB_CONFIG", None)
        else:
            os.environ["ALUMINIO_DB_CONFIG"] = self._antes

    def test_sem_ficheiro_usa_valores_por_omissao(self):
        cfg = bd.load_config()
        self.assertEqual(cfg["host"], "localhost")
        self.assertEqual(cfg["port"], 3306)
        self.assertEqual(cfg["user"], "aluminio_user")
        self.assertEqual(cfg["database"], "aluminio_manager")

    def test_guarda_e_volta_a_ler(self):
        cfg = {"host": "servidor.local", "port": 3307, "database": "bd",
               "user": "joao", "password": "segredo"}
        destino = bd.save_config(cfg)
        self.assertEqual(destino, self.ficheiro)
        self.assertEqual(bd.load_config(), cfg)
        self.assertEqual(self.ficheiro.stat().st_mode & 0o777, 0o600)

    def test_campos_em_falta_sao_preenchidos(self):
        self.ficheiro.parent.mkdir(parents=True)
        self.ficheiro.write_text(json.dumps({"host": "10.0.0.5"}), encoding="utf-8")
        cfg = bd.load_config()
        self.assertEqual(cfg["host"], "10.0.0.5")
        self.assertEqual(cfg["port"], 3306)
        self.assertEqual(cfg["user"], "aluminio_user")

    def test_ficheiro_corrompido_e_ignorado(self):
        self.ficheiro.parent.mkdir(parents=True)
        self.ficheiro.write_text("{isto não é json", encoding="utf-8")
        self.assertEqual(bd.load_config()["host"], "localhost")


class ErrosTest(unittest.TestCase):
    def test_servidor_em_baixo(self):
        texto = bd.descrever_erro(ErroFalso(2003))
        self.assertIn("contactar o servidor", texto)
        self.assertIn("Configurar automaticamente", texto)

    def test_credenciais_recusadas(self):
        texto = bd.descrever_erro(ErroFalso(1045))
        self.assertIn("recusou", texto)
        self.assertIn("Configurar automaticamente", texto)

    def test_base_de_dados_inexistente(self):
        self.assertIn("não existe", bd.descrever_erro(ErroFalso(1049)))

    def test_erro_desconhecido_mostra_mensagem_original(self):
        self.assertIn("erro simulado", bd.descrever_erro(ErroFalso(9999)))


if __name__ == "__main__":
    unittest.main()
