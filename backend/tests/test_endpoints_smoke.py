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
        self.assertEqual(r.json()["status"], "ready")

    def test_usinas_list(self):
        r = self.client.get("/api/usinas?limit=1&offset=0")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("total_count", data)
        self.assertIn("items", data)
        self.assertTrue(isinstance(data["items"], list))

    def test_404_usina(self):
        r = self.client.get("/api/usinas/nao_existe")
        self.assertEqual(r.status_code, 404)
        body = r.json()
        self.assertEqual(body["detail"]["code"], "usina_nao_encontrada")

    def test_422_data_invalida(self):
        r = self.client.get("/api/usinas/USI_NE_001/perda?inicio=abc&fim=2026-05-01T00:00:00")
        self.assertEqual(r.status_code, 422)
        body = r.json()
        self.assertEqual(body["detail"]["code"], "parametro_data_invalido")


if __name__ == "__main__":
    unittest.main()
