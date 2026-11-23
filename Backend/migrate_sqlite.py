import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "urbanpulse_dev.db")
print(f"Migrating SQLite DB for Stage E2 at: {db_path}")

conn = sqlite3.connect(db_path)
c = conn.cursor()

migrations = [
    ("incidents", "summary_text", "TEXT DEFAULT ''"),
    ("incidents", "severity", "VARCHAR(32) DEFAULT 'Medium'"),
    ("incidents", "priority_score", "DOUBLE PRECISION DEFAULT 50.0"),
    ("incidents", "urgent_review_flag", "BOOLEAN DEFAULT 0"),
    ("incidents", "score_breakdown", "JSON DEFAULT '{}'"),
    ("incidents", "image_verdict", "VARCHAR(64) DEFAULT 'Not Provided'"),
    ("admin_reviews", "incident_id", "VARCHAR(36)"),
    ("admin_reviews", "data_source", "VARCHAR(64) DEFAULT 'admin_portal'"),
    ("assignments", "data_source", "VARCHAR(64) DEFAULT 'admin_dispatch'"),
]

for table, col, typedef in migrations:
    try:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typedef};")
        print(f"Added {col} to {table}")
    except Exception as e:
        print(f"Notice on {table}.{col}: {e}")

try:
    c.execute("CREATE TABLE IF NOT EXISTS sensitive_pois AS SELECT * FROM pois WHERE 1=0;")
    c.execute("INSERT OR IGNORE INTO sensitive_pois SELECT * FROM pois;")
    c.execute("ALTER TABLE sensitive_pois ADD COLUMN poi_type VARCHAR(64);")
    c.execute("UPDATE sensitive_pois SET poi_type = category WHERE poi_type IS NULL;")
    print("Synchronized sensitive_pois table and added poi_type.")
except Exception as e:
    try:
        c.execute("UPDATE sensitive_pois SET poi_type = category WHERE poi_type IS NULL;")
    except Exception:
        pass
    print(f"Notice on sensitive_pois sync: {e}")

try:
    c.execute("""
    CREATE TABLE IF NOT EXISTS admin_reviews_v2 (
        id VARCHAR(36) PRIMARY KEY,
        report_id VARCHAR(36),
        incident_id VARCHAR(36),
        reviewer_user_id VARCHAR(36) NOT NULL,
        decision VARCHAR(32) NOT NULL,
        notes TEXT,
        data_source VARCHAR(64) DEFAULT 'admin_portal',
        reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    c.execute("""
    INSERT OR IGNORE INTO admin_reviews_v2 (id, report_id, incident_id, reviewer_user_id, decision, notes, data_source, reviewed_at)
    SELECT id, report_id, incident_id, reviewer_user_id, decision, notes, data_source, reviewed_at FROM admin_reviews;
    """)
    c.execute("DROP TABLE admin_reviews;")
    c.execute("ALTER TABLE admin_reviews_v2 RENAME TO admin_reviews;")
    print("Rebuilt admin_reviews with nullable report_id.")
except Exception as e:
    print(f"Notice on admin_reviews rebuild: {e}")

conn.commit()
conn.close()
print("Stage E2 migration completed successfully.")
