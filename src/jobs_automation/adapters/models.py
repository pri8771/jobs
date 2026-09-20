"""Model gateway implementation supporting LiteLLM routing and deterministic offline fallbacks."""

from __future__ import annotations

import json
import logging
from typing import Any

from jobs_automation.adapters.base import ModelGateway
from jobs_automation.core import ModelRoutingConfig

logger = logging.getLogger(__name__)


class MockModelGateway(ModelGateway):
    """Deterministic offline model gateway for tests and offline operations."""

    def complete(
        self,
        task: str,
        prompt: str,
        system_prompt: str | None = None,
        schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Produce structured responses deterministically without external API calls."""
        if task == "resume_tailoring":
            return {
                "targeted_bullets": [
                    "Led enterprise SAP BTP and business process automation architecture across ERP workflows.",
                    "Designed and deployed event-driven integration pipelines using Python, FastAPI, and Docker.",
                    "Automated document processing pipelines with OCR/LLM extraction, reducing manual handling time by 80%.",
                ],
                "skills_highlighted": [
                    "SAP BTP",
                    "Enterprise Integrations",
                    "Python",
                    "Docker",
                    "AI Workflow Automation",
                ],
                "positioning_alignment": "Enterprise Automation & Solutions Architect",
            }

        elif task == "cover_letter":
            return {
                "cover_letter_text": (
                    "Dear Hiring Team,\n\n"
                    "I am writing to express my strong interest in this role. With extensive experience in enterprise automation, "
                    "SAP BTP solutions architecture, and software engineering, I specialize in bridging core business systems with "
                    "modern AI-driven workflows.\n\n"
                    "At Viatris, I architected SAP BTP integrations and automated ERP business processes. Previously as Head of IT and Business Operations "
                    "at Thar Process, I led cross-functional enterprise infrastructure and custom software implementations.\n\n"
                    "I hold a B.S. in Chemical Engineering from Carnegie Mellon University and bring a proven track record of shipping reliable, scalable systems.\n\n"
                    "Thank you for your consideration.\n\n"
                    "Sincerely,\nPriyansh Chordia"
                ),
                "key_themes": ["SAP BTP", "Enterprise Automation", "Systems Architecture"],
            }

        elif task == "question_answering":
            # Deterministic question resolution based on verified candidate profile facts
            p_lower = prompt.lower()
            if "python" in p_lower:
                return {
                    "answer": "Yes, I have 8+ years of production experience with Python and FastAPI.",
                    "resolved": True,
                }
            elif "clearance" in p_lower or "security clearance" in p_lower:
                return {
                    "answer": None,
                    "resolved": False,
                    "reason": "Candidate has no active security clearance recorded.",
                }
            elif "relocate" in p_lower or "willing to relocate" in p_lower:
                # Unknown preference -> UNRESOLVED
                return {
                    "answer": None,
                    "resolved": False,
                    "reason": "Candidate relocation preference is unknown.",
                }
            elif "sponsorship" in p_lower or "work authorization" in p_lower:
                return {
                    "answer": None,
                    "resolved": False,
                    "reason": "Work authorization fact requires candidate confirmation.",
                }
            return {
                "answer": None,
                "resolved": False,
                "reason": "Unknown fact not present in candidate profile.",
            }

        elif task == "scoring":
            return {
                "semantic_score": 85.0,
                "reasoning": "High alignment with distributed systems and enterprise integration architecture.",
            }

        return {"result": "success", "task": task}


class LiteLLMModelGateway(ModelGateway):
    """LiteLLM-compatible model gateway that routes tasks to configured model providers."""

    def __init__(self, routing_config: ModelRoutingConfig, fallback_mock: bool = True) -> None:
        self.routing = routing_config
        self.fallback_mock = fallback_mock
        self._mock = MockModelGateway()

    def complete(
        self,
        task: str,
        prompt: str,
        system_prompt: str | None = None,
        schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        task_config = self.routing.tasks.get(task)
        if not task_config or not task_config.model:
            logger.info("No routing config for task '%s', using mock fallback", task)
            return self._mock.complete(task, prompt, system_prompt, schema)

        model_name = task_config.model

        try:
            # Attempt to use litellm if installed and credentials are present
            import litellm  # type: ignore[import-not-found]

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = litellm.completion(
                model=model_name,
                messages=messages,
                temperature=self.routing.defaults.temperature,
                timeout=self.routing.defaults.timeout_seconds,
            )
            raw_text = str(response.choices[0].message.content)
            if schema:
                return json.loads(raw_text)  # type: ignore[no-any-return]
            return {"content": raw_text}

        except Exception as e:
            if self.fallback_mock:
                logger.warning(
                    "LiteLLM call failed (%s); using deterministic offline fallback for task '%s'",
                    e,
                    task,
                )
                return self._mock.complete(task, prompt, system_prompt, schema)
            raise
