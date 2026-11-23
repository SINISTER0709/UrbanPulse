import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings

logger = logging.getLogger("urbanpulse.db")

DEV_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "urbanpulse_dev.db"))


def create_app_engine():
    """
    Creates the SQLAlchemy engine.
    If PostgreSQL is configured but port 5432 is not currently reachable,
    gracefully falls back to a local SQLite database (sqlite:///./urbanpulse_dev.db)
    so development and testing can proceed seamlessly without blocking.
    """
    url = settings.DATABASE_URL
    connect_args = {}

    if "sqlite" in url:
        connect_args["check_same_thread"] = False
        return create_engine(url, pool_pre_ping=True, connect_args=connect_args)

    if "postgresql" in url:
        connect_args["connect_timeout"] = 2
        candidate_engine = create_engine(url, pool_pre_ping=True, connect_args=connect_args)
        try:
            with candidate_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Connected successfully to PostgreSQL database.")
            return candidate_engine
        except Exception as e:
            logger.warning(
                f"Notice: PostgreSQL at localhost:5432 is not reachable. "
                f"Falling back to local development database ({DEV_DB_PATH})."
            )
            return create_engine(
                f"sqlite:///{DEV_DB_PATH}",
                pool_pre_ping=True,
                connect_args={"check_same_thread": False}
            )

    return create_engine(url, pool_pre_ping=True)


engine = create_app_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    FastAPI dependency yielding a SQLAlchemy session per request.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
