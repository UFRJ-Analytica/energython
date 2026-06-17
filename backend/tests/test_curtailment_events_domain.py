import unittest
from datetime import datetime, timedelta

from app.domain.curtailment_events import (
    COFF_INTERVAL_HOURS,
    COFF_VAL_GERACAOLIMITADA_UNIT,
    CurtailmentInterval,
    build_curtailment_intervals,
    classify_regulatory_eligibility,
    group_intervals_into_events,
    normalize_origin,
    normalize_reason,
)


class TestCurtailmentEventsDomain(unittest.TestCase):
    def _interval(
        self,
        ts: str,
        *,
        usina_id: str = "CJU_TESTE",
        tecnologia: str = "fotovoltaica",
        reason: str = "REL",
        origin: str = "SIS",
        energia: float = 10.0,
        perda: float = 1000.0,
    ) -> CurtailmentInterval:
        start = datetime.fromisoformat(ts)
        return CurtailmentInterval(
            interval_id=f"{usina_id}:{ts}:{reason}:{origin}",
            usina_id=usina_id,
            tecnologia=tecnologia,
            timestamp_inicio=start,
            timestamp_fim=start + timedelta(minutes=30),
            duracao_horas=0.5,
            energia_restringida_mwh=energia,
            perda_reais=perda,
            geracao_verificada_mwh=None,
            geracao_referencia_mwh=None,
            cod_razaorestricao=reason,
            cod_origemrestricao=origin,
            razao_normalizada=normalize_reason(reason),
            origem_normalizada=normalize_origin(origin),
            submercado="NE",
            source_table="test",
            data_quality_status="RESTRICAO_CLASSIFICADA",
        )

    def test_group_consecutive_30_min_intervals_into_one_event_preserving_totals(self):
        intervals = [
            self._interval("2026-05-01T10:00:00", energia=10.0, perda=100.0),
            self._interval("2026-05-01T10:30:00", energia=20.0, perda=200.0),
            self._interval("2026-05-01T11:00:00", energia=30.0, perda=300.0),
        ]

        events = group_intervals_into_events(intervals)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].n_intervalos, 3)
        self.assertEqual(events[0].duracao_horas, 1.5)
        self.assertEqual(events[0].energia_restringida_mwh, 60.0)
        self.assertEqual(events[0].perda_total_reais, 600.0)
        self.assertEqual(events[0].source_interval_ids, [i.interval_id for i in intervals])

    def test_group_temporal_gap_starts_new_event(self):
        intervals = [
            self._interval("2026-05-01T10:00:00"),
            self._interval("2026-05-01T11:00:00"),
        ]

        events = group_intervals_into_events(intervals)

        self.assertEqual(len(events), 2)
        self.assertTrue(events[1].gap_detectado)

    def test_group_reason_origin_plant_and_technology_changes_split_events(self):
        cases = [
            [self._interval("2026-05-01T10:00:00", reason="REL"), self._interval("2026-05-01T10:30:00", reason="CNF")],
            [self._interval("2026-05-01T10:00:00", origin="SIS"), self._interval("2026-05-01T10:30:00", origin="LOC")],
            [self._interval("2026-05-01T10:00:00", usina_id="A"), self._interval("2026-05-01T10:30:00", usina_id="B")],
            [self._interval("2026-05-01T10:00:00", tecnologia="eolica"), self._interval("2026-05-01T10:30:00", tecnologia="fotovoltaica")],
        ]
        for intervals in cases:
            with self.subTest(intervals=intervals):
                self.assertEqual(len(group_intervals_into_events(intervals)), 2)

    def test_build_intervals_classifies_and_converts_mwmed_unit(self):
        self.assertEqual(COFF_VAL_GERACAOLIMITADA_UNIT, "mwmed")
        rows = [
            {
                "usina_id": "CJU_TESTE",
                "timestamp": "2026-05-01T10:00:00",
                "fonte": "fotovoltaica",
                "energia_restringida_mwh": 20.0,
                "geracao_verificada_mwh": 5.0,
                "geracao_referencia_mwh": 25.0,
                "cod_razaorestricao": "REL",
                "cod_origemrestricao": "SIS",
                "submercado": "NE",
            }
        ]

        intervals = build_curtailment_intervals(rows, perda_por_intervalo={"2026-05-01 10:00:00": 123.0})

        self.assertEqual(COFF_INTERVAL_HOURS, 0.5)
        self.assertEqual(len(intervals), 1)
        self.assertEqual(intervals[0].energia_restringida_mwh, 10.0)
        self.assertEqual(intervals[0].data_quality_status, "RESTRICAO_CLASSIFICADA")
        self.assertEqual(intervals[0].perda_reais, 123.0)

    def test_regulatory_eligibility_uses_reason_and_origin(self):
        self.assertEqual(classify_regulatory_eligibility("CNF", "SIS"), "ELEGIVEL")
        self.assertEqual(classify_regulatory_eligibility("REL", "SIS"), "ELEGIVEL")
        self.assertEqual(classify_regulatory_eligibility("ENE", "SIS"), "NAO_ELEGIVEL")
        self.assertEqual(classify_regulatory_eligibility("CNF", "LOC"), "REVISAO_HUMANA")
        self.assertEqual(classify_regulatory_eligibility("REL", "LOC"), "REVISAO_HUMANA")
        self.assertEqual(classify_regulatory_eligibility(None, "SIS"), "REVISAO_HUMANA")
        self.assertEqual(classify_regulatory_eligibility("REL", None), "REVISAO_HUMANA")


if __name__ == "__main__":
    unittest.main()
