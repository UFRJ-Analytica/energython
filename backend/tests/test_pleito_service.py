import unittest
from datetime import datetime

from app.agents.dossier_agent import DossierAgent
from app.engine.elegibilidade import classificar_elegibilidade, normalizar_razao_pleito
from app.repositories.mock_repo import MockRepository
from app.services.pleito_service import PleitoService


class FakeLLM:
    def complete(self, system: str, user: str, model: str, max_tokens: int = 1024) -> str:
        return '{"status":"mock","message":"anthropic_disabled"}'


class TestPleitoService(unittest.TestCase):
    def test_normalizar_razao_pleito_aceita_codigos_e_descricoes_ons(self):
        casos = {
            "CNF": "CNF",
            "cnf": "CNF",
            "CNF - Confiabilidade": "CNF",
            "confiabilidade": "CNF",
            "REL": "REL",
            "REL - Restrição elétrica": "REL",
            "indisponibilidade_externa": "REL",
            "restrição por indisponibilidade externa": "REL",
            "ENE": "ENE",
            "energético": "ENE",
            "restrição energética": "ENE",
        }
        for entrada, esperado in casos.items():
            with self.subTest(entrada=entrada):
                self.assertEqual(normalizar_razao_pleito(entrada), esperado)

    def test_elegibilidade_por_codigo_ons_pos_lei_15269(self):
        self.assertTrue(classificar_elegibilidade("CNF", origem="SIS").elegivel)
        self.assertTrue(classificar_elegibilidade("REL", origem="SIS").elegivel)
        self.assertFalse(classificar_elegibilidade("ENE", origem="SIS").elegivel)
        self.assertFalse(classificar_elegibilidade("CNF", origem="LOC").elegivel)

    def setUp(self):
        self.repo = MockRepository(mvp_only_nordeste=True)
        self.svc = PleitoService(self.repo, DossierAgent(FakeLLM(), model="fake"))
        self.inicio = datetime.fromisoformat("2026-05-01T00:00:00")
        self.fim = datetime.fromisoformat("2026-05-02T00:00:00")

    def test_listar_eventos_para_pleito_evento_a_evento(self):
        out = self.svc.listar_eventos_para_pleito("USI_NE_001", self.inicio, self.fim)
        self.assertEqual(out["metadata"]["api_contract_version"], "pleito_evento_v1")
        self.assertEqual(out["total_eventos"], 2)
        self.assertGreaterEqual(out["eventos_elegiveis"], 1)
        ev = out["eventos"][0]
        self.assertIn("evento_id", ev)
        self.assertIn(ev["razao_classificada_ons"], {"REL", "CNF", "ENE"})
        self.assertIn("janela_prazo", ev)
        self.assertIn("reconciliacao", ev)
        self.assertIn("valor_pleitavel_reais", ev)

    def test_gerar_pleito_por_evento_com_template_fallback(self):
        eventos = self.svc.listar_eventos_para_pleito("USI_NE_001", self.inicio, self.fim)["eventos"]
        elegivel = next(e for e in eventos if e["elegivel"])
        out = self.svc.gerar_pleito(
            "USI_NE_001",
            [elegivel["evento_id"]],
            elegivel["canal_recomendado"],
            inicio=self.inicio,
            fim=self.fim,
        )
        self.assertEqual(out["status"], "RASCUNHO")
        self.assertEqual(out["eventos_ids"], [elegivel["evento_id"]])
        self.assertIn(elegivel["evento_id"], out["markdown_gerado"])
        self.assertIn("Revisão humana obrigatória", out["markdown_gerado"])
        exported = self.svc.exportar_pleito(out["pleito_id"], "md")
        self.assertEqual(exported["formato"], "md")
        self.assertTrue(exported["file_name"].endswith(".md"))


if __name__ == "__main__":
    unittest.main()
