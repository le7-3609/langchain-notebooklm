from langchain_tavily import TavilySearch


def get_tools() -> list:
    """Return the list of tools available to the research agent."""
    search = TavilySearch(
        max_results=4,          # fewer results → fewer tokens per query
        search_depth="basic",   # shorter snippets, well within free-tier TPM
        include_answer=False,    # we want raw sources, not a pre-baked answer
    )
    return [search]
