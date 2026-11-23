"""
UrbanPulse Database Initialization and PostGIS Checker CLI.
"""
import sys
import logging
from app.db.session import engine
from app.db.init_db import init_db, check_postgis

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("db_init")

def main():
    logger.info("=" * 60)
    logger.info("UrbanPulse AI Platform - Database & PostGIS Setup")
    logger.info("=" * 60)

    # 1. Check PostGIS extension and database reachability
    logger.info(f"Checking connection to: {engine.url.render_as_string(hide_password=True)}")
    pg_status = check_postgis()
    logger.info(f"PostGIS Status: {pg_status}")

    # 2. Initialize all tables
    logger.info("Creating UrbanPulse core schema tables...")
    try:
        init_db()
        logger.info("Table creation completed successfully.")
    except Exception as e:
        logger.error(f"Error initializing schema: {e}")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("Database initialization complete.")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
