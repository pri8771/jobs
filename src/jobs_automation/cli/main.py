"""Command-line interface for Jobs Automation."""

from __future__ import annotations

import sys
import uuid
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from jobs_automation.core.config import AppSettings, ConfigLoader
from jobs_automation.db.base import Base
from jobs_automation.db.session import check_db_connection, get_engine, get_sessionmaker, init_db
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


@cli.command(name="poll-emails")
@click.option("--reconcile", is_flag=True, default=False, help="Run 48-hour reconciliation sweep.")
@click.option("--dry-run", is_flag=True, default=False, help="Simulate polling without saving.")
@click.option(
    "--mock-fixtures", is_flag=True, default=False, help="Use realistic offline test fixtures."
)
@click.option("--config-dir", default="config", help="Path to config directory.")
def poll_emails(reconcile: bool, dry_run: bool, mock_fixtures: bool, config_dir: str) -> None:
    """Execute periodic Gmail mailbox sweep (4-hour cadence, thread-preserving, idempotent)."""
    console.print(Panel.fit("[bold blue]Jobs Automation — Mailbox Polling Sweep[/bold blue]"))

    loader = ConfigLoader(config_dir)
    profile, _ = loader.load_candidate_profile()
    if profile.identity.email:
        candidate_emails = [profile.identity.email]
    else:
        console.print(
            "[yellow]⚠️ Warning: profile.identity.email is not set. Outbound email classification confidence will be reduced.[/yellow]"
        )
        candidate_emails = []

    from jobs_automation.adapters.gmail import GmailAdapter, MockEmailAdapter
    from jobs_automation.ingestion.engine import EmailIngestionEngine
    from jobs_automation.ingestion.fixtures import get_sample_email_fixtures

    adapter: Any
    if mock_fixtures:
        console.print(
            "[dim cyan]Using offline test fixtures adapter (7 sample messages)...[/dim cyan]"
        )
        adapter = MockEmailAdapter(get_sample_email_fixtures())
    else:
        try:
            adapter = GmailAdapter()
        except Exception as e:
            console.print(
                f"[bold red]❌ Failed to initialize live Gmail API adapter: {e}[/bold red]\n"
                "[yellow]To run offline with test fixtures, pass --mock-fixtures explicitly.[/yellow]"
            )
            raise click.ClickException(
                f"Gmail credentials not available: {e}. Pass --mock-fixtures to test with offline fixtures."
            )

    settings = AppSettings()
    engine = get_engine(settings.database_url)
    session_factory = get_sessionmaker(engine)

    with session_factory() as session:
        ingestion_engine = EmailIngestionEngine(
            session=session,
            adapter=adapter,
            candidate_emails=candidate_emails,
        )

        console.print(
            f"Starting sweep (Reconciliation: [bold]{reconcile}[/bold], Dry-run: [bold]{dry_run}[/bold])..."
        )
        summary = ingestion_engine.run_sweep(reconcile=reconcile, dry_run=dry_run)

        table = Table(title="Ingestion Sweep Summary", header_style="bold green")
        table.add_column("Metric", style="bold")
        table.add_column("Count / Value")

        table.add_row("Messages Polled", str(summary.messages_polled))
        table.add_row("Messages Ingested", f"[bold green]{summary.messages_ingested}[/bold green]")
        table.add_row("Duplicate Messages Skipped", str(summary.messages_skipped_duplicate))
        table.add_row(
            "New Jobs Discovered", f"[bold cyan]{summary.jobs_discovered_new}[/bold cyan]"
        )
        table.add_row("Existing Jobs Updated", str(summary.jobs_updated_existing))
        table.add_row("Review Tasks Created", str(summary.review_tasks_created))
        table.add_row(
            "Checkpoint Advanced To", summary.checkpoint_advanced_to or "None (Unchanged)"
        )

        console.print(table)
        console.print()

        if dry_run:
            console.print(
                "[bold yellow]ℹ️ Dry-run completed: zero database changes or checkpoints were persisted.[/bold yellow]"
            )

        if summary.errors:
            console.print("[bold red]Errors during sweep:[/bold red]")
            for err in summary.errors:
                console.print(f"  • {err}")
        else:
            console.print("[bold green]✅ Ingestion sweep completed successfully.[/bold green]")


