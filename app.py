"""
NotebookLM Mini — Streamlit UI

Run with:
    streamlit run app.py
"""

import uuid

import streamlit as st
from dotenv import load_dotenv
from langgraph.types import Command

from src.graph import build_graph
from src.human_loop import extract_sources

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NotebookLM Mini",
    page_icon="🔍",
    layout="centered",
)

# ── Session-state initialisation ─────────────────────────────────────────────
_DEFAULTS: dict = {
    "graph": None,           # compiled LangGraph — built once per session
    "thread_id": None,       # unique ID per research run (checkpointer key)
    "phase": "idle",         # idle | researching | reviewing | resuming | done
    "chat": [],              # list[dict] — chat history shown in the UI
    "sources": [],           # list[dict] — parsed sources from agent
    "sources_text": "",      # raw agent output (shown in expander)
    "approved": [],          # sources the user approved
    "final_sources": [],     # confirmed after graph.invoke(Command(resume=...))
}

for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# Build graph only once per browser session (MemorySaver lives in graph.py module scope)
if st.session_state.graph is None:
    st.session_state.graph = build_graph()


# ── Helpers ───────────────────────────────────────────────────────────────────
def _add_message(role: str, content: str) -> None:
    st.session_state.chat.append({"role": role, "content": content})


def _reset() -> None:
    for k, v in _DEFAULTS.items():
        st.session_state[k] = v
    st.session_state.graph = build_graph()


# ── Header ────────────────────────────────────────────────────────────────────
st.title("🔍 NotebookLM Mini")
st.caption("Powered by LangGraph · Tavily · Groq")
st.divider()

# ── Render chat history ───────────────────────────────────────────────────────
for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ══════════════════════════════════════════════════════════════════════════════
# Phase: IDLE — waiting for the user to enter a topic
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.phase == "idle":
    topic = st.chat_input("What topic would you like to research?")
    if topic:
        _add_message("user", topic)
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.phase = "researching"
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# Phase: RESEARCHING — run the LangGraph agent until it hits interrupt()
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.phase == "researching":
    topic = next(m["content"] for m in reversed(st.session_state.chat) if m["role"] == "user")
    config = {"configurable": {"thread_id": st.session_state.thread_id}, "recursion_limit": 10}

    with st.chat_message("assistant"):
        with st.spinner(f"Researching **{topic}** — running web searches…"):
            st.session_state.graph.invoke(
                {"topic": topic, "sources_text": "", "approved_sources": []},
                config,
            )
            snapshot = st.session_state.graph.get_state(config)
            sources_text = snapshot.tasks[0].interrupts[0].value
            sources = extract_sources(sources_text)

        st.session_state.sources_text = sources_text
        st.session_state.sources = sources
        st.session_state.phase = "reviewing"

        n = len(sources)
        msg = (
            f"I found **{n} source{'s' if n != 1 else ''}** on **{topic}**.\n\n"
            "Please review and check the ones you'd like to keep, then click **Approve**."
        )
        st.markdown(msg)
        _add_message("assistant", msg)

    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# Phase: REVIEWING — HITL: show sources, let user approve / reject
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.phase == "reviewing":
    with st.expander("📄 Raw Research Findings", expanded=False):
        st.markdown(st.session_state.sources_text)

    st.subheader("Select sources to include")

    # Render a checkbox + title/link row for each source
    checked_sources: list[dict] = []
    for s in st.session_state.sources:
        col_cb, col_info = st.columns([1, 20], vertical_alignment="center")
        with col_cb:
            keep = st.checkbox("", value=True, key=f"src_{s['index']}", label_visibility="collapsed")
        with col_info:
            st.markdown(f"**{s['title']}**  \n[{s['url']}]({s['url']})")
        if keep:
            checked_sources.append(s)

    st.divider()
    col_approve, col_reject, _ = st.columns([2, 2, 6])

    with col_approve:
        approve_disabled = len(checked_sources) == 0
        if st.button("✅ Approve selected", type="primary", disabled=approve_disabled):
            st.session_state.approved = checked_sources
            st.session_state.phase = "resuming"
            st.rerun()

    with col_reject:
        if st.button("❌ Reject all"):
            _add_message("assistant", "No sources approved. Feel free to start a new search.")
            _reset()
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# Phase: RESUMING — send approved list back to the graph via Command(resume=...)
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.phase == "resuming":
    config = {"configurable": {"thread_id": st.session_state.thread_id}, "recursion_limit": 10}

    with st.chat_message("assistant"):
        with st.spinner("Saving your approved sources…"):
            final_state = st.session_state.graph.invoke(
                Command(resume=st.session_state.approved), config
            )

        approved = final_state.get("approved_sources", [])
        st.session_state.final_sources = approved
        st.session_state.phase = "done"

        lines = "\n".join(f"- [{s.get('title','Untitled')}]({s.get('url','')})" for s in approved)
        msg = f"✅ **Research complete!** {len(approved)} source(s) saved:\n\n{lines}"
        st.markdown(msg)
        _add_message("assistant", msg)

    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# Phase: DONE — show summary, offer to restart
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.phase == "done":
    st.divider()
    if st.button("🔄 Start new research", type="primary"):
        _reset()
        st.rerun()
