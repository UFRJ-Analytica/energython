import unittest
from datetime import datetime

from app.repositories.mock_repo import MockRepository


class TestRepositories(unittest.TestCase):
    def setUp(self):
        self.repo = MockRepository(mvp_only_nordeste=True)

    def test_list_usinas_ne_only_default(self):
        items = self.repo.list_usinas()
        self.assertGreater(len(items), 0)
        self.assertTrue(all(i["submercado"] == "NE" for i in items))

    def test_get_usina_inexistente(self):
        self.assertIsNone(self.repo.get_usina("USINA_INEXISTENTE"))

    def test_get_pld_periodo_sem_dados(self):
        inicio = datetime.fromisoformat("2030-01-01T00:00:00")
        fim = datetime.fromisoformat("2030-01-01T01:00:00")
        items = self.repo.get_pld("NE", inicio, fim)
        self.assertEqual(items, [])

    def test_get_geracao_horaria_contract(self):
        inicio = datetime.fromisoformat("2026-05-01T00:00:00")
        fim = datetime.fromisoformat("2026-05-01T23:59:59")
        items = self.repo.get_geracao_horaria("USI_NE_001", inicio, fim)
        self.assertGreaterEqual(len(items), 1)
        self.assertIn("geracao_mwh", items[0])
        self.assertIn("fator_capacidade", items[0])

    def test_get_clima_horario_forecast_filter(self):
        inicio = datetime.fromisoformat("2026-05-01T00:00:00")
        fim = datetime.fromisoformat("2026-05-01T23:59:59")
        forecast = self.repo.get_clima_horario("USI_NE_001", inicio, fim, is_forecast=True)
        observed = self.repo.get_clima_horario("USI_NE_001", inicio, fim, is_forecast=False)
        self.assertTrue(all(i["is_forecast"] is True for i in forecast))
        self.assertTrue(all(i["is_forecast"] is False for i in observed))


if __name__ == "__main__":
    unittest.main()