@cli.command(name="mailbox-status")
def mailbox_status() -> None:
    """Display mailbox health, checkpointing status, and ingested message statistics."""
    console.print(Panel.fit("[bold blue]Jobs Automation — Mailbox & Ingestion Status[/bold blue]"))

    settings = AppSettings()
    engine = get_engine(settings.database_url)
    session_factory = get_sessionmaker(engine)

    from sqlalchemy import distinct, func, select

    from jobs_automation.db.models import InboundMessageModel, JobModel, TaskModel

    with session_factory() as session:
        # Checkpoint
        chk_stmt = (
            select(TaskModel)
            .where(TaskModel.task_type == "email_checkpoint")
            .order_by(TaskModel.due_at.desc())
        )
        last_chk = session.execute(chk_stmt).scalars().first()

        # Message totals
        total_msgs = session.execute(select(func.count(InboundMessageModel.id))).scalar() or 0
        inbound_count = (
            session.execute(
                select(func.count(InboundMessageModel.id)).where(
                    InboundMessageModel.direction == "inbound"
                )
            ).scalar()
            or 0
        )
        outbound_count = (
            session.execute(
                select(func.count(InboundMessageModel.id)).where(
                    InboundMessageModel.direction == "outbound"
                )
            ).scalar()
            or 0
        )

        # Unique threads
        threads_count = (
            session.execute(
                select(func.count(distinct(InboundMessageModel.provider_thread_id)))
            ).scalar()
            or 0
        )

        # Jobs discovered
        jobs_count = session.execute(select(func.count(JobModel.id))).scalar() or 0

        # Pending review tasks
        review_count = (
            session.execute(
                select(func.count(TaskModel.id)).where(
                    TaskModel.task_type == "NEEDS_REVIEW", TaskModel.status == "pending"
                )
            ).scalar()
            or 0
        )

        overview = Table(title="Mailbox & Ingestion Overview", show_header=False)
        overview.add_column("Property", style="bold cyan")
        overview.add_column("Value")

        overview.add_row(
            "Last Checkpoint", str(last_chk.due_at) if last_chk else "None (Fresh Mailbox)"
        )
        overview.add_row("Total Messages Ingested", str(total_msgs))
        overview.add_row("Inbound Messages", str(inbound_count))
        overview.add_row("Outbound Messages (Candidate Replies)", str(outbound_count))
        overview.add_row("Conversation Threads Preserved", str(threads_count))
        overview.add_row("Total Jobs in Database", str(jobs_count))
        overview.add_row(
            "Tasks Awaiting Review (NEEDS_REVIEW)",
            f"[bold yellow]{review_count}[/bold yellow]" if review_count else "0",
        )

        console.print(overview)
        console.print()

        # Breakdown by classification
        class_stmt = select(
            InboundMessageModel.classification, func.count(InboundMessageModel.id)
        ).group_by(InboundMessageModel.classification)
        class_rows = session.execute(class_stmt).all()
        if class_rows:
            class_table = Table(title="Messages by Classification", header_style="bold magenta")
            class_table.add_column("Classification", style="bold")
            class_table.add_column("Count")
            for cat, count in sorted(class_rows, key=lambda x: x[1], reverse=True):
                class_table.add_row(cat, str(count))
            console.print(class_table)


