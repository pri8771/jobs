"""Command-line interface for Jobs Automation."""

from __future__ import annotations

import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from jobs_automation.core.config import AppSettings, ConfigLoader
from jobs_automation.db.base import Base
from jobs_automation.db.session import check_db_connection, get_engine, init_db
from jobs_automation.policy.evaluator import PolicyEvaluator
from jobs_automation.worksheets.generator import ProfileWorksheetGenerator

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="jobs-automation")
def cli() -> None:
    """Jobs Automation - Personal job-search operating system."""


@cli.command(name="validate-config")
@click.option("--config-dir", default="config", help="Path to config directory.")
def validate_config(config_dir: str) -> None:
    """Validate all configuration files and report unresolved facts."""
    console.print(Panel.fit("[bold blue]Jobs Automation - Configuration Validator[/bold blue]"))
    loader = ConfigLoader(config_dir)
    report = loader.validate_all()

    # Loaded files table
    table = Table(title="Loaded Configuration Files", show_header=True, header_style="bold cyan")
    table.add_column("Config Area", style="bold")
    table.add_column("Resolved Path")

    for area, path in sorted(report.loaded_files.items()):
        table.add_row(area, path)
    console.print(table)
    console.print()

    # Display errors if any
    if report.errors:
        console.print("[bold red]❌ Validation Errors:[/bold red]")
        for err in report.errors:
            console.print(f"  • [red]{err}[/red]")
        console.print()

    # Display warnings
    if report.warnings:
        console.print("[bold yellow]⚠️  Validation Warnings / Important Notes:[/bold yellow]")
        for warn in report.warnings:
            console.print(f"  • [yellow]{warn}[/yellow]")
        console.print()

    # Display unresolved candidate facts
    if report.unresolved_facts:
        facts_table = Table(
            title="Candidate Facts Tracking (Unknowns Must Not Be Fabricated)",
            header_style="bold magenta",
        )
        facts_table.add_column("Category", style="bold")
        facts_table.add_column("Unresolved / Pending Review Fields")

        has_any = False
        for cat, fields in report.unresolved_facts.items():
            if fields:
                has_any = True
                facts_table.add_row(cat, ", ".join(fields))
        if has_any:
            console.print(facts_table)
            console.print(
                "[italic dim]Note: The system preserves these as unresolved; agents will not guess answers.[/italic dim]\n"
            )

    if report.success:
        console.print("[bold green]✅ All configuration files validated successfully![/bold green]")
        sys.exit(0)
    else:
        console.print("[bold red]❌ Configuration validation failed with errors.[/bold red]")
        sys.exit(1)


@cli.command(name="db-check")
@click.option("--url", default=None, help="Database URL override.")
@click.option("--init-tables", is_flag=True, default=False, help="Initialize tables if connected.")
def db_check(url: str | None, init_tables: bool) -> None:
    """Check database connectivity and inspect tables."""
    console.print(Panel.fit("[bold blue]Jobs Automation - Database Health Check[/bold blue]"))
    settings = AppSettings()
    db_url = url or settings.database_url

    # Mask password for display
    display_url = db_url
    if "@" in display_url and ":" in display_url:
        try:
            proto, rest = display_url.split("://", 1)
            auth, host_db = rest.split("@", 1)
            user = auth.split(":", 1)[0]
            display_url = f"{proto}://{user}:****@{host_db}"
        except Exception:
            pass

    console.print(f"[bold]Target Database URL:[/bold] {display_url}")
    engine = get_engine(db_url)
    connected, msg, latency_ms = check_db_connection(engine)

    if connected:
        console.print(
            f"[bold green]✅ Connection Successful[/bold green] (Latency: {latency_ms:.2f}ms)"
        )
        console.print(f"[bold]Dialect:[/bold] {engine.dialect.name}")

        if init_tables:
            console.print("Initializing schema tables...")
            init_db(engine)
            console.print("[bold green]✅ Schema tables initialized successfully.[/bold green]")

        # Check existing tables in metadata
        table_count = len(Base.metadata.tables)
        console.print(f"[bold]Registered Data Models:[/bold] {table_count} tables")
        for table_name in sorted(Base.metadata.tables.keys()):
            console.print(f"  • {table_name}")
    else:
        console.print(f"[bold red]❌ Connection Failed:[/bold red] {msg}")
        console.print(
            "[dim yellow]Ensure PostgreSQL is running via 'docker compose up -d postgres'.[/dim yellow]"
        )
        sys.exit(1)


