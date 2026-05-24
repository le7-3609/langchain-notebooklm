from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from src.tools import get_tools

# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert research assistant. Your sole task is to collect
high-quality internet sources about the topic given by the user.

Follow these rules strictly:
1. Run MULTIPLE targeted searches — vary the query wording to cover different angles
   (e.g. overview, recent news, expert opinion, official documentation).
2. Aim to discover at least 8-12 distinct, trustworthy sources.
3. Group the sources you find into 2-4 themed clusters (e.g. "Overview & Background",
   "Recent Developments", "Expert Analysis", "Official / Academic Sources").
4. For every source output exactly:
      Title      : <page title>
      URL        : <full URL>
      Description: <1-2 sentence snippet describing the content>
      Relevance  : <why this is useful for the topic>
5. Do NOT summarise the content — only collect and organise the sources.
6. After presenting all sources, ask the user to review and approve them."""


def create_agent():
    """Build and return the LangGraph ReAct research agent."""
    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
    tools = get_tools()
    agent = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)
    return agent
