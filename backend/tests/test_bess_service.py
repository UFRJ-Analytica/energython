import unittest
from datetime import datetime

from app.repositories.mock_repo import MockRepository
from app.services.bess_service import BessService


class TestBessService(unittest.TestCase):
    def setUp(self):
        self.repo = MockRepository(mvp_only_nordeste=True)
        self.svc = BessService(self.repo)

    def test_simular_bess_limites_fisicos_basicos(self):
        out = self.svc.simular_bess(
            usina_id="USI_NE_001",
            inicio=datetime.fromisoformat("2026-05-01T00:00:00"),
            fim=datetime.fromisoformat("2026-05-02T00:00:00"),
            potencia_bateria_mw=10,
            duracao_horas=2,
            eficiencia=0.85,
            capex=None,
        )
        # corte total = 30 MWh; com limite de potência por evento (10) e eficiência 0.85 => 17.0 MWh
        self.assertEqual(out["energia_recuperada_mwh"], 17.0)
        self.assertLessEqual(out["percentual_mitigado"], 100.0)

    def test_simular_bess_com_capex_retorna_payback(self):
        out = self.svc.simular_bess(
            usina_id="USI_NE_001",
            inicio=datetime.fromisoformat("2026-05-01T00:00:00"),
            fim=datetime.fromisoformat("2026-05-02T00:00:00"),
            potencia_bateria_mw=10,
            duracao_horas=2,
            eficiencia=0.85,
            capex=10000,
        )
        self.assertIsNotNone(out["payback_anos"])


if __name__ == "__main__":
    unittest.main()