@cli.command(name="status")
@click.option("--config-dir", default="config", help="Path to config directory.")
def status(config_dir: str) -> None:
    """Display comprehensive status of the Jobs Automation system."""
    console.print(Panel.fit("[bold blue]Jobs Automation — System Status (V0.1)[/bold blue]"))

    # 1. Checkpoint & Architecture info
    info_table = Table(title="System Overview", show_header=False)
    info_table.add_column("Property", style="bold cyan")
    info_table.add_column("Value")
    info_table.add_row("Active Checkpoint", "V0.1 — Portable foundation + profiles")
    info_table.add_row("Primary Positioning", "Enterprise Automation & Solutions Architect")
    info_table.add_row("Target Compensation", "$150,000+ USD")
    info_table.add_row("Email Polling Default", "Every 4 hours (240 min) — Non-realtime periodic")
    info_table.add_row("Application Policy Default", "BLOCKED (Default-deny for auto-apply)")
    console.print(info_table)
    console.print()

    # 2. Config status
    loader = ConfigLoader(config_dir)
    report = loader.validate_all()
    if report.success:
        console.print("  [bold green]✅ Configuration:[/bold green] All configuration files valid")
    else:
        console.print("  [bold red]❌ Configuration:[/bold red] Has configuration errors")

    # 3. Database status
    settings = AppSettings()
    engine = get_engine(settings.database_url)
    connected, msg, latency_ms = check_db_connection(engine)
    if connected:
        console.print(
            f"  [bold green]✅ Database:[/bold green] Connected ({engine.dialect.name}, {latency_ms:.1f}ms)"
        )
    else:
        console.print(f"  [bold yellow]⚠️  Database:[/bold yellow] Offline ({msg})")

    # 4. Platforms overview
    try:
        platforms_cfg, _ = loader.load_platforms()
        plat_table = Table(
            title="Platforms & Application Submission Modes", header_style="bold green"
        )
        plat_table.add_column("Platform", style="bold")
        plat_table.add_column("Submission Mode")
        plat_table.add_column("Profile Status")
        plat_table.add_column("Alert Status")

        for name, p in sorted(platforms_cfg.platforms.items()):
            plat_table.add_row(name, p.submission_mode, p.profile_status, p.alert_status)
        console.print(plat_table)
        console.print()
    except Exception as e:
        console.print(f"  [red]Failed to load platforms config: {e}[/red]")

    # 5. Policy Registry Summary
    try:
        policy_cfg, _ = loader.load_policy_registry()
        evaluator = PolicyEvaluator(policy_cfg)
        test_eval = evaluator.evaluate("jobs.lever.co")
        console.print(
            f"  [bold]Policy Registry:[/bold] Default decision is [bold red]{policy_cfg.default.decision.upper()}[/bold red] ({policy_cfg.default.reason})"
        )
        console.print(
            f"  [dim]Example test query (jobs.lever.co) -> {test_eval.decision.value} ({test_eval.reason})[/dim]\n"
        )
    except Exception as e:
        console.print(f"  [red]Failed to load policy registry: {e}[/red]")


@cli.command(name="generate-profile-worksheet")
@click.option("--config-dir", default="config", help="Path to config directory.")
@click.option("--output", default="docs/PROFILE_WORKSHEET.md", help="Destination markdown path.")
def generate_worksheet(config_dir: str, output: str) -> None:
    """Generate profile setup worksheet for LinkedIn, Indeed, ZipRecruiter, and Dice."""
    console.print(Panel.fit("[bold blue]Generating Profile Setup Worksheet[/bold blue]"))
    loader = ConfigLoader(config_dir)
    profile, _ = loader.load_candidate_profile()
    job_search, _ = loader.load_job_search()

    generator = ProfileWorksheetGenerator(profile, job_search)
    out_path = generator.save_worksheet(output)
    console.print(
        f"[bold green]✅ Profile setup worksheet generated successfully at:[/bold green] [cyan]{out_path}[/cyan]"
    )


if __name__ == "__main__":
    cli()