@cli.command(name="evaluate-jobs")
@click.option("--config-dir", default="config", help="Path to config directory.")
@click.option("--limit", default=100, help="Max jobs to evaluate.")
def evaluate_jobs(config_dir: str, limit: int) -> None:
    """Evaluate discovered jobs using hard filters and multi-dimensional scoring."""
    console.print(Panel.fit("[bold blue]Jobs Automation — Job Evaluation & Scoring[/bold blue]"))

    loader = ConfigLoader(config_dir)
    profile, _ = loader.load_candidate_profile()
    search_config, _ = loader.load_job_search()

    from jobs_automation.evaluation.engine import JobEvaluationEngine

    settings = AppSettings()
    engine = get_engine(settings.database_url)
    session_factory = get_sessionmaker(engine)

    with session_factory() as session:
        eval_engine = JobEvaluationEngine(
            session=session,
            candidate_profile=profile,
            job_search_config=search_config,
        )
        summary = eval_engine.run_evaluation_batch(limit=limit)

        summary_table = Table(title="Evaluation Batch Summary", header_style="bold green")
        summary_table.add_column("Metric", style="bold")
        summary_table.add_column("Count", justify="right")
        summary_table.add_row("Jobs Evaluated", str(summary.total_evaluated))
        summary_table.add_row(
            "[green]Shortlisted (Ready for Preparation)[/green]", str(summary.shortlisted)
        )
        summary_table.add_row(
            "[yellow]Considered (Borderline / Review)[/yellow]", str(summary.considered)
        )
        summary_table.add_row(
            "[yellow]Hard Filter Review Needed[/yellow]", str(summary.needs_review)
        )
        summary_table.add_row("[dim]Rejected (Disqualified)[/dim]", str(summary.rejected))

        console.print(summary_table)


@cli.command(name="prepare-packets")
@click.option("--config-dir", default="config", help="Path to config directory.")
@click.option("--limit", default=50, help="Max shortlisted jobs to prepare.")
def prepare_packets(config_dir: str, limit: int) -> None:
    """Build reproducible application packets for shortlisted jobs."""
    console.print(Panel.fit("[bold blue]Jobs Automation — Application Packet Builder[/bold blue]"))

    loader = ConfigLoader(config_dir)
    profile, _ = loader.load_candidate_profile()

    from sqlalchemy import select

    from jobs_automation.adapters.models import MockModelGateway
    from jobs_automation.db.models import JobModel
    from jobs_automation.preparation.packet_builder import ApplicationPacketBuilder

    settings = AppSettings()
    engine = get_engine(settings.database_url)
    session_factory = get_sessionmaker(engine)

    with session_factory() as session:
        builder = ApplicationPacketBuilder(
            session=session,
            candidate_profile=profile,
            model_gateway=MockModelGateway(),
        )

        stmt = (
            select(JobModel)
            .where(JobModel.status == "shortlisted")
            .order_by(JobModel.first_seen_at.desc())
            .limit(limit)
        )
        jobs = session.execute(stmt).scalars().all()

        if not jobs:
            console.print("[yellow]No shortlisted jobs waiting for packet preparation.[/yellow]")
            return

        packet_table = Table(title="Prepared Application Packets", header_style="bold cyan")
        packet_table.add_column("Job Title", style="bold")
        packet_table.add_column("Company")
        packet_table.add_column("Resume Variant")
        packet_table.add_column("Packet Hash (SHA-256)", style="dim")
        packet_table.add_column("Status")

        for job in jobs:
            packet, res = builder.build_packet(job)
            status_str = (
                "[yellow]Review Needed[/yellow]"
                if res.has_unresolved_questions
                else "[green]Prepared[/green]"
            )
            co_name = job.company.normalized_name if job.company else "Unknown"
            packet_table.add_row(
                job.normalized_title,
                co_name,
                res.resume_variant,
                res.packet_hash[:16] + "...",
                status_str,
            )

        session.commit()
        console.print(packet_table)


@cli.command(name="review-queue")
def review_queue() -> None:
    """List pending review tasks awaiting candidate input."""
    console.print(Panel.fit("[bold blue]Jobs Automation — Human Review Queue[/bold blue]"))

    from sqlalchemy import select

    from jobs_automation.db.models import TaskModel

    settings = AppSettings()
    engine = get_engine(settings.database_url)
    session_factory = get_sessionmaker(engine)

    with session_factory() as session:
        stmt = (
            select(TaskModel)
            .where(TaskModel.task_type == "NEEDS_REVIEW", TaskModel.status == "pending")
            .order_by(TaskModel.due_at.desc().nulls_last())
        )
        tasks = session.execute(stmt).scalars().all()

        if not tasks:
            console.print("[green]Review queue is clean! No pending items require review.[/green]")
            return

        table = Table(title="Pending Review Items", header_style="bold yellow")
        table.add_column("Task ID", style="dim")
        table.add_column("Reason", style="bold")
        table.add_column("Due / Created")

        for t in tasks:
            reason = t.payload_json.get("reason", "Unknown reason") if t.payload_json else "Unknown"
            time_str = t.due_at.strftime("%Y-%m-%d %H:%M") if t.due_at else "Immediate"
            table.add_row(str(t.id)[:8] + "...", reason, time_str)

        console.print(table)


