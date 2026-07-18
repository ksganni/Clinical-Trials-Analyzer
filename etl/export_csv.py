"""Export core PostgreSQL tables to CSV files under data/."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from etl.db import get_connection

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

# Core collected data only (not analytics views)
EXPORTS: list[tuple[str, str]] = [
    ("trials", "trials.csv"),
    ("trial_conditions", "trial_conditions.csv"),
    ("trial_phases", "trial_phases.csv"),
    ("trial_locations", "trial_locations.csv"),
]


def export_relation(conn, relation: str, dest: Path) -> int:
    with conn.cursor() as cur:
        cur.execute(f"SELECT * FROM {relation}")
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()

    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)
    return len(rows)


def export_all() -> None:
    print("=" * 60)
    print("Exporting clinical trials data → data/")
    print("=" * 60)

    conn = get_connection()
    total_files = 0
    try:
        for relation, filename in EXPORTS:
            dest = DATA_DIR / filename
            count = export_relation(conn, relation, dest)
            print(f"  {filename:40s} {count:>8,} rows")
            total_files += 1
    finally:
        conn.close()

    print("-" * 60)
    print(f"Wrote {total_files} CSV files to {DATA_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        export_all()
    except Exception as exc:
        print(f"Export failed: {exc}", file=sys.stderr)
        sys.exit(1)
