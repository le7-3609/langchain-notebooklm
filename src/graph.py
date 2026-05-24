from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt

from src.agent import create_agent
from src.state import ResearchState

# Single MemorySaver instance — persists graph state across interrupt / resume cycles
_checkpointer = MemorySaver()


def _research_node(state: ResearchState) -> dict:
    """Run the ReAct research agent and store the findings as text."""
    agent = create_agent()
    result = agent.invoke(
        {"messages": [{"role": "user", "content": f"Research the following topic and collect sources: {state['topic']}"}]},
        {"recursion_limit": 8},
    )
    last_msg = result["messages"][-1]
    return {"sources_text": last_msg.content}


def _human_review_node(state: ResearchState) -> dict:
    """
    Pause the graph here (Human-in-the-Loop).

    interrupt() saves the current state to the checkpointer and surfaces
    `sources_text` back to the caller.  Execution resumes from this exact
    point when graph.invoke(Command(resume=<approved>), config) is called.
    """
    approved = interrupt(state["sources_text"])
    return {"approved_sources": approved}


def build_graph():
    """Compile and return the full research + HITL graph."""
    builder = StateGraph(ResearchState)
    builder.add_node("research", _research_node)
    builder.add_node("human_review", _human_review_node)

    builder.add_edge(START, "research")
    builder.add_edge("research", "human_review")
    builder.add_edge("human_review", END)

    return builder.compile(checkpointer=_checkpointer)
