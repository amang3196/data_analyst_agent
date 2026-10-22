"""Everything that touches DuckDB: describing the schema and running queries.

The agent never hard-codes table names. It reads them from the database here,
so pointing DB_PATH at a different .duckdb file is enough to switch datasets.
"""

from functools import lru_cache
from pathlib import Path

import duckdb
import pandas as pd

from app.config import settings


def _connect() -> duckdb.DuckDBPyConnection:
    """Open the database read-only, so no query can ever change the data."""
    return duckdb.connect(settings.db_path, read_only=True)


@lru_cache
def get_schema() -> str:
    """Describe every table and column, plus the business notes, as text for prompts."""
    with _connect() as con:
        columns = con.execute(
            "SELECT table_name, column_name, data_type "
            "FROM information_schema.columns ORDER BY table_name, ordinal_position"
        ).fetchall()

    lines, current_table = [], None
    for table, column, data_type in columns:
        if table != current_table:
            lines.append(f"\nTable {table}:")
            current_table = table
        lines.append(f"  - {column} ({data_type})")

    notes_file = Path(settings.notes_path)
    notes = notes_file.read_text() if notes_file.exists() else ""
    return "\n".join(lines) + "\n\nBusiness notes:\n" + notes


def run_query(sql: str) -> pd.DataFrame:
    """Run a SELECT query and return at most settings.max_rows rows."""
    sql = sql.strip().rstrip(";")
    limited_sql = f"SELECT * FROM ({sql}) AS result LIMIT {settings.max_rows}"
    with _connect() as con:
        return con.execute(limited_sql).fetch_df()
