"""Model gateway implementation supporting LiteLLM routing and deterministic offline fallbacks."""

from __future__ import annotations

import json
import logging
from typing import Any

from jobs_automation.adapters.base import ModelGateway
from jobs_automation.core import ModelRoutingConfig

logger = logging.getLogger(__name__)


class DeterministicModelGateway(ModelGateway):
    """Production-safe zero-provider gateway.

    This gateway never fabricates semantic candidate facts. It is intended for
    privacy-preserving/local operation when no LLM provider is configured.

    - cover_letter returns empty generated content so CoverLetterDrafter uses
      its canonical-profile deterministic renderer.
    - question_answering always returns unresolved; deterministic application
      answers are still handled by ScreeningQuestionAnsweringService before the
      gateway is called.
    - unsupported semantic tasks fail closed rather than synthesize content.
    """

    def complete(
        self,
        task: str,
        prompt: str,
        system_prompt: str | None = None,
        schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if task == "cover_letter":
            return {
                "content": "",
                "origin": "deterministic",
                "model": "deterministic-canonical-renderer",
            }

        if task == "question_answering":
            return {
                "answer": None,
                "resolved": False,
                "reason": (
                    "No semantic model provider is configured. "
                    "Deterministic safe mode leaves unsupported questions unresolved."
                ),
                "origin": "deterministic",
                "model": "deterministic-safe-unresolved",
            }

        raise ValueError(
            f"Task '{task}' requires a configured semantic model provider; "
            "deterministic gateway fails closed."
        )


class MockModelGateway(ModelGateway):
    """Deterministic offline model gateway for tests and offline operations."""

    def complete(
        self,
        task: str,
        prompt: str,
        system_prompt: str | None = None,
        schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Produce structured synthetic responses deterministically without external API calls."""
        if task == "resume_tailoring":
            return {
                "targeted_bullets": [
                    "Engineered enterprise integration workflows connecting distributed systems.",
                    "Implemented asynchronous data pipelines using standard libraries and containers.",
                    "Automated document processing pipelines, optimizing manual throughput.",
                ],
                "skills_highlighted": [
                    "Systems Architecture",
                    "Enterprise Integrations",
                    "Python",
                    "Docker",
                    "Workflow Automation",
                ],
                "positioning_alignment": "Solutions Architect",
                "origin": "mock",
            }

        elif task == "cover_letter":
            return {
                "cover_letter_text": (
                    "Dear Hiring Team,\n\n"
                    "I am writing to express my interest in the position. With extensive experience in "
                    "software engineering, architecture, and workflow automation, I have a track record of delivering "
                    "reliable, scalable business solutions.\n\n"
                    "Thank you for your consideration.\n\n"
                    "Sincerely,\nCandidate"
                ),
                "key_themes": ["Workflow Automation", "Systems Architecture"],
                "origin": "mock",
            }

        elif task == "question_answering":
            p_lower = prompt.lower()
            if "clearance" in p_lower or "security clearance" in p_lower:
                return {
                    "answer": None,
                    "resolved": False,
                    "reason": "Candidate has no active security clearance recorded.",
                    "origin": "mock",
                }
            elif "relocate" in p_lower or "willing to relocate" in p_lower:
                return {
                    "answer": None,
                    "resolved": False,
                    "reason": "Candidate relocation preference is unknown.",
                    "origin": "mock",
                }
            elif "sponsorship" in p_lower or "work authorization" in p_lower:
                return {
                    "answer": None,
                    "resolved": False,
                    "reason": "Work authorization fact requires candidate confirmation.",
                    "origin": "mock",
                }
            return {
                "answer": None,
                "resolved": False,
                "reason": "Unknown fact not present in candidate profile.",
                "origin": "mock",
            }

        elif task == "scoring":
            return {
                "semantic_score": 85.0,
                "reasoning": "High alignment with technical requirements and system engineering.",
                "origin": "mock",
            }

        return {"result": "success", "task": task, "origin": "mock"}


class LiteLLMModelGateway(ModelGateway):
    """LiteLLM-compatible model gateway that routes tasks to configured model providers.

    Fails closed by default if routing or provider credentials are not configured.
    """

    def __init__(self, routing_config: ModelRoutingConfig, fallback_mock: bool = False) -> None:
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
            if not self.fallback_mock:
                raise ValueError(
                    f"No model routing configured for task '{task}' and fallback_mock is disabled."
                )
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
                parsed = json.loads(raw_text)
                if isinstance(parsed, dict):
                    parsed["origin"] = "real"
                    parsed["model"] = model_name
                return parsed  # type: ignore[no-any-return]
            return {"content": raw_text, "origin": "real", "model": model_name}

        except Exception as e:
            if self.fallback_mock:
                logger.warning(
                    "LiteLLM call failed (%s); using deterministic offline fallback for task '%s'",
                    e,
                    task,
                )
                return self._mock.complete(task, prompt, system_prompt, schema)
            raise

