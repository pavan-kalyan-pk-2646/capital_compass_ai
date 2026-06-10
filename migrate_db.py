"""
migrate_db.py
--------------
Run this ONCE to upgrade your existing users.db portfolios table
from the old schema (missing stress_test, explanation, compliance columns)
to the new full schema required by Step 9.

Run from D:/paradise/:
    python migrate_db.py
"""

import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "users.db")

print(f"Connecting to: {DATABASE}")
conn = sqlite3.connect(DATABASE)
c    = conn.cursor()

# ── Check existing columns ─────────────────────────────────────────────
c.execute("PRAGMA table_info(portfolios)")
existing_cols = {row[1] for row in c.fetchall()}
print(f"Existing columns: {existing_cols}")

# ── Add missing columns (safe: only adds if they don't exist) ──────────
new_cols = {
    "stress_test": "TEXT",
    "explanation": "TEXT",
    "compliance":  "TEXT",
    "prediction":  "TEXT",   # Step 10 — market trend + suggestions + narrative
}

added = []
for col, col_type in new_cols.items():
    if col not in existing_cols:
        c.execute(f"ALTER TABLE portfolios ADD COLUMN {col} {col_type}")
        added.append(col)
        print(f"  ✓ Added column: {col}")
    else:
        print(f"  ✓ Column already exists: {col} (skipped)")

conn.commit()
conn.close()

if added:
    print(f"\n✅ Migration complete. Added {len(added)} column(s): {added}")
else:
    print("\n✅ Database already up to date. No changes needed.")