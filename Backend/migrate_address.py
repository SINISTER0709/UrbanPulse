import os
import sqlite3

db_paths = ["urbanpulse_dev.db", "backend/urbanpulse_dev.db"]
for db_path in db_paths:
    if not os.path.exists(db_path):
        continue
    print(f"Migrating {db_path}...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Check reports
    cur.execute("PRAGMA table_info(reports)")
    cols = [r[1] for r in cur.fetchall()]
    if "address" not in cols:
        cur.execute("ALTER TABLE reports ADD COLUMN address VARCHAR(255)")
        print(f"  Added address to {db_path} reports")

    # Check incidents
    cur.execute("PRAGMA table_info(incidents)")
    cols = [r[1] for r in cur.fetchall()]
    incident_cols = [
        ("address", "VARCHAR(255)"),
        ("summary_text", "TEXT"),
        ("severity", "VARCHAR(32) DEFAULT 'Medium'"),
        ("priority_score", "FLOAT DEFAULT 50.0"),
        ("urgent_review_flag", "BOOLEAN DEFAULT 0"),
        ("score_breakdown", "JSON"),
        ("image_verdict", "VARCHAR(64) DEFAULT 'Not Provided'"),
        ("data_source", "VARCHAR(64) DEFAULT 'user_submitted'"),
    ]
    for col_name, col_type in incident_cols:
        if col_name not in cols:
            cur.execute(f"ALTER TABLE incidents ADD COLUMN {col_name} {col_type}")
            print(f"  Added {col_name} to {db_path} incidents")

    # Update summary_text if null or empty from description
    if "description" in cols and "summary_text" in cols:
        cur.execute("UPDATE incidents SET summary_text = description WHERE summary_text IS NULL OR summary_text = ''")

    conn.commit()
    conn.close()
    print(f"Done migrating {db_path}")
