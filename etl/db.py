"""Database helpers for PostgreSQL."""

from __future__ import annotations

from pathlib import Path

import psycopg2
from psycopg2.extras import execute_batch

from etl.config import DATABASE_URL


SQL_DIR = Path(__file__).resolve().parents[1] / "sql"


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def run_sql_file(conn, filename: str) -> None:
    sql = (SQL_DIR / filename).read_text()
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def init_schema(conn) -> None:
    run_sql_file(conn, "01_schema.sql")
    run_sql_file(conn, "02_analytics_views.sql")


def upsert_trial_rows(conn, rows: list[dict]) -> None:
    if not rows:
        return
    sql = """
        INSERT INTO trials (
            nct_id, brief_title, official_title, overall_status, study_type,
            sponsor_name, sponsor_class, start_date, primary_completion_date,
            completion_date, enrollment_count
        ) VALUES (
            %(nct_id)s, %(brief_title)s, %(official_title)s, %(overall_status)s,
            %(study_type)s, %(sponsor_name)s, %(sponsor_class)s, %(start_date)s,
            %(primary_completion_date)s, %(completion_date)s, %(enrollment_count)s
        )
        ON CONFLICT (nct_id) DO UPDATE SET
            brief_title = EXCLUDED.brief_title,
            official_title = EXCLUDED.official_title,
            overall_status = EXCLUDED.overall_status,
            study_type = EXCLUDED.study_type,
            sponsor_name = EXCLUDED.sponsor_name,
            sponsor_class = EXCLUDED.sponsor_class,
            start_date = EXCLUDED.start_date,
            primary_completion_date = EXCLUDED.primary_completion_date,
            completion_date = EXCLUDED.completion_date,
            enrollment_count = EXCLUDED.enrollment_count,
            updated_at = NOW()
    """
    with conn.cursor() as cur:
        execute_batch(cur, sql, rows, page_size=200)
    conn.commit()


def replace_child_rows(conn, table: str, nct_ids: list[str]) -> None:
    if not nct_ids:
        return
    with conn.cursor() as cur:
        cur.execute(f"DELETE FROM {table} WHERE nct_id = ANY(%s)", (nct_ids,))
    conn.commit()


def insert_child_rows(conn, table: str, rows: list[dict]) -> None:
    if not rows:
        return

    if table == "trial_conditions":
        columns = "(nct_id, condition)"
        values = "(%(nct_id)s, %(condition)s)"
    elif table == "trial_phases":
        columns = "(nct_id, phase)"
        values = "(%(nct_id)s, %(phase)s)"
    elif table == "trial_locations":
        columns = "(nct_id, country, city, state)"
        values = "(%(nct_id)s, %(country)s, %(city)s, %(state)s)"
    else:
        raise ValueError(f"Unknown table: {table}")

    sql = f"INSERT INTO {table} {columns} VALUES {values}"
    with conn.cursor() as cur:
        execute_batch(cur, sql, rows, page_size=500)
    conn.commit()


def count_rows(conn, table: str) -> int:
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        return cur.fetchone()[0]
