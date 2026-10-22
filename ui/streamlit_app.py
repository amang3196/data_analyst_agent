"""Streamlit chat UI. It only talks to the FastAPI backend over HTTP.

Run from the project root (with the API already running):
    streamlit run ui/streamlit_app.py
"""

import json
import os

import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

EXAMPLES = [
    "Top 5 product categories by revenue in 2018",
    "How many orders were placed each month in 2017?",
    "Which 10 states have the most customers?",
    "What is the average review score by product category? Show the lowest 10.",
    "What share of payments use each payment type?",
]


def stream_api(question: str):
    """Send the question to the backend and yield its events as they arrive."""
    url = f"{API_URL}/ask/stream"
    with requests.post(url, json={"question": question}, stream=True, timeout=180) as response:
        if not response.ok:
            raise RuntimeError(f"API error {response.status_code}: {response.text}")
        for line in response.iter_lines():
            if line:
                yield json.loads(line)


def show_steps(steps: list[str], running: bool = False):
    """Show the agent's progress as a collapsible checklist."""
    label = "Working on it..." if running else f"Done in {len(steps)} steps"
    box = st.status(label, expanded=running, state="running" if running else "complete")
    for step in steps:
        box.write(f"- {step}")
    return box


def show_result(result: dict) -> None:
    """Draw one answer: text, chart, table, SQL and any failed attempts."""
    st.markdown(result["answer"])

    df = pd.DataFrame(result["rows"], columns=result["columns"])
    chart = result["chart"]
    if chart["type"] in ("bar", "line") and not df.empty:
        data = df.set_index(chart["x"])[chart["y"]]
        if chart["type"] == "bar":
            st.bar_chart(data)
        else:
            st.line_chart(data)

    if not df.empty:
        st.dataframe(df, hide_index=True)

    if result["sql"]:
        with st.expander("SQL used"):
            st.code(result["sql"], language="sql")

    if result["failed_attempts"]:
        with st.expander(f"Self-corrections ({len(result['failed_attempts'])})"):
            for i, attempt in enumerate(result["failed_attempts"], start=1):
                st.markdown(f"**Try {i} failed:** {attempt['error']}")
                st.code(attempt["sql"], language="sql")


st.set_page_config(page_title="Data Analyst Agent", layout="wide")
st.title("Data Analyst Agent")
st.caption("Ask a question about the Olist e-commerce data. The agent writes the SQL, runs it and fixes its own mistakes.")

if "messages" not in st.session_state:
    st.session_state.messages = []  # list of {"role", "content" or "result"}

# Sidebar: click an example to ask it
clicked = None
with st.sidebar:
    st.header("Try an example")
    for example in EXAMPLES:
        if st.button(example, width="stretch"):
            clicked = example

# Replay the conversation so far
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["content"])
        else:
            show_steps(message["steps"])
            show_result(message["result"])

question = st.chat_input("Ask a business question...") or clicked
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        steps, result = [], None
        box = show_steps(steps, running=True)
        try:
            for event in stream_api(question):
                if event["type"] == "step":
                    steps.append(event["message"])
                    box.write(f"- {event['message']}")  # appears live
                elif event["type"] == "result":
                    result = event["data"]
                else:  # "error"
                    raise RuntimeError(event["message"])
        except (requests.RequestException, RuntimeError) as e:
            box.update(label="Failed", state="error")
            st.error(str(e))
            st.stop()

        box.update(label=f"Done in {len(steps)} steps", state="complete", expanded=False)
        show_result(result)
    st.session_state.messages.append({"role": "assistant", "steps": steps, "result": result})
