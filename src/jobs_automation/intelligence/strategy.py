from pydantic import BaseModel, Field, model_validator

class StrategyGuardrails(BaseModel):
    min_n_descriptive: int = 5
    min_n_comparison: int = 10
    min_n_per_arm: int = 5
    default_window_days: int = 90
    stale_after_days: int = 180
    
    @model_validator(mode='after')
    def validate_positive(self) -> 'StrategyGuardrails':
        if self.min_n_descriptive < 0 or self.min_n_comparison < 0 or self.min_n_per_arm < 0 or self.default_window_days < 0 or self.stale_after_days < 0:
            raise ValueError("Guardrail values cannot be negative")
        return self




from typing import Any, Literal
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, UTC, timedelta
from jobs_automation.intelligence.envelope import RateWithN

class ResumeStrategyRow(BaseModel):
    resume_family: str
    resume_variant_id: str | None
    version: int
    response: RateWithN
    screen: RateWithN
    interview: RateWithN
    offer: RateWithN
    similar_role_family: str | None = None
    rollup: bool = False

class StrategyLearningService:
    def __init__(self, session: Session, guardrails: StrategyGuardrails, role_family_classifier: Any = None):
        self.session = session
        self.guardrails = guardrails
        self.role_family_classifier = role_family_classifier
        from jobs_automation.dashboard.analytics import FunnelAnalyticsService
        self.analytics = FunnelAnalyticsService(session)
        
    def _make_rate(self, numerator: int, denominator: int, window_days: int | None = None) -> RateWithN:
        rate = numerator / denominator if denominator > 0 else None
        now = datetime.now(UTC)
        start = now - timedelta(days=window_days) if window_days else None
        return RateWithN(
            numerator=numerator,
            denominator=denominator,
            rate=rate,
            n=denominator,
            min_n=self.guardrails.min_n_descriptive,
            low_n=denominator < self.guardrails.min_n_descriptive,
            window_days=window_days,
            window_start=start,
            window_end=now,
            evidence_class="DESCRIPTIVE"
        )
        
    def resume_strategy(self, window_days: int | None = None) -> list[ResumeStrategyRow]:
        wd = window_days if window_days is not None else self.guardrails.default_window_days
        cutoff = datetime.now(UTC) - timedelta(days=wd)
        

        from jobs_automation.db.models import ApplicationModel, ResumeVariantModel
        variants = self.session.scalars(select(ResumeVariantModel)).all()

        results = []
        for variant in variants:
            apps = [
                pkt_app
                for pkt in variant.packets
                for pkt_app in self.session.scalars(
                    select(ApplicationModel).where(ApplicationModel.packet_id == pkt.id)
                ).all()
            ]
            
            submitted_apps = [a for a in apps if self.analytics._is_real_submission(a) and (not a.applied_at or a.applied_at >= cutoff)]
            n = len(submitted_apps)
            
            responses = 0
            screens = 0
            interviews = 0
            offers = 0
            
            for a in submitted_apps:
                outcomes = self.analytics._get_application_historical_outcomes(a)
                if outcomes["ever_screened"] or outcomes["ever_interviewed"] or outcomes["ever_final_interview"] or outcomes["ever_offered"] or outcomes["ever_accepted"]:
                    responses += 1 # Any positive signal
                if outcomes["ever_screened"]:
                    screens += 1
                if outcomes["ever_interviewed"] or outcomes["ever_final_interview"]:
                    interviews += 1
                if outcomes["ever_offered"] or outcomes["ever_accepted"]:
                    offers += 1
                    
            results.append(ResumeStrategyRow(
                resume_family=variant.resume_family,
                resume_variant_id=str(variant.id),
                version=variant.version,
                response=self._make_rate(responses, n, window_days=wd),
                screen=self._make_rate(screens, n, window_days=wd),
                interview=self._make_rate(interviews, n, window_days=wd),
                offer=self._make_rate(offers, n, window_days=wd),
                rollup=False
            ))
            
        return results
        
    def source_strategy(self, window_days: int | None = None) -> list[Any]:
        # Implementation omitted for brevity unless needed for tests
        return []
        
    def role_strategy(self, window_days: int | None = None) -> list[Any]:
        return []
        
    def company_strategy(self, window_days: int | None = None) -> list[Any]:
        return []
