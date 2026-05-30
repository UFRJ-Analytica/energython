import unittest
from datetime import datetime

from app.repositories.mock_repo import MockRepository
from app.services.financeiro_service import FinanceiroService


class _RepoSemPld(MockRepository):
    def get_pld(self, submercado: str, inicio: datetime, fim: datetime):
        base = super().get_pld(submercado, inicio, fim)
        if base:
            # força ausência parcial de PLD para validar comportamento de qualidade de dados
            return base[:-1]
        return base


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

    def test_calcular_perda_marca_qualidade_quando_falta_pld(self):
        svc = FinanceiroService(_RepoSemPld(mvp_only_nordeste=True))
        out = svc.calcular_perda(
            "USI_NE_001",
            datetime.fromisoformat("2026-05-01T00:00:00"),
            datetime.fromisoformat("2026-05-02T00:00:00"),
        )
        self.assertIn("qualidade_dados", out)
        self.assertEqual(out["qualidade_dados"]["status"], "parcial")
        self.assertEqual(out["qualidade_dados"]["pld_faltante_eventos"], 1)

    def test_calcular_perda_sem_pld_retorna_zero_com_flag(self):
        class RepoSemNadaPld(MockRepository):
            def get_pld(self, submercado: str, inicio: datetime, fim: datetime):
                return []

        svc = FinanceiroService(RepoSemNadaPld(mvp_only_nordeste=True))
        out = svc.calcular_perda(
            "USI_NE_001",
            datetime.fromisoformat("2026-05-01T00:00:00"),
            datetime.fromisoformat("2026-05-02T00:00:00"),
        )
        self.assertEqual(out["total_perda_reais"], 0.0)
        self.assertEqual(out["qualidade_dados"]["status"], "sem_pld")


if __name__ == "__main__":
    unittest.main()
