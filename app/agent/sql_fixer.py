"""Agent 2 - SQL Fixer: reads why the last query failed and rewrites it."""

from app.agent.sql_writer import SQLQuery
from app.agent.state import AgentState
from app.db.database import get_schema
from app.llm import ask_llm
from app.progress import report_progress

PROMPT = """You are an expert data analyst fixing a DuckDB SQL query.

Database schema:
{schema}

Question: {question}

This query failed:
{sql}

Error:
{error}

Return a corrected single SELECT query that answers the question."""


def fix_sql(state: AgentState) -> AgentState:
    """Ask the LLM to repair the SQL using the error message."""
    report_progress(f"Fixing the query (try {state['attempts'] + 1})...")
    prompt = PROMPT.format(
        schema=get_schema(),
        question=state["question"],
        sql=state["sql"],
        error=state["error"],
    )
    result = ask_llm(SQLQuery, prompt)
    return {"sql": result.sql, "attempts": state["attempts"] + 1, "error": None}
