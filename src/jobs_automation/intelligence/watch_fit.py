"""V23-TW-05: Fit scoring, suppression, and paused semantics for watch observations.

Extends WatchRunner with role family classification, hard filter evaluation,
semantic scoring, application suppression, and task creation for shortlisted roles.
"""

from __future__ import annotations

import datetime
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from jobs_automation.db.base import utc_now
from jobs_automation.db.models import (
    ApplicationModel,
    JobModel,
    TargetCompanyModel,
    TargetCompanyObservationModel,
    TaskModel,
)
from jobs_automation.intelligence.role_family import RoleFamilyClassifier

logger = logging.getLogger(__name__)


class WatchFitEvaluator:
    """Evaluates fit for NEW_ROLE observations and manages suppression/task creation."""

    def __init__(
        self,
        session: Session,
        classifier: RoleFamilyClassifier | None = None,
    ) -> None:
        self.session = session
        self.classifier = classifier or RoleFamilyClassifier()

    def evaluate_new_role(
        self,
        observation: TargetCompanyObservationModel,
        target: TargetCompanyModel,
        job: JobModel | None = None,
    ) -> dict:
        """Evaluate fit for a NEW_ROLE observation.

        Returns a fit dict to be stored in observation.normalized_payload['fit'].
        Side effects:
        - Sets observation.status = 'SUPPRESSED' if an application already exists
        - Creates a TaskModel(task_type='TARGET_COMPANY_NEW_ROLE') if shortlisted
        """
        payload = observation.normalized_payload or {}
        title = payload.get("title", "")

        fit: dict = {
            "role_family": None,
            "role_family_match": False,
            "decision": "REVIEW",
        }

        # 1. Role family classification
        classified_family = self.classifier.classify(title)
        fit["role_family"] = classified_family

        # Check if family matches target's desired families
        target_families = target.target_role_families or []
        if isinstance(target_families, list) and classified_family in target_families:
            fit["role_family_match"] = True

        # 2. Check if already applied (suppression)
        if job and self._has_application(job.id):
            observation.status = "SUPPRESSED"
            fit["decision"] = "SUPPRESSED"
            fit["suppression_reason"] = "existing_application"
            return fit

        # 3. Basic decision logic
        if fit["role_family_match"]:
            fit["decision"] = "SHORTLIST"
        elif classified_family == "other":
            fit["decision"] = "REVIEW"
        else:
            # Known family but not in target list
            fit["decision"] = "REVIEW"

        # 4. Create task for shortlisted items (only for ACTIVE targets)
        if fit["decision"] == "SHORTLIST" and target.watch_status == "ACTIVE":
            self._create_review_task_if_needed(observation, job)

        return fit

    def _has_application(self, job_id: uuid.UUID) -> bool:
        """Check if there's an existing application for this job."""
        app = self.session.scalars(
            select(ApplicationModel).where(ApplicationModel.job_id == job_id).limit(1)
        ).first()
        return app is not None

    def _create_review_task_if_needed(
        self,
        observation: TargetCompanyObservationModel,
        job: JobModel | None,
    ) -> TaskModel | None:
        """Create a TARGET_COMPANY_NEW_ROLE task if no pending task exists."""
        job_id = observation.job_id or (job.id if job else None)
        if not job_id:
            return None

        # Check for existing pending task for this job
        existing = self.session.scalars(
            select(TaskModel).where(
                TaskModel.job_id == job_id,
                TaskModel.task_type == "TARGET_COMPANY_NEW_ROLE",
                TaskModel.status == "pending",
            ).limit(1)
        ).first()

        if existing:
            return None

        task = TaskModel(
            job_id=job_id,
            task_type="TARGET_COMPANY_NEW_ROLE",
            status="pending",
            payload_json={
                "target_company_id": str(observation.target_company_id),
                "observation_id": str(observation.id),
                "title": (observation.normalized_payload or {}).get("title", ""),
                "channel": "watch_runner",
            },
        )
        self.session.add(task)
        self.session.flush()
        return task
