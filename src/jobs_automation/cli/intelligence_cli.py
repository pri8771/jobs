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


@intel_cli.command("interview-brief")
@click.argument("application_id")
@click.option("--json", "output_json", is_flag=True, help="Output JSON format")
def interview_brief(application_id: str, output_json: bool) -> None:
    """Generate interview brief for an application."""
    from jobs_automation.intelligence.interview_service import InterviewIntelligenceService

    SessionLocal = get_sessionmaker()
    with SessionLocal() as session:
        service = InterviewIntelligenceService(session)
        try:
            brief = service.build_brief(application_id)
            if output_json:
                console.print(JSON(brief.model_dump_json()))
            else:
                console.print(f"[bold blue]Interview Brief for Application {application_id}[/bold blue]")
                console.print(f"Stage: {brief.interview_stage}")
                console.print(f"Role: {brief.role_summary}")
                console.print(f"Requirements count: {len(brief.key_requirements)}")
                if brief.conflicts:
                    console.print(f"[yellow]Conflicts: {', '.join(brief.conflicts)}[/yellow]")
                if brief.security_signals:
                    console.print(f"[red]Security Signals: {', '.join(brief.security_signals)}[/red]")
        except LookupError as e:
            console.print(f"[red]Error:[/red] {e}")


@intel_cli.command("followup-package")
@click.argument("application_id")
@click.option("--contact-id", default=None, help="Optional contact UUID")
@click.option("--json", "output_json", is_flag=True, help="Output JSON format")
def followup_package(application_id: str, contact_id: str | None, output_json: bool) -> None:
    """Generate follow-up package for an application."""
    from jobs_automation.intelligence.interview_service import InterviewIntelligenceService

    SessionLocal = get_sessionmaker()
    with SessionLocal() as session:
        service = InterviewIntelligenceService(session)
        try:
            pkg = service.build_followup(application_id, contact_id=contact_id)
            if output_json:
                console.print(JSON(pkg.model_dump_json()))
            else:
                console.print(f"[bold blue]Followup Package for Application {application_id}[/bold blue]")
                console.print(f"Context: {pkg.stage_context}")
                console.print(f"Facts count: {len(pkg.facts)}")
                console.print(f"Send performed: {pkg.send_performed}")
        except LookupError as e:
            console.print(f"[red]Error:[/red] {e}")


@intel_cli.group(name="tool")
def tool_cli() -> None:
    """Agent tool framework commands."""
    pass


@tool_cli.command("list")
def list_tools() -> None:
    """List all registered agent tools."""
    from jobs_automation.tools import get_default_tool_registry

    registry = get_default_tool_registry()
    table = Table(title="Registered Agent Tools")
    table.add_column("Name", style="bold cyan")
    table.add_column("Version", style="dim")
    table.add_column("Action Class", style="yellow")
    table.add_column("Capability")
    table.add_column("Requires Destination")

    for spec in registry.list():
        table.add_row(
            spec.name,
            spec.version,
            spec.action_class.value,
            spec.capability or "",
            "Yes" if spec.requires_destination else "No",
        )
    console.print(table)


@tool_cli.command("describe")
@click.argument("name")
@click.option("--version", default="1.0", help="Tool version")
def describe_tool(name: str, version: str) -> None:
    """Export JSON schema description for a tool."""
    from jobs_automation.tools import get_default_tool_registry

    registry = get_default_tool_registry()
    spec = registry.get(name, version)
    if not spec:
        console.print(f"[red]Tool not found:[/red] {name} (v{version})")
        raise click.ClickException(f"Tool not found: {name}")

    desc = {
        "name": spec.name,
        "version": spec.version,
        "action_class": spec.action_class.value,
        "capability": spec.capability,
        "requires_destination": spec.requires_destination,
        "input_schema": spec.input_model.model_json_schema(),
        "output_schema": spec.output_model.model_json_schema(),
    }
    console.print(JSON(json.dumps(desc)))


@tool_cli.command("call")
@click.argument("name")
@click.option("--json", "payload_json", default="{}", help="Input payload JSON string")
@click.option("--actor", default="USER", help="Actor name")
@click.option("--ceiling", default="P1_LOCAL_WRITE", help="Caller ceiling ActionClass")
@click.option("--allow-external-prep", is_flag=True, help="Set allow_external_prep flag")
@click.option("--approval-id", default=None, help="Optional approval UUID")
def call_tool(name: str, payload_json: str, actor: str, ceiling: str, allow_external_prep: bool, approval_id: str | None) -> None:
    """Invoke an agent tool directly via ToolRuntime."""
    from jobs_automation.db.session import get_engine, get_sessionmaker
    from jobs_automation.core.config import AppSettings
    from jobs_automation.tools import (
        ActionClass,
        PermissionContext,
        ToolRuntime,
        get_default_tool_registry,
    )

    settings = AppSettings()
    engine = get_engine(settings.database_url)
    SessionLocal = get_sessionmaker(engine)
    registry = get_default_tool_registry()

    runtime = ToolRuntime(SessionLocal, registry)
    payload = json.loads(payload_json)

    context = PermissionContext(
        actor=actor,
        actor_kind="USER" if actor == "USER" else "AGENT",
        caller_ceiling=ActionClass(ceiling),
        allow_external_prep=allow_external_prep,
        approval_id=uuid.UUID(approval_id) if approval_id else None,
    )

    result = runtime.invoke(name, payload, context)
    console.print(JSON(result.model_dump_json()))

    if result.status in (ToolStatus.BLOCKED, ToolStatus.NEEDS_REVIEW, ToolStatus.FAILED):
        raise click.ClickException(f"Tool invocation result: {result.status.value}")
