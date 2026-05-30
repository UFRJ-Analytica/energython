from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class BaseRepository(ABC):
    @abstractmethod
    def list_usinas(self, fonte: str | None = None, submercado: str | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_usina(self, usina_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def get_constrained_off(self, usina_id: str, inicio: datetime, fim: datetime) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_pld(self, submercado: str, inicio: datetime, fim: datetime) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_geracao_horaria(self, usina_id: str, inicio: datetime, fim: datetime) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_clima_horario(
        self,
        usina_id: str,
        inicio: datetime,
        fim: datetime,
        is_forecast: bool | None = None,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_disponibilidade_usina(self, usina_id: str, inicio: datetime, fim: datetime) -> list[dict[str, Any]]:
        """Série temporal de disponibilidade/TEIFa/TEIP da usina (quando existir no gold)."""
        raise NotImplementedError

    @abstractmethod
    def get_despacho_dessem(self, usina_id: str, inicio: datetime, fim: datetime) -> list[dict[str, Any]]:
        """Série temporal de despacho programado (DESSEM) por usina (quando existir no gold)."""
        raise NotImplementedError

    @abstractmethod
    def get_garantia_fisica(self, usina_id: str, inicio: datetime, fim: datetime) -> list[dict[str, Any]]:
        """Série temporal de garantia física/sazonalização da usina (quando existir no gold)."""
        raise NotImplementedError
