import unittest
from datetime import datetime

from app.agents.classifier_agent import ClassifierAgent
from app.agents.dossier_agent import DossierAgent
from app.agents.rag_agent import RagAgent
from app.repositories.mock_repo import MockRepository
from app.services.regulatorio_service import RegulatorioService


class FakeLLM:
    def __init__(self):
        self.calls = 0

    def complete(self, system: str, user: str, model: str, max_tokens: int = 1024) -> str:
        self.calls += 1
        if "JSON estrito" in system:
            return '{"razao":"confiabilidade","confianca":0.9,"justificativa":"teste"}'
        return "# Dossiê\n\nRascunho."


class TestRegulatorioService(unittest.TestCase):
    def setUp(self):
        repo = MockRepository(mvp_only_nordeste=True)
        llm = FakeLLM()
        classifier = ClassifierAgent(llm, model="fake")
        dossier = DossierAgent(llm, model="fake")
        rag = RagAgent(llm, model="fake", knowledge_dir=__import__("pathlib").Path("app/knowledge"))
        self.llm = llm
        self.svc = RegulatorioService(repo, classifier, dossier, rag, cache=__import__("app.utils.simple_cache", fromlist=["TTLCache"]).TTLCache(ttl_seconds=3600))

    def test_classificar_eventos(self):
        out = self.svc.classificar_eventos(
            "USI_NE_001",
            datetime.fromisoformat("2026-05-01T00:00:00"),
            datetime.fromisoformat("2026-05-02T00:00:00"),
        )
        self.assertIn("eventos", out)
        self.assertEqual(len(out["eventos"]), 2)
        self.assertIn("qualidade_classificacao", out)

    def test_classificador_so_em_caso_ambiguo(self):
        out = self.svc.classificar_eventos(
            "USI_NE_001",
            datetime.fromisoformat("2026-05-01T00:00:00"),
            datetime.fromisoformat("2026-05-02T00:00:00"),
        )
        # no dataset atual USI_NE_001 já vem com razões válidas, então não deve chamar classificador
        self.assertEqual(out["qualidade_classificacao"]["eventos_classificados_por_ia"], 0)
        self.assertEqual(self.llm.calls, 0)

    def test_classificar_eventos_cache(self):
        inicio = datetime.fromisoformat("2026-05-01T00:00:00")
        fim = datetime.fromisoformat("2026-05-02T00:00:00")
        _ = self.svc.classificar_eventos("USI_NE_001", inicio, fim)
        calls_after_first = self.llm.calls
        _ = self.svc.classificar_eventos("USI_NE_001", inicio, fim)
        self.assertEqual(self.llm.calls, calls_after_first)

    def test_regra_elegibilidade_parametrizavel(self):
        repo = MockRepository(mvp_only_nordeste=True)
        llm = FakeLLM()
        classifier = ClassifierAgent(llm, model="fake")
        dossier = DossierAgent(llm, model="fake")
        rag = RagAgent(llm, model="fake", knowledge_dir=__import__("pathlib").Path("app/knowledge"))
        svc = RegulatorioService(
            repo,
            classifier,
            dossier,
            rag,
            regras_elegibilidade={
                "confiabilidade": True,
                "indisponibilidade_externa": True,
                "energetico": True,
                "indefinido": False,
            },
            cache=__import__("app.utils.simple_cache", fromlist=["TTLCache"]).TTLCache(ttl_seconds=3600),
        )
        out = svc.classificar_eventos(
            "USI_NE_001",
            datetime.fromisoformat("2026-05-01T00:00:00"),
            datetime.fromisoformat("2026-05-02T00:00:00"),
        )
        self.assertEqual(out["total_potencial_ressarcivel_reais"], 6750.0)

    def test_gerar_dossie(self):
        out = self.svc.gerar_dossie(
            "USI_NE_001",
            datetime.fromisoformat("2026-05-01T00:00:00"),
            datetime.fromisoformat("2026-05-02T00:00:00"),
        )
        self.assertIn("dossie_markdown", out)
        self.assertTrue(out["dossie_markdown"].startswith("# Dossiê"))

    def test_cache_dossie(self):
        inicio = datetime.fromisoformat("2026-05-01T00:00:00")
        fim = datetime.fromisoformat("2026-05-02T00:00:00")
        _ = self.svc.gerar_dossie("USI_NE_001", inicio, fim)
        calls_after_first = self.llm.calls
        _ = self.svc.gerar_dossie("USI_NE_001", inicio, fim)
        self.assertEqual(self.llm.calls, calls_after_first)


if __name__ == "__main__":
    unittest.main()