@cli.command(name="assisted-apply")
@click.option("--job-id", type=str, default=None, help="Specific Job ID to apply for.")
@click.option("--packet-id", type=str, default=None, help="Specific Application Packet ID.")
@click.option(
    "--next", "pick_next", is_flag=True, default=False, help="Pick next prepared shortlisted job."
)
@click.option(
    "--mock-browser",
    is_flag=True,
    default=False,
    help="Use mock browser runner for testing/offline.",
)
@click.option(
    "--auto-confirm",
    is_flag=True,
    default=False,
    help="Confirm submission without interactive pause.",
)
@click.option(
    "--receipt", type=str, default=None, help="Optional submission receipt or confirmation message."
)
@click.option("--config-dir", default="config", help="Path to config directory.")
def assisted_apply(
    job_id: str | None,
    packet_id: str | None,
    pick_next: bool,
    mock_browser: bool,
    auto_confirm: bool,
    receipt: str | None,
    config_dir: str,
) -> None:
    """Execute assisted application flow with safe prefilling and human review checkpoint."""
    console.print(Panel.fit("[bold blue]Jobs Automation — Assisted Application Runner[/bold blue]"))

    loader = ConfigLoader(config_dir)
    profile, _ = loader.load_candidate_profile()
    policy_cfg, _ = loader.load_policy_registry()

    from sqlalchemy import select

    from jobs_automation.browser.assisted_engine import AssistedApplicationEngine
    from jobs_automation.browser.mock_runner import MockBrowserRunner
    from jobs_automation.browser.playwright_runner import PlaywrightBrowserRunner
    from jobs_automation.db.models import ApplicationModel, ApplicationPacketModel, JobModel
    from jobs_automation.policy.evaluator import PolicyEvaluator

    settings = AppSettings()
    engine = get_engine(settings.database_url)
    session_factory = get_sessionmaker(engine)

    with session_factory() as session:
        target_job_id: uuid.UUID | None = uuid.UUID(job_id) if job_id else None
        target_packet_id: uuid.UUID | None = uuid.UUID(packet_id) if packet_id else None

        if target_job_id is None and pick_next:
            # Find next shortlisted job that has a packet and no completed application
            stmt = (
                select(ApplicationPacketModel)
                .join(JobModel, ApplicationPacketModel.job_id == JobModel.id)
                .outerjoin(ApplicationModel, ApplicationModel.job_id == JobModel.id)
                .where(
                    JobModel.status.in_(["shortlisted", "packet_prepared"]),
                    (ApplicationModel.status.is_(None)) | (ApplicationModel.status != "SUBMITTED"),
                )
                .order_by(ApplicationPacketModel.created_at.desc())
                .limit(1)
            )
            pkt = session.scalar(stmt)
            if pkt:
                target_job_id = pkt.job_id
                target_packet_id = pkt.id
            else:
                console.print(
                    "[yellow]No eligible shortlisted jobs with packets waiting for application.[/yellow]"
                )
                return

        if target_job_id is None:
            console.print(
                "[red]Please specify --job-id <uuid> or use --next to pick the highest priority job.[/red]"
            )
            return

        policy_evaluator = PolicyEvaluator(policy_cfg)
        runner = MockBrowserRunner() if mock_browser else PlaywrightBrowserRunner(headless=False)

        assisted_engine = AssistedApplicationEngine(
            session=session,
            policy_evaluator=policy_evaluator,
            browser_runner=runner,
            candidate_profile=profile,
        )

        plan = assisted_engine.build_plan(job_id=target_job_id, packet_id=target_packet_id)

        console.print(f"Target: [bold]{plan.job_title}[/bold] at [cyan]{plan.company_name}[/cyan]")
        console.print(
            f"Destination: [underline]{plan.apply_url}[/underline] ([dim]{plan.destination_domain}[/dim])"
        )
        console.print(
            f"Policy Decision: [bold]{plan.policy.decision.value.upper()}[/bold] ({plan.policy.reason})"
        )
        console.print(f"Instructions: {plan.instructions}\n")

        if plan.unresolved_questions:
            console.print(
                "[bold yellow]⚠️  Unresolved screening questions exist for this job:[/bold yellow]"
            )
            for uq in plan.unresolved_questions:
                console.print(f"  • {uq}")
            console.print()

        res = assisted_engine.execute(
            job_id=target_job_id,
            packet_id=target_packet_id,
            auto_confirm=auto_confirm,
            receipt_text=receipt,
        )

        if res.status == "SUBMITTED":
            console.print(
                "[bold green]✅ Application Successfully Submitted & Recorded![/bold green]"
            )
            console.print(f"  Application ID: [dim]{res.application_id}[/dim]")
            console.print(f"  Receipt: [cyan]{res.receipt_text}[/cyan]")
            console.print(f"  Prefilled Fields: [dim]{res.prefilled_count}[/dim]")
        elif res.status == "MANUAL_RECORDED":
            console.print("[bold green]✅ Manual Application Confirmed & Recorded![/bold green]")
            console.print(f"  Application ID: [dim]{res.application_id}[/dim]")
        elif res.status == "REVIEW_REQUIRED":
            console.print("[bold yellow]⏸️  Review Required / Prefill Complete[/bold yellow]")
            console.print(f"  Status: {res.status}")
            console.print(f"  Message: {res.message}")
        elif res.status == "BLOCKED":
            console.print("[bold red]🚫 Submission Blocked by Policy[/bold red]")
            console.print(f"  Message: {res.message}")
        elif res.status == "ALREADY_SUBMITTED":
            console.print("[bold cyan]ℹ️  Already Submitted (Idempotent Guard)[/bold cyan]")
            console.print(f"  Message: {res.message}")


