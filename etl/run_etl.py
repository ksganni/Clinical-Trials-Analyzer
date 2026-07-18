#!/usr/bin/env python3
"""Main ETL entry point: API -> PostgreSQL."""

from __future__ import annotations

import sys
import time

from etl.api_client import iter_studies
from etl.config import MAX_STUDIES
from etl.db import (
    count_rows,
    get_connection,
    init_schema,
    insert_child_rows,
    replace_child_rows,
    upsert_trial_rows,
)
from etl.transform import parse_study


def run_etl() -> None:
    print("=" * 60)
    print("Clinical Trials ETL")
    print("=" * 60)

    conn = get_connection()
    init_schema(conn)
    print("Database schema ready.")

    batch_trials: list[dict] = []
    batch_conditions: list[dict] = []
    batch_phases: list[dict] = []
    batch_locations: list[dict] = []
    batch_nct_ids: list[str] = []

    total = 0
    started = time.time()

    for study in iter_studies():
        parsed = parse_study(study)
        if not parsed["trials"]:
            continue

        batch_trials.extend(parsed["trials"])
        batch_conditions.extend(parsed["conditions"])
        batch_phases.extend(parsed["phases"])
        batch_locations.extend(parsed["locations"])
        batch_nct_ids.extend(row["nct_id"] for row in parsed["trials"])
        total += 1

        if len(batch_trials) >= 100:
            _flush_batch(conn, batch_trials, batch_conditions, batch_phases, batch_locations, batch_nct_ids)
            batch_trials, batch_conditions, batch_phases, batch_locations, batch_nct_ids = [], [], [], [], []
            print(f"  Loaded {total} studies...")

    _flush_batch(conn, batch_trials, batch_conditions, batch_phases, batch_locations, batch_nct_ids)

    elapsed = round(time.time() - started, 1)
    print("-" * 60)
    print(f"Done in {elapsed}s")
    print(f"  trials:     {count_rows(conn, 'trials')}")
    print(f"  conditions: {count_rows(conn, 'trial_conditions')}")
    print(f"  phases:     {count_rows(conn, 'trial_phases')}")
    print(f"  locations:  {count_rows(conn, 'trial_locations')}")
    if MAX_STUDIES > 0:
        print(f"  (limited to MAX_STUDIES={MAX_STUDIES} - increase in .env for more)")
    print("=" * 60)
    conn.close()

    # Also write CSVs under data/ for Tableau / sharing without live DB
    from etl.export_csv import export_all

    export_all()


def _flush_batch(
    conn,
    trials: list[dict],
    conditions: list[dict],
    phases: list[dict],
    locations: list[dict],
    nct_ids: list[str],
) -> None:
    if not trials:
        return
    upsert_trial_rows(conn, trials)
    for table, rows in [
        ("trial_conditions", conditions),
        ("trial_phases", phases),
        ("trial_locations", locations),
    ]:
        replace_child_rows(conn, table, nct_ids)
        insert_child_rows(conn, table, rows)


if __name__ == "__main__":
    try:
        run_etl()
    except Exception as exc:
        print(f"ETL failed: {exc}", file=sys.stderr)
        sys.exit(1)
