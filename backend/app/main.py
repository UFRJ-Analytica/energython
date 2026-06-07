from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine
from app.routers.financeiro import router as financeiro_router
from app.routers.pleito import router as pleito_router
from app.routers.regulatorio import router as regulatorio_router
from app.routers.usinas import router as usinas_router
from app.utils.logging_utils import configure_logging, request_logger_middleware

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

app.include_router(usinas_router)
app.include_router(financeiro_router)
app.include_router(regulatorio_router)
app.include_router(pleito_router)


@app.get("/health")
def health():
    return {"status": "ok"}


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