@cli.command(name="auto-apply")
@click.option("--job-id", type=str, default=None, help="Specific Job ID to apply for.")
@click.option("--packet-id", type=str, default=None, help="Specific Application Packet ID.")
@click.option(
    "--next", "pick_next", is_flag=True, default=False, help="Pick next prepared shortlisted job."
)
@click.option("--mock-mode", is_flag=True, default=True, help="Run with simulated ATS submission.")
@click.option(
    "--kill-switch", is_flag=True, default=False, help="Force trigger global kill switch."
)
@click.option("--config-dir", default="config", help="Path to config directory.")
def auto_apply(
    job_id: str | None,
    packet_id: str | None,
    pick_next: bool,
    mock_mode: bool,
    kill_switch: bool,
    config_dir: str,
) -> None:
    """Execute controlled automated application to allowlisted ATS platforms."""
    console.print(
        Panel.fit("[bold blue]Jobs Automation — Controlled Auto-Apply Engine[/bold blue]")
    )

    loader = ConfigLoader(config_dir)
    profile, _ = loader.load_candidate_profile()
    policy_cfg, _ = loader.load_policy_registry()

    from sqlalchemy import select

    from jobs_automation.automation.auto_engine import ControlledAutoApplicationEngine
    from jobs_automation.automation.kill_switch import KillSwitchManager
    from jobs_automation.db.models import ApplicationModel, ApplicationPacketModel, JobModel

    settings = AppSettings()
    engine = get_engine(settings.database_url)
    session_factory = get_sessionmaker(engine)

    with session_factory() as session:
        target_job_id: uuid.UUID | None = uuid.UUID(job_id) if job_id else None
        target_packet_id: uuid.UUID | None = uuid.UUID(packet_id) if packet_id else None

        if target_job_id is None and pick_next:
            stmt = (
                select(ApplicationPacketModel)
                .join(JobModel, ApplicationPacketModel.job_id == JobModel.id)
                .outerjoin(ApplicationModel, ApplicationModel.job_id == JobModel.id)
                .where(
                    JobModel.status.in_(["shortlisted", "packet_prepared"]),
                    (ApplicationModel.status.is_(None)) | (ApplicationModel.status != "SUBMITTED"),
                )
                .order_by(ApplicationPacketModel.created_at.desc())
                .limit(1)
            )
            pkt = session.scalar(stmt)
            if pkt:
                target_job_id = pkt.job_id
                target_packet_id = pkt.id
            else:
                console.print(
                    "[yellow]No eligible shortlisted jobs with packets waiting for application.[/yellow]"
                )
                return

        if target_job_id is None:
            console.print("[red]Please specify --job-id <uuid> or use --next.[/red]")
            return

        policy_evaluator = PolicyEvaluator(policy_cfg)
        ks_manager = KillSwitchManager(
            global_override=True if kill_switch else None, policy_config=policy_cfg
        )

        auto_engine = ControlledAutoApplicationEngine(
            session=session,
            policy_evaluator=policy_evaluator,
            candidate_profile=profile,
            kill_switch=ks_manager,
        )

        res = auto_engine.execute_auto_apply(
            job_id=target_job_id,
            packet_id=target_packet_id,
            mock_mode=mock_mode,
        )

        if res.status == "SUBMITTED":
            console.print(
                "[bold green]✅ Application Successfully Submitted Automatically![/bold green]"
            )
            console.print(f"  Platform: [bold]{res.platform}[/bold]")
            console.print(f"  Receipt ID: [cyan]{res.receipt_id}[/cyan]")
            console.print(f"  Confirmation URL: [underline]{res.confirmation_url}[/underline]")
            console.print(f"  Retries Performed: {res.retries_performed}")
        elif res.status == "SIMULATED":
            console.print(
                "[bold cyan]🧪 Application Successfully Simulated (Mock Mode)[/bold cyan]"
            )
            console.print(f"  Platform: [bold]{res.platform}[/bold]")
            console.print(f"  Simulated Receipt ID: [cyan]{res.receipt_id}[/cyan]")
            console.print(
                "  [dim]Note: External submission was NOT performed and cannot masquerade as real submission.[/dim]"
            )
        elif res.status == "NOT_IMPLEMENTED":
            console.print(
                f"[bold yellow]⚠️  Live submission not yet implemented:[/bold yellow] {res.message}"
            )
        elif res.status == "KILL_SWITCH_ACTIVE":
            console.print("[bold red]🛑 Aborted: Kill switch is active[/bold red]")
            console.print(f"  Message: {res.message}")
        elif res.status == "STOPPED_UNKNOWN_QUESTION":
            console.print("[bold yellow]⚠️  Stopped on unknown required question[/bold yellow]")
            console.print(f"  Message: {res.message}")
        elif res.status == "RATE_LIMITED":
            console.print("[bold yellow]⏱️  Rate limited[/bold yellow]")
            console.print(f"  Message: {res.message}")
        elif res.status == "BLOCKED":
            console.print("[bold red]🚫 Blocked by policy[/bold red]")
            console.print(f"  Message: {res.message}")
        elif res.status == "ALREADY_SUBMITTED":
            console.print("[bold cyan]ℹ️  Already submitted (Idempotent)[/bold cyan]")
            console.print(f"  Message: {res.message}")
        else:
            console.print(f"[bold red]❌ Submission failed:[/bold red] {res.message}")


