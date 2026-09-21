"""Intelligence module for opportunity graph, target company watch, and strategy learning."""

from jobs_automation.intelligence.opportunity_graph import (
    CompanyContactRecord,
    CompanyOpportunityRecord,
    ContactApplicationRecord,
    EdgeStatus,
    NodeType,
    OpportunityEdge,
    OpportunityGraph,
    OpportunityGraphService,
    OpportunityNode,
    OpportunitySignalRecord,
    Predicate,
    ReferralPathRecord,
    ResumeOutcomeRecord,
)

__all__ = [
    "NodeType",
    "Predicate",
    "EdgeStatus",
    "OpportunityNode",
    "OpportunityEdge",
    "OpportunityGraph",
    "OpportunityGraphService",
    "CompanyOpportunityRecord",
    "CompanyContactRecord",
    "ContactApplicationRecord",
    "ResumeOutcomeRecord",
    "OpportunitySignalRecord",
    "ReferralPathRecord",
]
