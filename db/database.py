
from __future__ import annotations
from pathlib import Path
import sqlite3
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "reconpilot.db"
SCHEMA_PATH = ROOT / "db" / "schema.sql"

def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    # Demo merchant
    conn.execute(
        """INSERT OR IGNORE INTO merchants(merchant_id,name,created_at)
           VALUES(?,?,?)""",
        ("merchant_demo", "ReconPilot Demo Merchant", now())
    )
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Initialized {DB_PATH}")
