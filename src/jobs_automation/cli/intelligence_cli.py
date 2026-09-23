import click
from rich.console import Console
from rich.json import JSON
from jobs_automation.db.session import get_sessionmaker
from jobs_automation.intelligence.edges import backfill_message_link_contacts

console = Console()

@click.group(name="intel")
def intel_cli() -> None:
    """Intelligence and Graph commands."""
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