@cli.command(name="lifecycle-status")
def lifecycle_status() -> None:
    """Display current application lifecycle pipeline stages, interviews, and activity."""
    console.print(
        Panel.fit("[bold blue]Jobs Automation — Application Lifecycle Pipeline[/bold blue]")
    )

    from sqlalchemy import select

    from jobs_automation.db.models import ApplicationModel

    settings = AppSettings()
    engine = get_engine(settings.database_url)
    session_factory = get_sessionmaker(engine)

    with session_factory() as session:
        stmt = select(ApplicationModel).order_by(ApplicationModel.last_activity_at.desc())
        apps = session.scalars(stmt).all()

        if not apps:
            console.print("[yellow]No tracked applications found in database.[/yellow]")
            return

        table = Table(title="Active Applications Pipeline", header_style="bold green")
        table.add_column("Company", style="bold")
        table.add_column("Title")
        table.add_column("Status", style="bold")
        table.add_column("Mode", style="dim")
        table.add_column("Applied Date")
        table.add_column("Interviews")

        for app in apps:
            co = app.job.company_name if app.job else "Unknown"
            title = app.job.title if app.job else "Unknown"
            applied_str = app.applied_at.strftime("%Y-%m-%d") if app.applied_at else "Pending"
            int_count = len(app.interviews) if app.interviews else 0
            int_str = (
                f"[bold green]{int_count} scheduled[/bold green]"
                if int_count > 0
                else "[dim]0[/dim]"
            )

            status_style = {
                "SUBMITTED": "[cyan]SUBMITTED[/cyan]",
                "CONFIRMED": "[blue]CONFIRMED[/blue]",
                "SCREENING": "[yellow]SCREENING[/yellow]",
                "INTERVIEWING": "[bold green]INTERVIEWING[/bold green]",
                "OFFER_RECEIVED": "[bold magenta]OFFER RECEIVED[/bold magenta]",
                "REJECTED": "[dim red]REJECTED[/dim red]",
            }.get(app.status, app.status)

            table.add_row(co, title, status_style, app.application_mode, applied_str, int_str)

        console.print(table)


