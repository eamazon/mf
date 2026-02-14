"""CLI entry point for the Mutual Fund Recommender."""

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from .data.fund_categories import POPULAR_SCHEMES, EQUITY_CATEGORIES, DEBT_CATEGORIES, HYBRID_CATEGORIES
from .data import cache as cache_mod

console = Console()

ALL_CATEGORIES = list(POPULAR_SCHEMES.keys())


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Indian Mutual Fund Recommender - data-backed analysis using free public data.

    Analyzes mutual funds using NAV history from MFAPI.in and metadata from Kuvera.
    Computes returns, risk metrics, and a composite score to help you shortlist funds.

    This is NOT financial advice. Use it as a research starting point.
    """
    pass


@cli.command()
@click.argument("category", required=False)
@click.option("--top", "-n", default=5, help="Number of top funds to show per category.")
@click.option("--all-categories", "-a", is_flag=True, help="Show recommendations across all categories.")
def recommend(category, top, all_categories):
    """Get top fund recommendations for a category.

    CATEGORY can be one of: Large Cap, Mid Cap, Small Cap, Flexi Cap,
    ELSS (Tax Saving), Index Fund, Balanced Advantage.

    If no category is given, shows an interactive menu.
    """
    from .recommender import recommend_category, recommend_all_categories
    from .display import display_comparison_table, display_category_recommendations, display_disclaimer

    display_disclaimer()

    if all_categories:
        console.print("\n[bold]Analyzing funds across all categories...[/bold]\n")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            console=console,
        ) as progress:
            task = progress.add_task("Fetching & analyzing funds...", total=100)

            def cb(done, total):
                progress.update(task, completed=done, total=total)

            results = recommend_all_categories(top_n=top, progress_callback=cb)
        display_category_recommendations(results)
        return

    if not category:
        console.print("\n[bold]Available categories:[/bold]\n")
        for i, cat in enumerate(ALL_CATEGORIES, 1):
            count = len(POPULAR_SCHEMES.get(cat, []))
            console.print(f"  {i}. {cat} ({count} funds)")
        console.print()
        choice = click.prompt("Pick a category number", type=int)
        if 1 <= choice <= len(ALL_CATEGORIES):
            category = ALL_CATEGORIES[choice - 1]
        else:
            console.print("[red]Invalid choice.[/red]")
            return

    if category not in POPULAR_SCHEMES:
        # Fuzzy match
        cat_lower = category.lower()
        for cat in ALL_CATEGORIES:
            if cat_lower in cat.lower() or cat.lower() in cat_lower:
                category = cat
                break
        else:
            console.print(f"[red]Unknown category: {category}[/red]")
            console.print(f"Available: {', '.join(ALL_CATEGORIES)}")
            return

    console.print(f"\n[bold]Analyzing {category} funds...[/bold]\n")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Analyzing {category}...", total=len(POPULAR_SCHEMES.get(category, [])))

        def cb(done, total):
            progress.update(task, completed=done, total=total)

        results = recommend_category(category, top_n=top, progress_callback=cb)

    if not results:
        console.print("[yellow]No results found. The API may be temporarily unavailable.[/yellow]")
        return

    display_comparison_table(results, title=f"Top {category} Funds")

    # Show detailed cards for top 3
    from .display import display_fund_card
    console.print("[bold]Detailed Analysis:[/bold]\n")
    for fund in results[:3]:
        display_fund_card(fund)


@cli.command()
@click.argument("query")
@click.option("--max", "-m", "max_results", default=5, help="Maximum number of results.")
def search(query, max_results):
    """Search for a fund by name and analyze it.

    Example: mf search "parag parikh"
    """
    from .recommender import search_and_analyze
    from .display import display_comparison_table, display_fund_card, display_disclaimer

    display_disclaimer()
    console.print(f"\n[bold]Searching for '{query}'...[/bold]\n")

    with Progress(SpinnerColumn(), TextColumn("Fetching data..."), console=console) as progress:
        progress.add_task("Searching...", total=None)
        results = search_and_analyze(query, max_results=max_results)

    if not results:
        console.print("[yellow]No funds found matching your query.[/yellow]")
        return

    display_comparison_table(results, title=f"Results for '{query}'")

    if len(results) > 0:
        console.print("[bold]Top result - Detailed Analysis:[/bold]\n")
        display_fund_card(results[0])


@cli.command()
@click.argument("scheme_code", type=int)
def analyze(scheme_code):
    """Analyze a specific fund by its AMFI scheme code.

    You can find scheme codes at: https://api.mfapi.in/mf
    """
    from .recommender import analyze_fund, get_benchmark_nav
    from .display import display_fund_card, display_disclaimer

    display_disclaimer()
    console.print(f"\n[bold]Analyzing scheme {scheme_code}...[/bold]\n")

    with Progress(SpinnerColumn(), TextColumn("Fetching NAV data..."), console=console) as progress:
        progress.add_task("Analyzing...", total=None)
        benchmark = get_benchmark_nav()
        result = analyze_fund(scheme_code, benchmark)

    if not result:
        console.print("[red]Could not analyze this fund. Check the scheme code or try again later.[/red]")
        return

    display_fund_card(result)


@cli.command()
def learn():
    """Learn what each metric means - plain English explanations.

    Great starting point if you're new to mutual fund investing.
    """
    from .display import display_metric_guide
    display_metric_guide()


@cli.command()
def clear_cache():
    """Clear the local data cache (forces fresh API calls)."""
    cache_mod.clear()
    console.print("[green]Cache cleared.[/green]")


@cli.command()
@click.option("--api-key", "-k", envvar="ANTHROPIC_API_KEY", help="Anthropic API key (or set ANTHROPIC_API_KEY env var).")
@click.option("--question", "-q", default=None, help="Ask a single question (non-interactive mode).")
def chat(api_key, question):
    """Chat with an AI mutual fund advisor (powered by Claude).

    Understands natural language. Ask things like:

    \b
      "I'm 28, can invest 30k/month, moderate risk - build me a portfolio"
      "Compare PPFAS Flexi Cap vs Mirae Large Cap"
      "I need 1 crore in 15 years, how much SIP do I need?"
      "What are the best small cap funds right now?"
      "Explain Sharpe ratio to me like I'm 5"

    Requires an Anthropic API key. Set ANTHROPIC_API_KEY env var or pass --api-key.
    """
    from .agent.chat import create_agent
    from rich.markdown import Markdown
    from rich.panel import Panel

    try:
        agent = create_agent(api_key)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        return

    console.print(Panel(
        "[bold cyan]MF Advisor[/bold cyan] - Your AI Mutual Fund Research Assistant\n\n"
        "Ask me anything about Indian mutual funds. I'll fetch real data and give you\n"
        "data-backed answers. Try:\n\n"
        "  [green]\"Best large cap funds right now\"[/green]\n"
        "  [green]\"I'm 30, aggressive risk, 50k/month - build a portfolio\"[/green]\n"
        "  [green]\"How much SIP for 1 crore in 15 years?\"[/green]\n"
        "  [green]\"Compare Parag Parikh vs Mirae Asset Large Cap\"[/green]\n\n"
        "[dim]Type 'quit' or 'exit' to leave. Type 'reset' to start fresh.[/dim]\n"
        "[dim yellow]This is NOT financial advice. For educational use only.[/dim yellow]",
        title="[bold]Welcome[/bold]",
        border_style="cyan",
    ))

    # Single-question mode
    if question:
        console.print(f"\n[bold]You:[/bold] {question}\n")
        with console.status("[bold cyan]Thinking & fetching data...[/bold cyan]"):
            response = agent.chat(question)
        console.print(Markdown(response))
        return

    # Interactive loop
    while True:
        console.print()
        try:
            user_input = console.input("[bold]You:[/bold] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            console.print("[dim]Goodbye![/dim]")
            break
        if user_input.lower() == "reset":
            agent.reset()
            console.print("[green]Conversation reset.[/green]")
            continue

        with console.status("[bold cyan]Thinking & fetching data...[/bold cyan]"):
            try:
                response = agent.chat(user_input)
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                continue

        console.print()
        console.print(Markdown(response))


if __name__ == "__main__":
    cli()
