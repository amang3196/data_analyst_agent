"""FastAPI backend: a thin HTTP layer around the agent.

Run from the project root:
    uvicorn app.api.main:app --reload
Interactive docs: http://localhost:8000/docs
"""

import json
import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.agent.graph import run_agent, stream_agent

logger = logging.getLogger("uvicorn.error")
app = FastAPI(title="Data Analyst Agent")


class AskRequest(BaseModel):
    """What the UI sends."""

    question: str = Field(min_length=3, max_length=500)


class AskResponse(BaseModel):
    """What the UI gets back."""

    answer: str
    sql: str
    columns: list[str]
    rows: list[list]
    chart: dict
    failed_attempts: list[dict]
    success: bool


@app.get("/health")
def health() -> dict:
    """Simple check that the server is up."""
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    """Run the agent on one question and return the answer, data, chart and SQL."""
    try:
        return AskResponse(**run_agent(request.question))
    except Exception as e:  # e.g. a missing or invalid Gemini API key
        logger.exception("Agent failed")  # prints the full error in the API terminal
        raise HTTPException(status_code=500, detail=f"Agent failed: {e}") from e


@app.post("/ask/stream")
def ask_stream(request: AskRequest) -> StreamingResponse:
    """Same as /ask, but sends live progress while the agent works.

    The response is one JSON object per line (NDJSON):
        {"type": "step", "message": "SQL query generated"}
        ...
        {"type": "result", "data": {...same fields as /ask...}}
    or {"type": "error", "message": "..."} if the agent crashes.
    """

    def events():
        try:
            for event in stream_agent(request.question):
                yield json.dumps(event) + "\n"
        except Exception as e:  # report any crash to the UI
            logger.exception("Agent failed")
            yield json.dumps({"type": "error", "message": f"Agent failed: {e}"}) + "\n"

    return StreamingResponse(events(), media_type="application/x-ndjson")