@cli.command(name="contacts")
def contacts_crm() -> None:
    """List recruiter and hiring manager CRM contact records."""
    console.print(Panel.fit("[bold blue]Jobs Automation — Recruiter CRM Directory[/bold blue]"))

    from sqlalchemy import select

    from jobs_automation.db.models import ContactModel

    settings = AppSettings()
    engine = get_engine(settings.database_url)
    session_factory = get_sessionmaker(engine)

    with session_factory() as session:
        contacts = session.scalars(
            select(ContactModel).order_by(ContactModel.last_contact_at.desc().nulls_last())
        ).all()

        if not contacts:
            console.print("[yellow]No recruiter contacts recorded yet.[/yellow]")
            return

        table = Table(title="Recruiter & Hiring Team Contacts", header_style="bold cyan")
        table.add_column("Name", style="bold")
        table.add_column("Email")
        table.add_column("Role")
        table.add_column("Company")
        table.add_column("Last Contact")

        for c in contacts:
            co = c.company.normalized_name if c.company else "Unknown"
            last_dt = c.last_contact_at.strftime("%Y-%m-%d") if c.last_contact_at else "Never"
            table.add_row(c.name, c.email or "[dim]N/A[/dim]", c.role or "Recruiter", co, last_dt)

        console.print(table)


@cli.command(name="update-lifecycle")
def update_lifecycle() -> None:
    """Sweep recruiting messages, trigger lifecycle transitions, and check follow-up alerts."""
    console.print(
        Panel.fit("[bold blue]Jobs Automation — Lifecycle & Communication Engine[/bold blue]")
    )

    from sqlalchemy import select

    from jobs_automation.db.models import InboundMessageModel
    from jobs_automation.lifecycle.alerts import LifecycleAlertService
    from jobs_automation.lifecycle.engine import LifecycleEngine

    settings = AppSettings()
    engine = get_engine(settings.database_url)
    session_factory = get_sessionmaker(engine)

    with session_factory() as session:
        lifecycle_engine = LifecycleEngine(session)
        alert_service = LifecycleAlertService(session)

        # Process recruiting messages
        messages = session.scalars(
            select(InboundMessageModel)
            .where(InboundMessageModel.classification != "JOB_ALERT")
            .order_by(InboundMessageModel.received_at.asc())
        ).all()

        transitions_count = 0
        interviews_count = 0

        for msg in messages:
            res = lifecycle_engine.process_message(msg)
            if res:
                transitions_count += 1
                if res.interview_scheduled:
                    interviews_count += 1

        # Check follow-up alerts
        unanswered_tasks = alert_service.check_unanswered_recruiters()
        stale_tasks = alert_service.check_stale_applications()

        session.commit()

        console.print(f"  • Messages processed: [bold]{len(messages)}[/bold]")
        console.print(
            f"  • Lifecycle state transitions: [bold green]{transitions_count}[/bold green]"
        )
        console.print(
            f"  • Interviews scheduled / extracted: [bold cyan]{interviews_count}[/bold cyan]"
        )
        console.print(
            f"  • Unanswered recruiter alerts created: [bold yellow]{len(unanswered_tasks)}[/bold yellow]"
        )
        console.print(
            f"  • Stale application reminders created: [bold magenta]{len(stale_tasks)}[/bold magenta]"
        )


