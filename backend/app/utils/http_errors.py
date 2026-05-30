from __future__ import annotations

from fastapi import HTTPException


def api_error(status_code: int, code: str, detail: str, context: dict | None = None) -> HTTPException:
    payload = {"code": code, "detail": detail, "context": context or {}}
    return HTTPException(status_code=status_code, detail=payload)
