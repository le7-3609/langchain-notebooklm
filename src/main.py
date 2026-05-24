from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from src.agent import create_agent

console = Console()


def main() -> None:
    load_dotenv()

    console.print(Rule("[bold blue]NotebookLM Mini — Research Agent[/bold blue]"))
    topic = console.input("[bold yellow]Enter a topic to research:[/bold yellow] ").strip()
    if not topic:
        console.print("[red]No topic provided. Exiting.[/red]")
        return

    console.print(Panel(f"Researching: [bold]{topic}[/bold]", style="blue"))

    agent = create_agent()
    result = agent.invoke(
        {"messages": [{"role": "user", "content": f"Research the following topic and collect sources: {topic}"}]}
    )

    last_message = result["messages"][-1]
    console.print(Rule("[bold green]Sources Found[/bold green]"))
    console.print(last_message.content)


if __name__ == "__main__":
    main()
