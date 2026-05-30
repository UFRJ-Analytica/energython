import unittest

from app.ml.features import build_inference_frame


class TestMlFeaturesReadiness(unittest.TestCase):
    def test_build_inference_frame_sets_optional_future_columns_with_missing_flags(self):
        usina = {"usina_id": "USI_NE_001", "fonte": "eolica", "submercado": "NE"}
        clima_future = [
            {
                "timestamp": "2026-05-01T14:00:00",
                "irradiancia_wm2": 760,
                "vento_ms": 10.1,
                "temperatura_c": 30.0,
                "is_forecast": True,
            }
        ]

        out = build_inference_frame(
            usina=usina,
            clima_future=clima_future,
            geracao_recent=[],
            constrained_recent=[],
            pld_recent=[],
            disponibilidade_recent=[],
            dessem_recent=[],
            garantia_fisica_recent=[],
        )

        self.assertEqual(len(out), 1)
        self.assertIn("disponibilidade", out.columns)
        self.assertIn("teifa", out.columns)
        self.assertIn("teip", out.columns)
        self.assertIn("geracao_programada_mwh", out.columns)
        self.assertIn("garantia_fisica_mwh", out.columns)
        self.assertIn("flag_missing_disponibilidade", out.columns)
        self.assertIn("flag_missing_dessem", out.columns)
        self.assertIn("flag_missing_garantia_fisica", out.columns)
        self.assertEqual(int(out.iloc[0]["flag_missing_disponibilidade"]), 1)
        self.assertEqual(int(out.iloc[0]["flag_missing_dessem"]), 1)
        self.assertEqual(int(out.iloc[0]["flag_missing_garantia_fisica"]), 1)


if __name__ == "__main__":
    unittest.main()
