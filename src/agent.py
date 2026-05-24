from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from src.tools import get_tools

# ── System Prompt ─────────────────────────────────────────────────────────────
# Kept intentionally short — every token here is repeated on every LLM call.
SYSTEM_PROMPT = (
    "You are a research assistant. Your job is to find internet sources about "
    "the user's topic.\n"
    "Rules:\n"
    "1. Run 2-3 different searches using varied query wording.\n"
    "2. For each source list: Title, URL, one-sentence description, relevance.\n"
    "3. Group results into 2-3 themes.\n"
    "4. Do NOT summarise content — only collect sources."
)


def create_agent():
    """Build and return the LangGraph ReAct research agent."""
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)  # 12k TPM free tier
    tools = get_tools()
    agent = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)
    return agent
