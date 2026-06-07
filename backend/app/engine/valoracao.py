from __future__ import annotations


def valorar_evento(energia_ressarcivel_mwh: float, pld_reais_mwh: float, contratos: list[dict] | None = None) -> dict:
    valor = float(energia_ressarcivel_mwh or 0.0) * float(pld_reais_mwh or 0.0)
    destinatario = "Agente gerador (parcela não contratada — assumido; confirmar situação contratual)"
    if contratos:
        tipo = str(contratos[0].get("tipo_contrato") or "").upper()
        if tipo == "CCEAR_DISPONIBILIDADE":
            destinatario = "Distribuidora compradora vinculada ao CCEAR por Disponibilidade"
        elif tipo == "CER":
            destinatario = "CONER, conforme contrato CER informado"
    return {
        "valor_pleitavel_reais": round(valor, 2),
        "pld_usado_reais_mwh": round(float(pld_reais_mwh or 0.0), 4),
        "destinatario_do_ressarcimento": destinatario,
        "fonte_valoracao": "CCEE/PLD horário; contratos manuais quando disponíveis",
    }
