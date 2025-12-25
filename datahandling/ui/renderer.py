from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from rich.text import Text
from rich.table import Table

console = Console()


def render_dataset_identity(dataset):
    """
    Global renderer for DatasetIdentity
    """

    header = Text()
    header.append("Dataset Scan Result\n", style="bold cyan")
    header.append(f"Path: {dataset.root}\n", style="dim")

    body = Tree("📦 Dataset")

    body.add(f"[bold green]Type[/bold green]: {dataset.container_type}")
    body.add(f"[bold green]Form[/bold green]: {dataset.structural_form}")

    details_node = body.add("[bold yellow]Details[/bold yellow]")
    render_details(details_node, dataset.details)

    panel = Panel(
        body,
        title="PPFlow",
        subtitle="Dataset Intelligence",
        border_style="cyan",
        padding=(1, 2),
    )

    console.print(header)
    console.print(panel)


def render_details(tree, details):
    """
    Recursively render ANY details dict
    """
    if not isinstance(details, dict):
        tree.add(str(details))
        return

    for key, value in details.items():
        key_style = "[bold magenta]"
        node = tree.add(f"{key_style}{key}[/bold magenta]")

        if isinstance(value, dict):
            render_details(node, value)

        elif isinstance(value, list):
            for item in value:
                node.add(f"[white]- {item}")

        else:
            node.add(f"[white]{value}")
