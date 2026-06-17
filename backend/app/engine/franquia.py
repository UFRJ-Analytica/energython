from __future__ import annotations


def aplicar_franquia_eventos(eventos: list[dict], franquia_horas: float) -> list[dict]:
    """Aplica franquia anual apenas a eventos REL, preservando ordem temporal."""
    acumulado = 0.0
    out: list[dict] = []
    for ev in sorted(eventos, key=lambda x: x.get("timestamp") or ""):
        item = dict(ev)
        duracao = float(item.get("duracao_horas") or 1.0)
        energia = float(item.get("energia_restringida_mwh") or 0.0)
        razao = item.get("razao_classificada_ons")
        elegivel = bool(item.get("elegivel"))

        item["horas_acumuladas_antes"] = round(acumulado, 4)
        if not elegivel:
            item["status_franquia"] = "nao_aplicavel_inelegivel"
            item["status_franquia_label"] = "Não aplicável: evento inelegível"
            item["energia_ressarcivel_mwh"] = 0.0
            item["horas_acumuladas_depois"] = round(acumulado, 4)
            out.append(item)
            continue
        if razao != "REL":
            item["status_franquia"] = f"nao_aplicavel_{str(razao or 'indefinido').lower()}_termo"
            item["status_franquia_label"] = "Não consome franquia anual: compensação por termo/regramento específico fora da franquia REL"
            item["energia_ressarcivel_mwh"] = energia
            item["horas_acumuladas_depois"] = round(acumulado, 4)
            out.append(item)
            continue

        antes = acumulado
        depois = acumulado + duracao
        acumulado = depois
        item["horas_acumuladas_depois"] = round(depois, 4)
        if depois <= franquia_horas:
            item["status_franquia"] = "dentro_franquia"
            item["status_franquia_label"] = "Dentro da franquia anual REL"
            item["energia_ressarcivel_mwh"] = 0.0
        elif antes >= franquia_horas:
            item["status_franquia"] = "acima_franquia"
            item["status_franquia_label"] = "Acima da franquia anual REL"
            item["energia_ressarcivel_mwh"] = energia
        else:
            frac_acima = (depois - franquia_horas) / duracao if duracao > 0 else 0.0
            item["status_franquia"] = "parcialmente_franquia"
            item["status_franquia_label"] = "Parcialmente dentro da franquia anual REL"
            item["energia_ressarcivel_mwh"] = round(energia * frac_acima, 4)
        out.append(item)
    return out
