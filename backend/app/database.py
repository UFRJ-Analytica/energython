from app.config import get_settings

settings = get_settings()

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(settings.database_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    _database_init_error: Exception | None = None
except Exception as exc:  # permite rodar em modo mock sem deps de banco instaladas
    engine = None
    SessionLocal = None
    _database_init_error = exc


def get_db_session():
    if SessionLocal is None:
        if settings.data_backend == "postgres":
            detail = f": {_database_init_error}" if _database_init_error else ""
            raise RuntimeError(
                "DATA_BACKEND=postgres, mas a sessão SQLAlchemy não foi inicializada. "
                "Rode o backend com `uv run uvicorn app.main:app ...` a partir da pasta backend "
                "e confira se DATABASE_URL e as dependências sqlalchemy/psycopg estão disponíveis"
                f"{detail}"
            )
        yield None
        return
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
