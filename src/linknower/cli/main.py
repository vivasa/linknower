"""Command-line interface for LinkNower."""

from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from linknower.data import (
    ChromaDBEmbeddingRepository,
    SQLiteClusterRepository,
    SQLiteEventRepository,
)
from linknower.domain import EventType
from linknower.ml import ClusteringEngine, EmbeddingEngine, FeatureEngineer
from linknower.services import ClusterService, SearchService, StatsService, SyncService, TimelineService
from linknower.utils import Config, PrivacyFilter

app = typer.Typer(
    name="linknower",
    help="Local-first personal workflow intelligence engine",
    add_completion=True,
)
console = Console()


def load_config() -> Config:
    """Load configuration from file or create default."""
    config = Config()
    config_path = config.get_config_path()
    
    if config_path.exists():
        return Config.from_file(config_path)
    return config


def get_services(config: Config):
    """Initialize and return all services."""
    # Repositories
    event_repo = SQLiteEventRepository(config.raw_db_path)
    cluster_repo = SQLiteClusterRepository(config.cluster_db_path)
    embedding_repo = ChromaDBEmbeddingRepository(config.chroma_db_path)

    # ML components
    embedding_engine = EmbeddingEngine(config.embedding_model)
    feature_engineer = FeatureEngineer(
        time_weight=config.time_weight,
        semantic_weight=config.semantic_weight,
        context_weight=config.context_weight,
    )
    clustering_engine = ClusteringEngine(min_cluster_size=config.min_cluster_size)

    # Privacy filter
    privacy_filter = PrivacyFilter(config.privacy_patterns)

    # Services
    sync_service = SyncService(
        event_repo, embedding_repo, embedding_engine, privacy_filter, config
    )
    search_service = SearchService(event_repo, embedding_repo, embedding_engine)
    cluster_service = ClusterService(
        event_repo, cluster_repo, embedding_repo, clustering_engine, feature_engineer, embedding_engine
    )
    timeline_service = TimelineService(event_repo)
    stats_service = StatsService(event_repo, cluster_repo)

    return {
        "sync": sync_service,
        "search": search_service,
        "cluster": cluster_service,
        "timeline": timeline_service,
        "stats": stats_service,
    }


@app.command()
def init():
    """Initialize LinkNower configuration."""
    config = load_config()
    config_path = config.get_config_path()

    if config_path.exists():
        console.print(f"[yellow]Configuration already exists at {config_path}[/yellow]")
        if not typer.confirm("Overwrite?"):
            raise typer.Abort()

    # Save default configuration
    config.to_file(config_path)
    console.print(f"[green]✓[/green] Initialized configuration at {config_path}")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("1. Run [cyan]lk sync --full[/cyan] to index your data")
    console.print("2. Run [cyan]lk search 'your query'[/cyan] to search")


@app.command()
def sync(
    full: bool = typer.Option(False, "--full", help="Perform full sync of all data"),
):
    """Sync data from configured sources."""
    config = load_config()
    config_path = config.get_config_path()

    if not config_path.exists():
        console.print("[red]Error:[/red] Not initialized. Run [cyan]lk init[/cyan] first.")
        raise typer.Exit(1)
    services = get_services(config)
    sync_service = services["sync"]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Syncing data...", total=None)
        stats = sync_service.sync_all(full=full)
        progress.update(task, completed=True)

    console.print("\n[green]✓[/green] Sync completed")
    console.print(f"  Browser events: {stats['browser']}")
    console.print(f"  Command events: {stats['command']}")
    console.print(f"  Commit events: {stats['commit']}")
    console.print(f"  Total: {sum(stats.values())}")


@app.command()
def search(
    query: str,
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum results to return"),
    event_type: Optional[str] = typer.Option(
        None, "--type", "-t", help="Filter by event type (browser/command/commit)"
    ),
):
    """Search for events semantically similar to query."""
    config = load_config()
    services = get_services(config)
    search_service = services["search"]

    # Parse event type
    et = None
    if event_type:
        try:
            et = EventType(event_type.lower())
        except ValueError:
            console.print(f"[red]Error:[/red] Invalid event type: {event_type}")
            console.print("Valid types: browser, command, commit")
            raise typer.Exit(1)

    # Perform search
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Searching...", total=None)
        results = search_service.search(query, limit=limit, event_type=et)
        progress.update(task, completed=True)

    # Display results
    if not results:
        console.print("[yellow]No results found[/yellow]")
        return

    table = Table(title=f"Search Results for: {query}")
    table.add_column("Type", style="cyan")
    table.add_column("Time", style="magenta")
    table.add_column("Content", style="white")
    table.add_column("Score", justify="right", style="green")

    for event, score in results:
        table.add_row(
            event.type.value,
            event.timestamp.strftime("%Y-%m-%d %H:%M"),
            event.content[:80] + "..." if len(event.content) > 80 else event.content,
            f"{score:.3f}",
        )

    console.print(table)


