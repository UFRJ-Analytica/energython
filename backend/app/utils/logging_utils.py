from __future__ import annotations

import json
import logging
import time
from typing import Callable

from fastapi import Request


def configure_logging(level: int = logging.INFO):
    logging.basicConfig(level=level, format="%(message)s")


def log_json(event: str, **kwargs):
    payload = {"event": event, **kwargs}
    logging.getLogger("curtailiq").info(json.dumps(payload, ensure_ascii=False))


def request_logger_middleware(app):
    @app.middleware("http")
    async def _log_requests(request: Request, call_next: Callable):
        start = time.time()
        response = await call_next(request)
        elapsed_ms = round((time.time() - start) * 1000, 2)
        log_json(
            "http_request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            elapsed_ms=elapsed_ms,
        )
        return response
