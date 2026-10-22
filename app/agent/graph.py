"""Wires the agents into a LangGraph graph with a self-correcting retry loop.

    write_sql -> check_sql -> run_sql -> write_answer
                    |            |
                    +-- fails ---+--> fix_sql --> check_sql (again)

After settings.max_attempts failed tries, the graph stops retrying and
write_answer returns an honest "couldn't answer" message.
"""

from langgraph.graph import END, START, StateGraph

from app.agent.answer_writer import write_answer
from app.agent.sql_checker import check_sql
from app.agent.sql_fixer import fix_sql
from app.agent.sql_runner import run_sql
from app.agent.sql_writer import write_sql
from app.agent.state import AgentState
from app.config import settings


def next_step(state: AgentState) -> str:
    """Decide where to go after checking or running the SQL."""
    if not state.get("error"):
        return "ok"
    if state["attempts"] >= settings.max_attempts:
        return "give_up"
    return "retry"


def build_graph():
    """Create and compile the graph. Called once at import time."""
    graph = StateGraph(AgentState)

    graph.add_node("write_sql", write_sql)
    graph.add_node("check_sql", check_sql)
    graph.add_node("run_sql", run_sql)
    graph.add_node("fix_sql", fix_sql)
    graph.add_node("write_answer", write_answer)

    graph.add_edge(START, "write_sql")
    graph.add_edge("write_sql", "check_sql")
    graph.add_conditional_edges(
        "check_sql", next_step, {"ok": "run_sql", "retry": "fix_sql", "give_up": "write_answer"}
    )
    graph.add_conditional_edges(
        "run_sql", next_step, {"ok": "write_answer", "retry": "fix_sql", "give_up": "write_answer"}
    )
    graph.add_edge("fix_sql", "check_sql")
    graph.add_edge("write_answer", END)

    return graph.compile()


agent = build_graph()


def _to_response(state: AgentState) -> dict:
    """Pick the fields the API sends back to the UI from the final state."""
    return {
        "answer": state["answer"],
        "sql": state.get("sql", ""),
        "columns": state.get("columns", []),
        "rows": state.get("rows", []),
        "chart": state["chart"],
        "failed_attempts": state.get("failed_attempts", []),
        "success": not state.get("error"),
    }


def run_agent(question: str) -> dict:
    """Answer one question and return the final result (no live progress)."""
    state = agent.invoke({"question": question, "failed_attempts": []})
    return _to_response(state)


def stream_agent(question: str):
    """Answer one question, yielding progress events while the agent works.

    Yields {"type": "step", "message": ...} for each progress line, then
    one {"type": "result", "data": ...} at the end.

    stream_mode="custom" gives us the report_progress() messages;
    stream_mode="values" gives us the full state after each step (we keep the last).
    """
    state = {}
    for mode, chunk in agent.stream(
        {"question": question, "failed_attempts": []}, stream_mode=["custom", "values"]
    ):
        if mode == "custom":
            yield {"type": "step", "message": chunk["message"]}
        else:
            state = chunk
    yield {"type": "result", "data": _to_response(state)}
