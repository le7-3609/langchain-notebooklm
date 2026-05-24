import uuid

from dotenv import load_dotenv
from langgraph.types import Command
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from src.graph import build_graph
from src.human_loop import show_and_collect_approvals

console = Console()


def main() -> None:
    load_dotenv()

    console.print(Rule("[bold blue]NotebookLM Mini — Research Agent[/bold blue]"))
    topic = console.input("[bold yellow]Enter a topic to research:[/bold yellow] ").strip()
    if not topic:
        console.print("[red]No topic provided. Exiting.[/red]")
        return

    console.print(Panel(f"Researching: [bold]{topic}[/bold]", style="blue"))

    graph = build_graph()
    # Each run gets its own thread so the checkpointer keeps its state isolated
    config = {
        "configurable": {"thread_id": str(uuid.uuid4())},
        "recursion_limit": 10,
    }

    # ── Phase 1: Research ────────────────────────────────────────────────────
    # The graph runs the research node, then hits interrupt() inside human_review.
    # invoke() returns the state snapshot at the point of interruption.
    graph.invoke(
        {"topic": topic, "sources_text": "", "approved_sources": []},
        config,
    )

    # ── Phase 2: Human-in-the-Loop ───────────────────────────────────────────
    # get_state() reveals whether the graph is paused and exposes interrupt values.
    snapshot = graph.get_state(config)
    if not snapshot.next:
        console.print("[red]Graph finished without reaching the review step.[/red]")
        return

    # tasks[0].interrupts[0].value is the sources_text passed to interrupt()
    sources_text = snapshot.tasks[0].interrupts[0].value
    approved = show_and_collect_approvals(sources_text)

    if not approved:
        console.print("[yellow]No sources approved. Exiting.[/yellow]")
        return

    console.print(
        Panel(f"[green]✓ {len(approved)} source(s) approved[/green]", style="green")
    )

    # ── Phase 3: Resume graph with the approved list ─────────────────────────
    # Command(resume=...) unfreezes the graph; approved is received by interrupt()
    # as its return value inside _human_review_node.
    final_state = graph.invoke(Command(resume=approved), config)

    console.print(Rule("[bold green]Approved Sources[/bold green]"))
    for s in final_state.get("approved_sources", []):
        console.print(
            f"  • [bold white]{s.get('title', 'Untitled')}[/bold white]  "
            f"[blue]{s.get('url', '')}[/blue]"
        )


if __name__ == "__main__":
    main()
