import json
import uuid
import click
from rich.console import Console
from rich.json import JSON
from rich.table import Table

from jobs_automation.db.session import get_sessionmaker
from jobs_automation.intelligence.edges import backfill_message_link_contacts
from jobs_automation.intelligence.target_companies import TargetCompanyService
from jobs_automation.intelligence.watch_runner import WatchRunner
from jobs_automation.ingestion.sources import get_source

console = Console()


@click.group(name="intel")
def intel_cli() -> None:
    """Intelligence, Graph, and Target Watch commands."""
    pass


@intel_cli.command("backfill-contact-links")
@click.option("--dry-run", is_flag=True, help="Report what would happen without committing")
def backfill_contact_links(dry_run: bool) -> None:
    """Backfills contact_id onto existing MessageLinkModel rows."""
    SessionLocal = get_sessionmaker()
    with SessionLocal() as session:
        report = backfill_message_link_contacts(session, dry_run=dry_run)

    console.print(f"Dry run: {dry_run}")
    console.print(JSON(report.model_dump_json()))


@intel_cli.group(name="targets")
def targets_cli() -> None:
    """Target company watchlist commands."""
    pass


@targets_cli.command("add")
@click.option("--name", required=True, help="Canonical company name")
@click.option("--domain", default=None, help="Company domain")
@click.option("--priority", default=3, type=int, help="Priority (1-5)")
@click.option("--reason", default=None, help="Reason for watching")
@click.option("--provider", default="GREENHOUSE", help="ATS provider (GREENHOUSE, LEVER)")
@click.option("--source-key", required=True, help="Source key / token for board API")
def add_target(name: str, domain: str | None, priority: int, reason: str | None, provider: str, source_key: str) -> None:
    """Add a company to the watch list."""
    SessionLocal = get_sessionmaker()
    with SessionLocal() as session:
        svc = TargetCompanyService(session)
        target = svc.add(
            canonical_name=name,
            domain=domain,
            priority=priority,
            reason=reason,
            source_config={"provider": provider, "source_key": source_key},
        )
        session.commit()
        console.print(f"[green]Added target company:[/green] {target.canonical_name} (ID: {target.id}, Status: {target.watch_status})")


@targets_cli.command("list")
@click.option("--status", default=None, help="Filter by status (ACTIVE, PAUSED, ARCHIVED)")
def list_targets(status: str | None) -> None:
    """List target companies."""
    SessionLocal = get_sessionmaker()
    with SessionLocal() as session:
        svc = TargetCompanyService(session)
        targets = svc.list(status=status)

        table = Table(title="Target Companies")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="bold")
        table.add_column("Domain")
        table.add_column("Priority", justify="right")
        table.add_column("Status", style="yellow")
        table.add_column("Provider")

        for t in targets:
            provider = (t.source_config or {}).get("provider", "N/A")
            table.add_row(
                str(t.id)[:8],
                t.canonical_name,
                t.domain or "",
                str(t.priority),
                t.watch_status,
                provider,
            )
        console.print(table)


@targets_cli.command("set-status")
@click.argument("target_id")
@click.argument("status", type=click.Choice(["ACTIVE", "PAUSED", "ARCHIVED"]))
def set_status(target_id: str, status: str) -> None:
    """Set watch status of a target company."""
    SessionLocal = get_sessionmaker()
    with SessionLocal() as session:
        svc = TargetCompanyService(session)
        target = svc.set_status(uuid.UUID(target_id), status)
        session.commit()
        console.print(f"[green]Updated status for {target.canonical_name}:[/green] {target.watch_status}")


@targets_cli.command("observations")
@click.argument("target_id")
@click.option("--limit", default=20, type=int, help="Max observations to display")
def observations(target_id: str, limit: int) -> None:
    """Display observations for a target company."""
    SessionLocal = get_sessionmaker()
    with SessionLocal() as session:
        svc = TargetCompanyService(session)
        obs_list = svc.observations(uuid.UUID(target_id))[:limit]

        table = Table(title=f"Observations for {target_id[:8]}")
        table.add_column("Observed At", style="cyan")
        table.add_column("Type", style="bold")
        table.add_column("Source Ref")
        table.add_column("Confidence", justify="right")
        table.add_column("Status")

        for obs in obs_list:
            table.add_row(
                obs.observed_at.strftime("%Y-%m-%d %H:%M"),
                obs.observation_type,
                obs.source_reference[:40] if obs.source_reference else "",
                f"{obs.confidence:.2f}",
                obs.status,
            )
        console.print(table)


@targets_cli.command("run-watch")
@click.option("--target-id", default=None, help="Optional specific target UUID")
@click.option("--dry-run", is_flag=True, help="Roll back transaction after run")
def run_watch(target_id: str | None, dry_run: bool) -> None:
    """Run watch sweep across active target companies."""
    SessionLocal = get_sessionmaker()
    with SessionLocal() as session:
        sources = {
            "GREENHOUSE": get_source("GREENHOUSE"),
            "LEVER": get_source("LEVER"),
        }
        runner = WatchRunner(session, sources)
        target_uuid = uuid.UUID(target_id) if target_id else None
        report = runner.run(target_id=target_uuid)

        if dry_run:
            session.rollback()
            console.print("[yellow]Dry run mode: changes rolled back.[/yellow]")
        else:
            session.commit()

        console.print(f"[bold green]Watch Sweep Completed[/bold green] (Targets checked: {len(report.target_reports)})")
        console.print(f"  New Roles: {report.total_new}")
        console.print(f"  Changed Roles: {report.total_changed}")
        console.print(f"  Closed Roles: {report.total_closed}")
