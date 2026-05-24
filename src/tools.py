from langchain_tavily import TavilySearch


def get_tools() -> list:
    """Return the list of tools available to the research agent."""
    search = TavilySearch(
        max_results=2,          # 2 results keeps each tool response ~2k tokens
        search_depth="basic",   # short snippets, stays within free-tier TPM
        include_answer=False,   # raw sources only
    )
    return [search]
