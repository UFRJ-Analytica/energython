import os
import unittest

from fastapi.testclient import TestClient


def _bool_env(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}


@unittest.skipUnless(_bool_env("RUN_E2E_POSTGRES", False), "Defina RUN_E2E_POSTGRES=1 para habilitar teste E2E com banco real")
class TestE2ERessarcimentoPostgres(unittest.TestCase):
    def setUp(self):
        os.environ["DATA_BACKEND"] = "postgres"
        os.environ["MVP_ONLY_NORDESTE"] = "true"

        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            self.skipTest("DATABASE_URL não definido para E2E postgres")

        # Import tardio para garantir leitura das variáveis de ambiente acima
        from app.main import app  # noqa: WPS433

        self.client = TestClient(app)

    def test_fluxo_ressarcimento_postgres(self):
        response = self.client.post(
            "/api/usinas/RNUAU/ressarcimento",
            json={
                "inicio": "2026-05-01T00:00:00",
                "fim": "2026-05-02T00:00:00",
                "franquia_horas_override": 1,
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()

        self.assertEqual(body["usina_id"], "RNUAU")
        self.assertIn("resultado_elegibilidade", body)
        self.assertIn("dossie_markdown", body)
        self.assertIn("human_in_the_loop", body)
        self.assertFalse(body["human_in_the_loop"]["submissao_automatica_habilitada"])

        resultado = body["resultado_elegibilidade"]
        self.assertIn("metadata", resultado)
        self.assertEqual(resultado["metadata"]["api_contract_version"], "v1")
        # Em ambientes com cache aquecido, metadata interna pode vir de entrada legada sem esse campo.
        self.assertIn("eventos", resultado)
        self.assertIn("total_potencial_ressarcivel_reais", resultado)
        self.assertIn("total_ressarcivel_pos_franquia_reais", resultado)


if __name__ == "__main__":
    unittest.main()
