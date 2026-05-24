from typing_extensions import TypedDict


class ResearchState(TypedDict):
    topic: str
    sources_text: str       # raw research output from the ReAct agent
    approved_sources: list  # user-approved sources after Human-in-the-Loop