@cli.command(name="dashboard")
@click.option("--host", default="127.0.0.1", help="Host interface to bind dashboard.")
@click.option("--port", default=8765, type=int, help="Port to run dashboard (default: 8765).")
def dashboard(host: str, port: int) -> None:
    """Launch embedded interactive web dashboard and REST API."""
    console.print(
        Panel.fit(
            f"[bold blue]Jobs Automation — Web Dashboard & Analytics[/bold blue]\n[green]http://{host}:{port}[/green]"
        )
    )
    from jobs_automation.dashboard.server import DashboardServer

    settings = AppSettings()
    engine = get_engine(settings.database_url)
    session_factory = get_sessionmaker(engine)

    server = DashboardServer(session_factory, host=host, port=port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping dashboard server...[/yellow]")
        server.shutdown()


@cli.command(name="health-check")
def health_check() -> None:
    """Run system readiness and diagnostic health checks."""
    console.print(
        Panel.fit(
            "[bold blue]Jobs Automation — System Diagnostics & Health Check[/bold blue]"
        )
    )
    from jobs_automation.health import HealthCheckService

    settings = AppSettings()
    engine = get_engine(settings.database_url)
    session_factory = get_sessionmaker(engine)

    checker = HealthCheckService(session_factory)
    report = checker.run_full_check()

    table = Table(title="System Component Status", header_style="bold cyan")
    table.add_column("Component", style="bold")
    table.add_column("Status")
    table.add_column("Latency")
    table.add_column("Diagnostics")

    for name, comp in report.components.items():
        status_color = (
            "green"
            if comp.status == "HEALTHY"
            else ("yellow" if comp.status == "DEGRADED" else "red")
        )
        latency_str = f"{comp.latency_ms:.1f}ms" if comp.latency_ms > 0 else "-"
        table.add_row(
            name,
            f"[{status_color}]{comp.status}[/{status_color}]",
            latency_str,
            comp.message,
        )

    console.print(table)
    overall_color = (
        "green"
        if report.overall_status == "HEALTHY"
        else ("yellow" if report.overall_status == "DEGRADED" else "red")
    )
    console.print(
        f"Overall System State: [{overall_color} bold]{report.overall_status}[/{overall_color} bold]\n"
    )


@cli.command(name="worker")
@click.option("--once", is_flag=True, default=False, help="Run single sweep cycle and exit.")
@click.option(
    "--interval",
    default=14400,
    type=int,
    help="Polling interval in seconds (default: 14400 / 4h).",
)
@click.option(
    "--mock-fixtures",
    is_flag=True,
    default=False,
    help="Use offline test fixtures for email polling instead of live Gmail.",
)
@click.option("--config-dir", default="config", help="Path to config directory.")
@click.option(
    "--reconcile",
    is_flag=True,
    default=False,
    help="Force 48-hour reconciliation pass for single sweep.",
)
def worker(once: bool, interval: int, mock_fixtures: bool, config_dir: str, reconcile: bool) -> None:
    """Run scheduled background worker for ingestion, lifecycle updates, and alerting."""
    console.print(Panel.fit("[bold blue]Jobs Automation — Scheduled Worker Daemon[/bold blue]"))
    from jobs_automation.worker import WorkerDaemon

    email_adapter = None
    if mock_fixtures:
        from jobs_automation.adapters.gmail import MockEmailAdapter
        from jobs_automation.ingestion.fixtures import get_sample_email_fixtures

        console.print("[dim cyan]Running worker with offline test fixtures adapter...[/dim cyan]")
        email_adapter = MockEmailAdapter(get_sample_email_fixtures())

    settings = AppSettings()
    engine = get_engine(settings.database_url)
    session_factory = get_sessionmaker(engine)

    daemon = WorkerDaemon(
        session_factory,
        poll_interval_seconds=interval,
        config_dir=config_dir,
        email_adapter=email_adapter,
    )
    if once:
        res = daemon.run_sweep(reconcile=True if reconcile else None)
        console.print(f"[green]Sweep finished:[/green] {res}")
    else:
        daemon.start()


if __name__ == "__main__":
    cli()


