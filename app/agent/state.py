"""The shared state that flows through the LangGraph graph.

Each step (node) reads what it needs from the state and returns only the
fields it changes. LangGraph merges those changes into the state.
"""

import operator
from typing import Annotated, TypedDict


class Attempt(TypedDict):
    """One failed SQL try and why it failed. Shown in the UI."""

    sql: str
    error: str


class AgentState(TypedDict, total=False):
    """Everything the agent knows during one question."""

    question: str  # the user's question
    sql: str  # the current SQL query
    error: str | None  # why the current SQL failed (None = no problem)
    attempts: int  # how many SQL queries have been tried so far

    # operator.add means "append": nodes return [new_attempt] and it is added to the list
    failed_attempts: Annotated[list[Attempt], operator.add]

    columns: list[str]  # result column names
    rows: list[list]  # result rows

    answer: str  # the final text answer
    chart: dict  # {"type": "bar" | "line" | "table", "x": column, "y": column}
