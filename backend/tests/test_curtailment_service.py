import subprocess
import sys
import unittest
from pathlib import Path

from app.repositories.mock_repo import MockRepository
from app.services.curtailment_service import CurtailmentService


class TestCurtailmentService(unittest.TestCase):
    def setUp(self):
        self.repo = MockRepository(mvp_only_nordeste=True)
        self.backend_dir = Path(__file__).resolve().parents[1]
        self.model_path = self.backend_dir / "models_ml" / "curtailment_model.pkl"

    def test_prever_risco_fallback_sem_modelo(self):
        svc = CurtailmentService(self.repo, model_path=str(self.backend_dir / "models_ml" / "nao_existe.pkl"))
        out = svc.prever_risco("USI_NE_001", horizonte_horas=24)
        self.assertEqual(out["usina_id"], "USI_NE_001")
        self.assertEqual(out["modelo"], "heuristico_fallback")
        self.assertIsInstance(out["previsoes"], list)

    def test_prever_risco_com_modelo_treinado(self):
        cmd = [
            sys.executable,
            "models_ml/train_curtailment_model.py",
            "--data-dir",
            "data/samples",
            "--output-model",
            str(self.model_path),
            "--output-metrics",
            "models_ml/curtailment_metrics.json",
        ]
        subprocess.run(cmd, cwd=self.backend_dir, check=True)

        svc = CurtailmentService(self.repo, model_path=str(self.model_path))
        out = svc.prever_risco("USI_NE_001", horizonte_horas=24)
        self.assertEqual(out["modelo"], "ml_base_random_forest")
        self.assertTrue(len(out["previsoes"]) >= 1)
        self.assertIn("prob_corte", out["previsoes"][0])
        self.assertIn("magnitude_estimada_mwh", out["previsoes"][0])


if __name__ == "__main__":
    unittest.main()
