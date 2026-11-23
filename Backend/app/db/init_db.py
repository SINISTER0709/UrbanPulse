import logging
from sqlalchemy import text
from app.db.session import engine
from app.models.base import Base

logger = logging.getLogger(__name__)


def check_postgis(bind_engine=None) -> dict:
    """
    Verifies PostGIS extension availability and retrieves version information.
    """
    target_engine = bind_engine or engine
    try:
        with target_engine.connect() as conn:
            if "postgresql" in target_engine.dialect.name:
                version = conn.execute(text("SELECT PostGIS_Version();")).scalar()
                logger.info(f"PostGIS active. Version: {version}")
                return {"status": "available", "postgis_version": str(version), "spatial": True}
            else:
                return {"status": "available", "dialect": target_engine.dialect.name, "spatial": False}
    except Exception as e:
        logger.warning(f"Database/PostGIS check notification: {e}")
        return {"status": "unavailable", "error": str(e), "spatial": False}


def init_db(bind_engine=None):
    """
    Initializes all database tables and ensures PostGIS extension is enabled if running on PostgreSQL.
    """
    target_engine = bind_engine or engine
    if "postgresql" in target_engine.dialect.name:
        try:
            with target_engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
                conn.commit()
                logger.info("Ensured PostGIS extension is enabled in PostgreSQL.")
        except Exception as e:
            logger.warning(f"Notice enabling postgis extension (may already exist or need superuser): {e}")

    Base.metadata.create_all(bind=target_engine)
    logger.info("All UrbanPulse schema tables created successfully.")
