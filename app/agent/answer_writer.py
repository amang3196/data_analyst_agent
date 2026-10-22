"""Agent 3 - Answer Writer: explains the result in plain English and picks a chart."""

from typing import Literal

from pydantic import BaseModel, Field

from app.agent.state import AgentState
from app.llm import ask_llm
from app.progress import report_progress

PROMPT = """You are a data analyst explaining a query result to a business user.

Question: {question}

SQL used:
{sql}

Result (first {shown} of {total} rows):
{preview}

1. Answer the question in 2-4 sentences. Use only numbers that appear in the result.
2. Pick the best chart:
   - "line" for a value over time
   - "bar" for comparing categories
   - "table" for a single number or many columns
   x and y must be column names from the result."""


class Answer(BaseModel):
    """The structured output we ask the LLM for."""

    summary: str = Field(description="2-4 sentence answer")
    chart_type: Literal["bar", "line", "table"]
    x: str | None = Field(default=None, description="column for the x-axis")
    y: str | None = Field(default=None, description="numeric column for the y-axis")


def write_answer(state: AgentState) -> AgentState:
    """Write the final answer, or an honest failure message if every try failed."""
    if state.get("error"):
        report_progress(f"Giving up after {state['attempts']} tries")
        message = (
            f"Sorry, I couldn't answer that after {state['attempts']} tries. "
            f"Last problem: {state['error']}"
        )
        return {"answer": message, "chart": {"type": "table"}}

    columns, rows = state["columns"], state["rows"]
    preview = "\n".join([", ".join(columns)] + [", ".join(map(str, r)) for r in rows[:20]])

    report_progress("Analysing results...")
    result = ask_llm(
        Answer,
        PROMPT.format(
            question=state["question"],
            sql=state["sql"],
            shown=min(20, len(rows)),
            total=len(rows),
            preview=preview,
        )
    )

    # Fall back to a table if the LLM named columns that don't exist
    chart = {"type": result.chart_type, "x": result.x, "y": result.y}
    if result.x not in columns or result.y not in columns:
        chart = {"type": "table"}
    return {"answer": result.summary, "chart": chart}
