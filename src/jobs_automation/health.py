"""System health check and diagnostic monitoring for Jobs Automation OS."""

from __future__ import annotations

import datetime
import time
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import func, select, text

from jobs_automation.automation.adapters import ATSAdapterRegistry
from jobs_automation.automation.kill_switch import KillSwitchManager
from jobs_automation.db.models import (
    PolicyRegistryModel,
    TaskModel,
)


class ComponentHealth(BaseModel):
    """Health status and diagnostic metrics for an individual component."""

    name: str
    status: str  # HEALTHY | DEGRADED | UNHEALTHY
    message: str
    latency_ms: float = 0.0
    details: dict[str, Any] = Field(default_factory=dict)


class HealthReport(BaseModel):
    """Consolidated system health report."""

    timestamp: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )
    overall_status: str  # HEALTHY | DEGRADED | UNHEALTHY
    components: dict[str, ComponentHealth] = Field(default_factory=dict)


class HealthCheckService:
    """Evaluates readiness, connectivity, security switches, and operational state."""

    def __init__(self, session_factory: Any) -> None:
        self.session_factory = session_factory

    def check_database(self) -> ComponentHealth:
        """Verifies database connectivity, query latency, and pending task load."""
        start = time.perf_counter()
        try:
            with self.session_factory() as session:
                session.execute(text("SELECT 1"))
                pending_tasks = (
                    session.scalar(
                        select(func.count(TaskModel.id)).where(
                            TaskModel.status == "pending"
                        )
                    )
                    or 0
                )
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            status = "HEALTHY" if elapsed_ms < 500 else "DEGRADED"
            return ComponentHealth(
                name="database",
                status=status,
                message=f"Connected in {elapsed_ms}ms, {pending_tasks} pending tasks in queue.",
                latency_ms=elapsed_ms,
                details={"pending_tasks": pending_tasks},
            )
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            return ComponentHealth(
                name="database",
                status="UNHEALTHY",
                message=f"Database connection failed: {exc}",
                latency_ms=elapsed_ms,
                details={"error": str(exc)},
            )

    def check_kill_switches(self) -> ComponentHealth:
        """Inspects global and per-platform safety kill switches."""
        ks = KillSwitchManager()
        global_killed, global_reason = ks.is_global_active()
        greenhouse_killed, _ = ks.is_platform_active("greenhouse")
        lever_killed, _ = ks.is_platform_active("lever")
        details = {
            "global_kill_switch_active": global_killed,
            "greenhouse_killed": greenhouse_killed,
            "lever_killed": lever_killed,
        }
        if global_killed:
            return ComponentHealth(
                name="kill_switches",
                status="DEGRADED",
                message=f"Global automation kill switch is ACTIVE: {global_reason}",
                details=details,
            )
        return ComponentHealth(
            name="kill_switches",
            status="HEALTHY",
            message="Kill switches nominal. Submissions permitted according to policy.",
            details=details,
        )

    def check_policy_registry(self) -> ComponentHealth:
        """Inspects policy registry for expired policy reviews."""
        try:
            with self.session_factory() as session:
                policies = session.scalars(select(PolicyRegistryModel)).all()
                now = datetime.datetime.now(datetime.UTC)
                expired: list[str] = []
                for p in policies:
                    if p.review_due_at and p.review_due_at < now:
                        expired.append(f"{p.platform} ({p.domain_pattern})")

                if expired:
                    return ComponentHealth(
                        name="policy_registry",
                        status="DEGRADED",
                        message=f"{len(expired)} platform policy reviews are expired.",
                        details={"expired_platforms": expired},
                    )

                return ComponentHealth(
                    name="policy_registry",
                    status="HEALTHY",
                    message=f"{len(policies)} platform policies verified and up to date.",
                    details={"total_policies": len(policies)},
                )
        except Exception as exc:
            return ComponentHealth(
                name="policy_registry",
                status="UNHEALTHY",
                message=f"Failed to query policy registry: {exc}",
                details={"error": str(exc)},
            )

    def check_adapters(self) -> ComponentHealth:
        """Inspects availability of registered automated ATS adapters."""
        registry = ATSAdapterRegistry()
        adapters = registry.registered_platforms
        if not adapters:
            return ComponentHealth(
                name="adapters",
                status="DEGRADED",
                message="No ATS adapters registered in registry.",
                details={"registered_platforms": []},
            )
        return ComponentHealth(
            name="adapters",
            status="HEALTHY",
            message=f"{len(adapters)} ATS adapter platforms registered and active.",
            details={"registered_platforms": adapters},
        )

    def run_full_check(self) -> HealthReport:
        """Executes all diagnostics and returns consolidated health report."""
        components = {
            "database": self.check_database(),
            "kill_switches": self.check_kill_switches(),
            "policy_registry": self.check_policy_registry(),
            "adapters": self.check_adapters(),
        }

        # Calculate overall status
        statuses = [c.status for c in components.values()]
        if "UNHEALTHY" in statuses:
            overall = "UNHEALTHY"
        elif "DEGRADED" in statuses:
            overall = "DEGRADED"
        else:
            overall = "HEALTHY"

        return HealthReport(overall_status=overall, components=components)
