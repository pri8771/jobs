"""Evaluation module for hard filtering and semantic scoring."""

from jobs_automation.evaluation.engine import EvaluationRunSummary, JobEvaluationEngine
from jobs_automation.evaluation.filters import FilterDecisionStatus, FilterResult, HardFilterService
from jobs_automation.evaluation.scorer import DimensionScore, EvaluationScoreResult, SemanticScorer

__all__ = [
    "DimensionScore",
    "EvaluationRunSummary",
    "EvaluationScoreResult",
    "FilterDecisionStatus",
    "FilterResult",
    "HardFilterService",
    "JobEvaluationEngine",
    "SemanticScorer",
]
