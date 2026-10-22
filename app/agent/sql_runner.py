"""Step - SQL Runner: runs the checked SQL on DuckDB. No LLM here.

A database error, or an empty result, counts as a failure so the SQL Fixer
gets a chance to correct the query.
"""

import json

import duckdb

from app.agent.state import AgentState
from app.db.database import run_query
from app.progress import report_progress


def run_sql(state: AgentState) -> AgentState:
    """Graph node: run the query and store the result, or record why it failed."""
    sql = state["sql"]
    try:
        df = run_query(sql)
    except duckdb.Error as e:  # any DuckDB error goes back to the fixer
        error = f"Database error: {e}"
        report_progress(f"Query failed: {str(e).splitlines()[0]}")
        return {"error": error, "failed_attempts": [{"sql": sql, "error": error}]}

    # An empty result is often a wrong filter (e.g. 'Canceled' vs 'canceled').
    # But if the fixer already sent this exact SQL back, we accept that it's truly empty.
    already_tried = any(a["sql"] == sql for a in state.get("failed_attempts", []))
    if df.empty and not already_tried:
        error = "The query returned no rows. Check filters and values; if empty is correct, return the same SQL."
        report_progress("Query returned no rows")
        return {"error": error, "failed_attempts": [{"sql": sql, "error": error}]}

    # to_json converts dates and numbers into plain JSON values the API can send
    report_progress(f"Results fetched ({len(df)} rows)")
    table = json.loads(df.to_json(orient="split", date_format="iso", index=False))
    return {"error": None, "columns": table["columns"], "rows": table["data"]}
