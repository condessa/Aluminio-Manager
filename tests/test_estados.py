"""Testes da máquina de estados das obras."""

import unittest

from modules.obras import transicoes_permitidas, validar_transicao


class TransicoesTest(unittest.TestCase):
    def test_progressao_normal(self):
        self.assertIsNone(validar_transicao("orcamento", "confirmada"))
        self.assertIsNone(validar_transicao("confirmada", "em_producao"))
        self.assertIsNone(validar_transicao("em_producao", "em_montagem"))
        self.assertIsNone(validar_transicao("em_montagem", "concluida"))

    def test_nao_retrocede(self):
        self.assertIsNotNone(validar_transicao("em_montagem", "orcamento"))
        self.assertIsNotNone(validar_transicao("confirmada", "orcamento"))

    def test_concluida_e_final(self):
        self.assertEqual(transicoes_permitidas("concluida"), [])
        self.assertIsNotNone(validar_transicao("concluida", "cancelada"))
        self.assertIn("já não pode", validar_transicao("concluida", "cancelada"))

    def test_cancelada_e_final(self):
        self.assertEqual(transicoes_permitidas("cancelada"), [])
        self.assertIsNotNone(validar_transicao("cancelada", "confirmada"))
        self.assertIsNotNone(validar_transicao("cancelada", "concluida"))

    def test_cancelar_em_curso_e_permitido(self):
        self.assertIsNone(validar_transicao("em_producao", "cancelada"))
        self.assertIsNone(validar_transicao("orcamento", "cancelada"))

    def test_em_espera_volta_ao_estado_anterior(self):
        self.assertEqual(transicoes_permitidas("em_espera", "em_montagem"),
                         ["em_montagem", "cancelada"])
        self.assertIsNone(validar_transicao("em_espera", "em_montagem", "em_montagem"))
        self.assertIsNotNone(validar_transicao("em_espera", "orcamento", "em_montagem"))

    def test_em_espera_sem_memoria_permite_activos(self):
        self.assertEqual(transicoes_permitidas("em_espera"),
                         ["orcamento", "confirmada", "em_producao", "em_montagem", "cancelada"])


if __name__ == "__main__":
    unittest.main()
