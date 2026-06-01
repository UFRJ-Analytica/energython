import unittest

from fastapi.testclient import TestClient

from app.main import app


class TestEndpointsSmoke(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "ok")

    def test_readiness(self):
        r = self.client.get("/readiness")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["status"], "ready")
        self.assertIn("data_backend", body)
        self.assertIn("checks", body)

    def test_usinas_filter_submercado_ne(self):
        r = self.client.get("/api/usinas?submercado=NE&limit=50&offset=0")
        self.assertEqual(r.status_code, 200)
        items = r.json()["items"]
        self.assertTrue(all(i["submercado"] == "NE" for i in items))

    def test_usinas_list(self):
        r = self.client.get("/api/usinas?limit=1&offset=0")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("total_count", data)
        self.assertIn("items", data)
        self.assertIn("metadata", data)
        self.assertEqual(data["metadata"]["mvp_scope"], "geradoras_renovaveis_submercado_ne")
        self.assertEqual(data["metadata"]["api_contract_version"], "v1")
        self.assertTrue(isinstance(data["items"], list))

    def test_404_usina(self):
        r = self.client.get("/api/usinas/nao_existe")
        self.assertEqual(r.status_code, 404)
        body = r.json()
        self.assertEqual(body["detail"]["code"], "usina_nao_encontrada")
        self.assertIn("context", body["detail"])

    def test_422_data_invalida(self):
        r = self.client.get("/api/usinas/USI_NE_001/perda?inicio=abc&fim=2026-05-01T00:00:00")
        self.assertEqual(r.status_code, 422)
        body = r.json()
        self.assertEqual(body["detail"]["code"], "parametro_data_invalido")

    def test_perda_paginada(self):
        r = self.client.get(
            "/api/usinas/USI_NE_001/perda?inicio=2026-05-01T00:00:00&fim=2026-05-02T00:00:00&limit=1&offset=0"
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("paginacao_serie", body)
        self.assertEqual(body["paginacao_serie"]["total_count"], 2)
        self.assertEqual(len(body["serie"]), 1)

    def test_elegibilidade_paginada(self):
        r = self.client.get(
            "/api/usinas/USI_NE_001/elegibilidade?inicio=2026-05-01T00:00:00&fim=2026-05-02T00:00:00&limit=1&offset=0"
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("paginacao_eventos", body)
        self.assertEqual(body["paginacao_eventos"]["total_count"], 2)
        self.assertEqual(len(body["eventos"]), 1)

    def test_fluxo_ressarcimento(self):
        r = self.client.post(
            "/api/usinas/USI_NE_001/ressarcimento",
            json={
                "inicio": "2026-05-01T00:00:00",
                "fim": "2026-05-02T00:00:00",
                "franquia_horas_override": 1,
            },
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("resultado_elegibilidade", body)
        self.assertIn("dossie_markdown", body)
        self.assertIn("human_in_the_loop", body)
        self.assertFalse(body["human_in_the_loop"]["submissao_automatica_habilitada"])

    def test_export_dossie_markdown(self):
        r = self.client.post(
            "/api/usinas/USI_NE_001/dossie/export",
            json={
                "inicio": "2026-05-01T00:00:00",
                "fim": "2026-05-02T00:00:00",
                "formato": "markdown",
            },
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["formato"], "markdown")
        self.assertTrue(body["file_name"].endswith(".md"))
        self.assertIn("text/markdown", body["content_type"])

    def test_export_dossie_json(self):
        r = self.client.post(
            "/api/usinas/USI_NE_001/dossie/export",
            json={
                "inicio": "2026-05-01T00:00:00",
                "fim": "2026-05-02T00:00:00",
                "formato": "json",
            },
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["formato"], "json")
        self.assertTrue(body["file_name"].endswith(".json"))
        self.assertEqual(body["content_type"], "application/json")

    def test_export_dossie_formato_invalido(self):
        r = self.client.post(
            "/api/usinas/USI_NE_001/dossie/export",
            json={
                "inicio": "2026-05-01T00:00:00",
                "fim": "2026-05-02T00:00:00",
                "formato": "xml",
            },
        )
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.json()["detail"]["code"], "formato_exportacao_invalido")

    def test_previsao_perdas_diferencia_historico_e_previsao(self):
        r = self.client.get("/api/usinas/USI_NE_001/previsao-perdas?horizonte=24&historico_horas=48")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("serie_historico", body)
        self.assertIn("serie_previsao", body)
        self.assertIn("resumo", body)
        if body["serie_historico"]:
            self.assertEqual(body["serie_historico"][0]["tipo_dado"], "historico")
        if body["serie_previsao"]:
            self.assertEqual(body["serie_previsao"][0]["tipo_dado"], "previsao")

    def test_curtailment_previsao_detalhada(self):
        r = self.client.get("/api/usinas/USI_NE_001/curtailment/previsao-detalhada?horizonte=24")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("modelo", body)
        self.assertIn("previsoes", body)
        self.assertIn("resumo", body)
        self.assertEqual(body["tipo_dado"], "previsao")


if __name__ == "__main__":
    unittest.main()