@app.command()
def timeline(
    days: Optional[int] = typer.Option(7, "--days", "-d", help="Number of days to show"),
    date: Optional[str] = typer.Option(None, "--date", help="Specific date (YYYY-MM-DD)"),
):
    """View contextual timeline of activities."""
    config = load_config()
    services = get_services(config)
    timeline_service = services["timeline"]

    # Parse date if provided
    start = None
    end = None
    if date:
        try:
            target_date = datetime.fromisoformat(date)
            start = target_date.replace(hour=0, minute=0, second=0)
            end = target_date.replace(hour=23, minute=59, second=59)
            days = None
        except ValueError:
            console.print(f"[red]Error:[/red] Invalid date format: {date}")
            console.print("Use YYYY-MM-DD format")
            raise typer.Exit(1)

    # Get timeline
    events = timeline_service.get_timeline(start=start, end=end, days=days)

    if not events:
        console.print("[yellow]No events found in timeline[/yellow]")
        return

    # Display timeline
    title = f"Timeline: Last {days} days" if days else f"Timeline: {date}"
    table = Table(title=title)
    table.add_column("Time", style="magenta")
    table.add_column("Type", style="cyan")
    table.add_column("Content", style="white")
    table.add_column("CWD", style="dim")

    for event in events:
        table.add_row(
            event.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            event.type.value,
            event.content[:70] + "..." if len(event.content) > 70 else event.content,
            event.cwd[:30] + "..." if event.cwd and len(event.cwd) > 30 else (event.cwd or ""),
        )

    console.print(table)
    console.print(f"\n[dim]Total events: {len(events)}[/dim]")


@app.command()
def cluster():
    """Manage activity clusters."""
    config = load_config()
    services = get_services(config)
    cluster_service = services["cluster"]

    # Run clustering
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Clustering events...", total=None)
        stats = cluster_service.cluster_events()
        progress.update(task, completed=True)

    console.print("\n[green]✓[/green] Clustering completed")
    console.print(f"  Clusters found: {stats['clusters']}")
    console.print(f"  Noise events: {stats['noise']}")

    # Show clusters
    clusters = cluster_service.get_all_clusters()
    if not clusters:
        return

    table = Table(title="Activity Clusters")
    table.add_column("ID", justify="right", style="cyan")
    table.add_column("Label", style="green")
    table.add_column("Events", justify="right")
    table.add_column("Duration", style="magenta")

    for cluster in clusters:
        duration = cluster.end_time - cluster.start_time
        hours = duration.total_seconds() / 3600

        table.add_row(
            str(cluster.id),
            cluster.label,
            str(cluster.event_count),
            f"{hours:.1f}h",
        )

    console.print(table)


@app.command()
def stats():
    """Display statistics about indexed data."""
    config = load_config()
    services = get_services(config)
    stats_service = services["stats"]

    data = stats_service.get_stats()

    table = Table(title="LinkNower Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="green")

    table.add_row("Total Events", str(data["total_events"]))
    table.add_row("  Browser Events", str(data["browser_events"]))
    table.add_row("  Command Events", str(data["command_events"]))
    table.add_row("  Commit Events", str(data["commit_events"]))
    table.add_row("Total Clusters", str(data["total_clusters"]))
    table.add_row("Clustered Events", str(data["clustered_events"]))

    console.print(table)


@app.command(name="config")
def config_cmd(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    edit: bool = typer.Option(False, "--edit", help="Edit configuration file"),
    add_repo: Optional[str] = typer.Option(None, "--add-repo", help="Add git repository"),
):
    """Manage configuration."""
    config = load_config()
    config_path = config.get_config_path()

    if show:
        console.print(f"[bold]Configuration:[/bold] {config_path}\n")
        console.print(f"Data directory: {config.data_dir}")
        console.print(f"Zen profile: {config.zen_profile_path}")
        console.print(f"Zsh history: {config.zsh_history_path}")
        console.print(f"Git repos: {', '.join(config.git_repos) if config.git_repos else 'None'}")
        console.print(f"Embedding model: {config.embedding_model}")
        console.print(f"Min cluster size: {config.min_cluster_size}")

    elif edit:
        import subprocess

        editor = subprocess.run(["which", "editor"], capture_output=True, text=True)
        if editor.returncode == 0:
            subprocess.run([editor.stdout.strip(), str(config_path)])
        else:
            console.print(f"[yellow]Open and edit:[/yellow] {config_path}")

    elif add_repo:
        repo_path = Path(add_repo).expanduser().resolve()
        if not (repo_path / ".git").exists():
            console.print(f"[red]Error:[/red] Not a git repository: {repo_path}")
            raise typer.Exit(1)

        config.add_git_repo(str(repo_path))
        config.to_file(config_path)
        console.print(f"[green]✓[/green] Added repository: {repo_path}")

    else:
        console.print("Use --show, --edit, or --add-repo")


if __name__ == "__main__":
    app()
