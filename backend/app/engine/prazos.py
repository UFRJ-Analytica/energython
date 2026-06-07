from __future__ import annotations

from datetime import date, datetime, timedelta


def janela_pleito(timestamp: datetime, hoje: date | None = None) -> dict:
    hoje = hoje or date.today()
    data_evento = timestamp.date()
    dias_decorridos = (hoje - data_evento).days
    dias_restantes = 90 - dias_decorridos
    sager_restantes = 3 - dias_decorridos
    termo_inicio = date(2023, 9, 1)
    termo_fim = date(2025, 11, 25)
    return {
        "data_referencia_hoje": hoje.isoformat(),
        "dias_restantes_protocolo_ons": dias_restantes,
        "pode_pleitear_protocolo_ons": dias_restantes >= 0,
        "elegivel_termo": termo_inicio <= data_evento <= termo_fim,
        "janela_adesao_termo": "parametrizavel_regulamentacao_mme_ccee",
        "sager_dias_restantes": sager_restantes,
        "sager_informativo": sager_restantes >= 0,
    }
