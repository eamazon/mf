"""Rich terminal display for fund analysis results."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich import box

from .explain import METRIC_EXPLANATIONS, format_value, explain

console = Console()

# Metrics to show in the summary table
SUMMARY_METRICS = [
    "cagr_1y", "cagr_3y", "cagr_5y", "sharpe", "sortino",
    "volatility", "max_drawdown", "consistency", "beta", "alpha",
    "expense_ratio", "composite_score",
]


def display_fund_card(fund: dict) -> None:
    """Display a single fund as a detailed card."""
    name = fund.get("scheme_name", "Unknown")
    score = fund.get("composite_score", 0)
    label = fund.get("score_label", "N/A")

    # Score color
    if score >= 80:
        score_color = "green"
    elif score >= 65:
        score_color = "cyan"
    elif score >= 50:
        score_color = "yellow"
    else:
        score_color = "red"

    # Header info
    header = Text()
    header.append(f"  Score: ", style="bold")
    header.append(f"{score:.0f}/100 ({label})", style=f"bold {score_color}")
    header.append(f"  |  Fund House: {fund.get('fund_house', 'N/A')}")
    header.append(f"  |  Category: {fund.get('category', 'N/A')}")
    fm = fund.get("fund_manager", "N/A")
    if fm and fm != "N/A":
        header.append(f"  |  Manager: {fm}")

    # Metrics grid
    grid = Table(show_header=True, box=box.SIMPLE, padding=(0, 2))
    grid.add_column("Metric", style="bold", min_width=22)
    grid.add_column("Value", min_width=10, justify="right")
    grid.add_column("What it means", style="dim", min_width=40)

    for metric in SUMMARY_METRICS:
        val = fund.get(metric)
        if val is None:
            continue
        info = METRIC_EXPLANATIONS.get(metric, {})
        grid.add_row(
            info.get("name", metric),
            _colored_value(metric, val),
            info.get("short", ""),
        )

    panel = Panel(
        grid,
        title=f"[bold]{name}[/bold]",
        subtitle=header,
        border_style=score_color,
        padding=(1, 2),
    )
    console.print(panel)
    console.print()


def display_comparison_table(funds: list[dict], title: str = "Fund Comparison") -> None:
    """Display multiple funds side by side in a ranking table."""
    if not funds:
        console.print("[yellow]No funds to display.[/yellow]")
        return

    table = Table(
        title=f"[bold]{title}[/bold]",
        box=box.ROUNDED,
        show_lines=True,
        padding=(0, 1),
    )
    table.add_column("#", style="bold", width=3, justify="center")
    table.add_column("Fund Name", min_width=30, max_width=45)
    table.add_column("Score", justify="center", min_width=8)
    table.add_column("3Y Return", justify="right")
    table.add_column("5Y Return", justify="right")
    table.add_column("Sharpe", justify="right")
    table.add_column("Volatility", justify="right")
    table.add_column("Max DD", justify="right")
    table.add_column("Consistency", justify="right")

    for i, fund in enumerate(funds, 1):
        score = fund.get("composite_score", 0)
        label = fund.get("score_label", "")

        table.add_row(
            str(i),
            _truncate(fund.get("scheme_name", ""), 45),
            _colored_value("composite_score", score),
            _colored_value("cagr_3y", fund.get("cagr_3y")),
            _colored_value("cagr_5y", fund.get("cagr_5y")),
            _colored_value("sharpe", fund.get("sharpe")),
            _colored_value("volatility", fund.get("volatility")),
            _colored_value("max_drawdown", fund.get("max_drawdown")),
            _colored_value("consistency", fund.get("consistency")),
        )

    console.print(table)
    console.print()


def display_category_recommendations(all_results: dict[str, list[dict]]) -> None:
    """Display recommendations grouped by category."""
    for category, funds in all_results.items():
        if not funds:
            continue
        display_comparison_table(funds, title=f"Top Picks: {category}")


def display_metric_guide() -> None:
    """Display the metric learning guide."""
    console.print()
    console.print("[bold]Mutual Fund Metrics Guide[/bold]", style="underline")
    console.print()
    console.print(
        "These are the key numbers that help you evaluate a mutual fund. "
        "No financial jargon - just plain English.\n"
    )

    # Group metrics
    groups = {
        "Performance (How much money did it make?)": [
            "cagr_1y", "cagr_3y", "cagr_5y", "consistency",
        ],
        "Risk (How bumpy is the ride?)": [
            "volatility", "sharpe", "sortino", "max_drawdown",
        ],
        "Market Relationship": [
            "beta", "alpha",
        ],
        "Cost & Size": [
            "expense_ratio", "aum",
        ],
        "Overall": [
            "composite_score",
        ],
    }

    for group_name, metrics in groups.items():
        console.print(f"\n[bold cyan]{group_name}[/bold cyan]")
        console.print("-" * 60)
        for m in metrics:
            info = METRIC_EXPLANATIONS.get(m)
            if not info:
                continue
            console.print(f"\n  [bold]{info['name']}[/bold]")
            console.print(f"  {info['detail']}")
            console.print(f"  [green]Tip: {info['good']}[/green]")

    console.print()


def display_disclaimer() -> None:
    """Show the obligatory not-financial-advice disclaimer."""
    console.print(
        Panel(
            "[yellow]This tool is for educational and research purposes only. "
            "It is NOT financial advice. Past performance does not guarantee future results. "
            "Always do your own research and consider consulting a SEBI-registered financial advisor "
            "before making investment decisions. The data comes from free public APIs and may "
            "contain inaccuracies.[/yellow]",
            title="[bold red]Disclaimer[/bold red]",
            border_style="red",
        )
    )


def _colored_value(metric: str, value) -> str:
    """Return a Rich-formatted colored value string."""
    if value is None:
        return "[dim]N/A[/dim]"

    formatted = format_value(metric, value)

    # Color logic
    if metric == "composite_score":
        if value >= 80:
            return f"[bold green]{formatted}[/bold green]"
        if value >= 65:
            return f"[bold cyan]{formatted}[/bold cyan]"
        if value >= 50:
            return f"[yellow]{formatted}[/yellow]"
        return f"[red]{formatted}[/red]"

    if metric in ("cagr_1y", "cagr_3y", "cagr_5y"):
        return f"[green]{formatted}[/green]" if value > 0 else f"[red]{formatted}[/red]"

    if metric == "sharpe":
        if value >= 1.5:
            return f"[green]{formatted}[/green]"
        if value >= 0.5:
            return f"[yellow]{formatted}[/yellow]"
        return f"[red]{formatted}[/red]"

    if metric == "sortino":
        if value >= 2.0:
            return f"[green]{formatted}[/green]"
        if value >= 1.0:
            return f"[yellow]{formatted}[/yellow]"
        return f"[red]{formatted}[/red]"

    if metric == "volatility":
        if value < 0.15:
            return f"[green]{formatted}[/green]"
        if value < 0.25:
            return f"[yellow]{formatted}[/yellow]"
        return f"[red]{formatted}[/red]"

    if metric == "max_drawdown":
        if value > -0.15:
            return f"[green]{formatted}[/green]"
        if value > -0.30:
            return f"[yellow]{formatted}[/yellow]"
        return f"[red]{formatted}[/red]"

    if metric == "consistency":
        if value >= 0.8:
            return f"[green]{formatted}[/green]"
        if value >= 0.6:
            return f"[yellow]{formatted}[/yellow]"
        return f"[red]{formatted}[/red]"

    if metric == "alpha":
        return f"[green]{formatted}[/green]" if value > 0 else f"[red]{formatted}[/red]"

    return formatted


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."
