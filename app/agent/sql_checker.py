"""Guard - SQL Checker: makes sure the SQL is safe before it runs. No LLM here.

We parse the SQL with sqlglot (a real SQL parser) instead of searching the text,
so tricks like comments or odd spacing can't sneak a DELETE through.
"""

import sqlglot
from sqlglot import exp

from app.agent.state import AgentState
from app.progress import report_progress

# Statement types that change data or the database
BLOCKED_STATEMENTS = (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create, exp.Alter, exp.Command)

# DuckDB functions that can read files on disk
BLOCKED_FUNCTIONS = {"read_csv", "read_csv_auto", "read_parquet", "read_json", "read_json_auto", "read_text", "read_blob", "glob"}


def find_problem(sql: str) -> str | None:
    """Return a reason the SQL is unsafe or invalid, or None if it is fine."""
    try:
        statements = sqlglot.parse(sql, read="duckdb")
    except sqlglot.errors.ParseError as e:
        return f"SQL syntax error: {e}"

    statements = [s for s in statements if s is not None]
    if len(statements) != 1:
        return "Exactly one SQL statement is allowed."

    query = statements[0]
    if not isinstance(query, (exp.Select, exp.SetOperation)):
        return "Only SELECT queries are allowed."

    for node in query.walk():
        if isinstance(node, BLOCKED_STATEMENTS):
            return f"Not allowed: {node.key.upper()}"
        if isinstance(node, exp.Func):
            name = (node.name if isinstance(node, exp.Anonymous) else node.sql_name()).lower()
            if name in BLOCKED_FUNCTIONS:
                return f"Not allowed: function {name}"
    return None


def check_sql(state: AgentState) -> AgentState:
    """Graph node: record an error (and a failed attempt) if the SQL is not safe."""
    problem = find_problem(state["sql"])
    if problem:
        report_progress(f"Safety check failed: {problem}")
        return {"error": problem, "failed_attempts": [{"sql": state["sql"], "error": problem}]}
    report_progress("Safety check passed")
    return {"error": None}
