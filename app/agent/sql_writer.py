"""Agent 1 - SQL Writer: turns the user's question into a DuckDB SQL query."""

from pydantic import BaseModel, Field

from app.agent.state import AgentState
from app.db.database import get_schema
from app.llm import ask_llm
from app.progress import report_progress

PROMPT = """You are an expert data analyst writing DuckDB SQL.

Database schema:
{schema}

Write ONE read-only SELECT query that answers the question.
- Use only the tables and columns listed above.
- Follow the business notes exactly.
- Give result columns short, readable names with AS.
- Round money and averages to 2 decimals.
- Add ORDER BY so the most important rows come first.

Question: {question}"""


class SQLQuery(BaseModel):
    """The structured output we ask the LLM for."""

    sql: str = Field(description="A single DuckDB SELECT query, no markdown")


def write_sql(state: AgentState) -> AgentState:
    """Ask the LLM for a first SQL query."""
    prompt = PROMPT.format(schema=get_schema(), question=state["question"])
    result = ask_llm(SQLQuery, prompt)
    report_progress("SQL query generated")
    return {"sql": result.sql, "attempts": 1, "error": None}
