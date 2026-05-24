import re

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

console = Console()

# ── Regexes for the different formats the LLM may produce ────────────────────

# Format A — explicit labels:  "Title: ...\nURL: https://..."
_LABEL_URL_RE = re.compile(r"URL\s*:\s*(https?://\S+)", re.IGNORECASE)
_LABEL_TITLE_RE = re.compile(r"Title\s*:\s*(.+?)(?:\n|$)", re.IGNORECASE)

# Format B — numbered list:  '1. "Title" (https://...) - description'
_NUMBERED_RE = re.compile(
    r'\d+\.\s+"?([^"(\n]{3,100}?)"?\s*\n?\s*\((https?://[^\s)]{10,})\)',
    re.IGNORECASE,
)

# Format C — markdown links:  [Title](https://...)
_MD_LINK_RE = re.compile(r'\[([^\]]+)\]\((https?://[^\s)]+)\)')

# Format D — bare URLs (last resort)
_BARE_URL_RE = re.compile(r'https?://[^\s)>\]"\']{10,}')


def _clean_url(url: str) -> str:
    return url.rstrip(".,)>]\"'")


def _extract_sources(text: str) -> list[dict]:
    """
    Try four strategies in order of specificity.
    Returns as soon as one strategy finds results.
    """
    # Strategy A: explicit Title:/URL: labels
    urls = [_clean_url(u) for u in _LABEL_URL_RE.findall(text)]
    titles = [t.strip().strip("*_") for t in _LABEL_TITLE_RE.findall(text)]
    if urls:
        return [
            {"index": i + 1, "title": titles[i] if i < len(titles) else f"Source {i+1}", "url": u}
            for i, u in enumerate(urls)
        ]

    # Strategy B: numbered list  "Title" (URL)
    matches = _NUMBERED_RE.findall(text)
    if matches:
        return [
            {"index": i + 1, "title": t.strip(), "url": _clean_url(u)}
            for i, (t, u) in enumerate(matches)
        ]

    # Strategy C: markdown links [title](url)
    matches = _MD_LINK_RE.findall(text)
    if matches:
        return [
            {"index": i + 1, "title": t.strip(), "url": _clean_url(u)}
            for i, (t, u) in enumerate(matches)
        ]

    # Strategy D: bare URLs — use them as titles too
    urls = [_clean_url(u) for u in _BARE_URL_RE.findall(text)]
    return [{"index": i + 1, "title": f"Source {i + 1}", "url": u} for i, u in enumerate(urls)]


def show_and_collect_approvals(sources_text: str) -> list[dict]:
    """
    1. Print the raw research findings inside a panel.
    2. Parse sources and display a numbered table.
    3. Ask the user which sources to approve.
    Returns a list of approved source dicts.
    """
    console.print(
        Panel(sources_text, title="[bold cyan]Research Findings[/bold cyan]", expand=False)
    )

    sources = _extract_sources(sources_text)

    if not sources:
        console.print(
            "[red]Could not parse individual sources — no 'URL:' lines found in output.[/red]"
        )
        return []

    # ── Numbered table ──────────────────────────────────────────────────────
    table = Table(title="Discovered Sources", show_lines=True, expand=False)
    table.add_column("#", style="cyan", width=4, justify="right")
    table.add_column("Title", style="white", max_width=45)
    table.add_column("URL", style="blue", max_width=55)
    for s in sources:
        table.add_row(str(s["index"]), s["title"], s["url"])
    console.print(table)

    # ── Approval prompt ─────────────────────────────────────────────────────
    console.print(
        "\nEnter source numbers to [bold green]APPROVE[/bold green] "
        "(comma-separated, e.g. [cyan]1,3,4[/cyan]), "
        "[bold green]all[/bold green] to keep everything, "
        "or [bold red]none[/bold red] to reject all."
    )
    raw = Prompt.ask("[yellow]Your selection[/yellow]").strip().lower()

    if raw in ("all", ""):
        return sources
    if raw == "none":
        return []
    try:
        chosen = {int(n.strip()) for n in raw.split(",")}
        return [s for s in sources if s["index"] in chosen]
    except ValueError:
        console.print("[red]Could not parse input — approving all sources.[/red]")
        return sources
