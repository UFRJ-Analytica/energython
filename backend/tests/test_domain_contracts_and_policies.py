import unittest
from datetime import datetime

from app.domain.contracts import parse_constrained_off, parse_pld
from app.domain.policies import FinanceiroPolicy, RegulatorioPolicy


class TestDomainContractsAndPolicies(unittest.TestCase):
    def test_parse_contracts_tipados(self):
        eventos = parse_constrained_off(
            [
                {
                    "timestamp": "2026-05-01T01:00:00",
                    "energia_restringida_mwh": "12.5",
                    "razao_restricao": "CNF",
                    "cod_origemrestricao": "SIS",
                    "origem_restricao": "Sistema",
                }
            ]
        )
        pld = parse_pld(
            [
                {
                    "timestamp": datetime.fromisoformat("2026-05-01T01:00:00"),
                    "pld_reais_mwh": "150.0",
                }
            ]
        )

        self.assertEqual(len(eventos), 1)
        self.assertEqual(eventos[0].energia_restringida_mwh, 12.5)
        self.assertEqual(eventos[0].razao_restricao, "CNF")
        self.assertEqual(eventos[0].cod_origemrestricao, "SIS")
        self.assertEqual(eventos[0].origem_restricao, "Sistema")
        self.assertEqual(len(pld), 1)
        self.assertEqual(pld[0].pld_reais_mwh, 150.0)

    def test_regulatorio_policy_normaliza_codigos_coff(self):
        policy = RegulatorioPolicy.default()
        self.assertEqual(policy.normalize_razao("CNF"), "confiabilidade")
        self.assertEqual(policy.normalize_razao("ENE"), "energetico")
        self.assertTrue(policy.is_elegivel("confiabilidade"))
        self.assertFalse(policy.is_elegivel("energetico"))
        self.assertEqual(policy.versao_regulatoria, "lei_15269_2025")

    def test_regulatorio_policy_usa_razao_e_origem_para_elegibilidade(self):
        policy = RegulatorioPolicy.default()
        self.assertTrue(policy.is_elegivel("confiabilidade", origem="SIS"))
        self.assertTrue(policy.is_elegivel("indisponibilidade_externa", origem="SIS"))
        self.assertFalse(policy.is_elegivel("energetico", origem="SIS"))
        self.assertFalse(policy.is_elegivel("confiabilidade", origem="LOC"))
        self.assertFalse(policy.is_elegivel("indisponibilidade_externa", origem=None))
        self.assertEqual(policy.classificar_elegibilidade("CNF", "SIS"), "ELEGIVEL")
        self.assertEqual(policy.classificar_elegibilidade("REL", "LOC"), "REVISAO_HUMANA")

    def test_regulatorio_policy_versionada_pre_lei(self):
        policy = RegulatorioPolicy.by_version("pre_lei_15269_2025")
        self.assertTrue(policy.is_elegivel("energetico"))
        self.assertEqual(policy.versao_regulatoria, "pre_lei_15269_2025")

    def test_financeiro_policy_status_qualidade(self):
        policy = FinanceiroPolicy.default()
        self.assertEqual(policy.classificar_status_qualidade_perda(0, 10), "completo")
        self.assertEqual(policy.classificar_status_qualidade_perda(1, 0), "sem_pld")
        self.assertEqual(policy.classificar_status_qualidade_perda(1, 5), "parcial")


if __name__ == "__main__":
    unittest.main()
