from __future__ import annotations


def reconciliar_evento(evento: dict, clima_ons: dict | None = None, dados_proprios: dict | None = None) -> dict:
    if not dados_proprios:
        return {
            "houve_comparacao": False,
            "divergencia_significativa": False,
            "argumento_tecnico": "Reconciliação com dados próprios não realizada; rascunho reserva direito de complementação probatória.",
        }

    vento_ons = float((clima_ons or {}).get("vento_ms") or 0.0)
    vento_prop = float(dados_proprios.get("vento_ms_proprio") or 0.0)
    delta_rel = ((vento_prop - vento_ons) / vento_ons) if vento_ons else 0.0
    ger_ref = float(evento.get("geracao_referencia_mwh") or 0.0)
    ger_recalc = ger_ref * (1 + max(delta_rel, 0.0))
    delta_ger = ger_recalc - ger_ref
    significativa = abs(delta_rel) >= 0.10 or abs(delta_ger) >= 1.0
    return {
        "houve_comparacao": True,
        "divergencia_significativa": significativa,
        "vento_ons_ms": round(vento_ons, 4),
        "vento_proprio_ms": round(vento_prop, 4),
        "delta_vento_relativo": round(delta_rel, 4),
        "geracao_referencia_recalculada_mwh": round(ger_recalc, 4),
        "delta_geracao_referencia_mwh": round(delta_ger, 4),
        "argumento_tecnico": (
            f"Dados próprios indicam variação de vento de {delta_rel:.1%} frente ao dado ONS, "
            f"com impacto estimado de {delta_ger:.2f} MWh na geração de referência."
        ),
        "fonte_dados_proprios": dados_proprios.get("fonte_dado") or "dados próprios informados pelo agente",
    }
