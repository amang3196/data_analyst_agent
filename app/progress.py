"""Live progress messages, shown to the user while the agent works.

Any step can call report_progress("..."). When the graph is streamed
(see stream_agent in graph.py), these messages go straight to the UI.
"""

from langgraph.config import get_stream_writer


def report_progress(message: str) -> None:
    """Send one progress line to the UI. Does nothing outside a graph run."""
    try:
        get_stream_writer()({"message": message})
    except RuntimeError:  # called outside LangGraph, e.g. from a notebook
        pass
