import unittest
from datetime import datetime

from app.repositories.mock_repo import MockRepository
from app.services.financeiro_service import FinanceiroService


class TestFinanceiroService(unittest.TestCase):
    def setUp(self):
        self.repo = MockRepository(mvp_only_nordeste=True)
        self.svc = FinanceiroService(self.repo)

    def test_calcular_perda(self):
        out = self.svc.calcular_perda(
            "USI_NE_001",
            datetime.fromisoformat("2026-05-01T00:00:00"),
            datetime.fromisoformat("2026-05-02T00:00:00"),
        )
        self.assertEqual(out["total_perda_reais"], 6750.0)
        self.assertEqual(len(out["serie"]), 2)

    def test_projetar_exposicao(self):
        out = self.svc.projetar_exposicao("USI_NE_001", horizonte_horas=48)
        self.assertIn("exposicao_estimada_reais", out)
        self.assertGreaterEqual(out["exposicao_estimada_reais"], 0)


if __name__ == "__main__":
    unittest.main()
