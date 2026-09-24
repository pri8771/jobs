"""V23 Agent Tool Registry (V23-TL-02).

Manages tool registrations, lookup, and JSON schema export for tool specifications.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from pydantic import BaseModel
from sqlalchemy.orm import Session

from jobs_automation.intelligence.envelope import EvidenceRef
from jobs_automation.tools.envelope import ActionClass, PermissionContext, ToolStatus


@dataclass
class ToolHandlerResult:
    payload_model: BaseModel
    status: ToolStatus = ToolStatus.SUCCEEDED
    warnings: list[str] = None
    review_needs: list[str] = None
    entity_refs: list[EvidenceRef] = None
    evidence_refs: list[EvidenceRef] = None
    external_reference: str | None = None
    simulated: bool = False

    def __post_init__(self) -> None:
        if self.warnings is None:
            self.warnings = []
        if self.review_needs is None:
            self.review_needs = []
        if self.entity_refs is None:
            self.entity_refs = []
        if self.evidence_refs is None:
            self.evidence_refs = []


@dataclass
class ToolSpec:
    name: str
    version: str
    action_class: ActionClass
    capability: str | None
    input_model: type[BaseModel]
    output_model: type[BaseModel]
    handler: Callable[[Session, Any, PermissionContext], ToolHandlerResult]
    requires_destination: bool = False


class ToolRegistry:
    """Registry for discovering and invoking typed agent tools."""

    def __init__(self) -> None:
        self._specs: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        """Register a tool spec. Raises ValueError if (name, version) already registered."""
        key = f"{spec.name}:{spec.version}"
        if key in self._specs:
            raise ValueError(f"Tool already registered: {key}")
        self._specs[key] = spec

    def get(self, name: str, version: str = "1.0") -> ToolSpec | None:
        """Retrieve a registered ToolSpec by name and version."""
        key = f"{name}:{version}"
        return self._specs.get(key)

    def list(self) -> list[ToolSpec]:
        """List all registered ToolSpecs."""
        return list(self._specs.values())

    def describe(self) -> list[dict[str, Any]]:
        """Return JSON schema descriptions for all registered tools."""
        descriptions: list[dict[str, Any]] = []
        for spec in self._specs.values():
            descriptions.append({
                "name": spec.name,
                "version": spec.version,
                "action_class": spec.action_class.value,
                "capability": spec.capability,
                "requires_destination": spec.requires_destination,
                "input_schema": spec.input_model.model_json_schema(),
                "output_schema": spec.output_model.model_json_schema(),
            })
        return descriptions
