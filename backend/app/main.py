import subprocess
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine
from app.routers.debug import router as debug_router
from app.routers.financeiro import router as financeiro_router
from app.routers.pleito import router as pleito_router
from app.routers.regulatorio import router as regulatorio_router
from app.routers.usinas import router as usinas_router
from app.utils.logging_utils import configure_logging, request_logger_middleware
from app.utils.simple_cache import cache_registry_stats


def _git_hash() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


_BACK_BUILD_TIME = datetime.now(timezone.utc).isoformat()
_BACK_GIT_HASH = _git_hash()

settings = get_settings()
configure_logging()
app = FastAPI(title="CurtailIQ Backend", version="0.1.0")
request_logger_middleware(app)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def api_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if request.method != "GET" or response.status_code != 200:
        return response

    path = request.url.path
    if path == "/api/build-info" or path == "/api/cache/status":
        response.headers.setdefault("Cache-Control", "no-store")
        return response

    if path.startswith("/api/") and settings.api_http_cache_seconds > 0:
        max_age = int(settings.api_http_cache_seconds)
        stale = max(0, int(settings.api_http_stale_while_revalidate_seconds))
        response.headers.setdefault(
            "Cache-Control",
            f"public, max-age={max_age}, stale-while-revalidate={stale}",
        )
        response.headers.setdefault("Vary", "Origin")
    return response

app.include_router(usinas_router)
app.include_router(financeiro_router)
app.include_router(regulatorio_router)
app.include_router(pleito_router)
app.include_router(debug_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/build-info")
def build_info():
    return {
        "git_hash": _BACK_GIT_HASH,
        "build_time": _BACK_BUILD_TIME,
    }


@app.get("/api/cache/status")
def cache_status():
    return {
        "cache_enabled": settings.cache_enabled,
        "caches": cache_registry_stats(),
    }


@app.get("/readiness")
def readiness():
    if settings.data_backend == "postgres":
        if engine is None:
            return {
                "status": "not_ready",
                "data_backend": "postgres",
                "checks": {"db_connection": "driver_or_engine_unavailable"},
            }
        try:
            with engine.connect() as conn:
                conn.exec_driver_sql("SELECT 1")
            return {
                "status": "ready",
                "data_backend": "postgres",
                "checks": {"db_connection": "ok"},
            }
        except Exception:
            return {
                "status": "not_ready",
                "data_backend": "postgres",
                "checks": {"db_connection": "error"},
            }
    return {
        "status": "ready",
        "data_backend": "mock",
        "checks": {"mock_repository": "ok"},
    }
