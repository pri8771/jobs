from typing import Protocol
from jobs_automation.ingestion.sources.base import PublicJobSource
from jobs_automation.ingestion.sources.greenhouse_board import GreenhouseBoardSource
from jobs_automation.ingestion.sources.lever_postings import LeverPostingsSource

def get_source(provider: str) -> PublicJobSource:
    provider_upper = provider.upper()
    if provider_upper == "GREENHOUSE":
        return GreenhouseBoardSource()
    elif provider_upper == "LEVER":
        return LeverPostingsSource()
    else:
        raise KeyError(f"Unknown job source provider: {provider}")
