"""Master configuration loader and application settings."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

from jobs_automation.core.candidate_profile import CandidateProfileConfig
from jobs_automation.core.job_search import JobSearchConfig
from jobs_automation.core.model_routing import ModelRoutingConfig
from jobs_automation.core.platforms import PlatformsConfig
from jobs_automation.core.policy_registry import PolicyRegistryConfig


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://jobs:jobs@localhost:5432/jobs"
    gmail_client_id: str | None = None
    gmail_client_secret: str | None = None
    gmail_token_path: str = ".local/gmail_token.json"
    model_gateway_base_url: str | None = None
    model_gateway_api_key: str | None = None
    log_level: str = "INFO"
    environment: str = "development"


class ConfigValidationReport:
    def __init__(self) -> None:
        self.success: bool = True
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.unresolved_facts: dict[str, list[str]] = {}
        self.loaded_files: dict[str, str] = {}

    def add_error(self, message: str) -> None:
        self.success = False
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)


class ConfigLoader:
    def __init__(self, config_dir: str | Path = "config") -> None:
        self.config_dir = Path(config_dir)

    def _resolve_file(self, base_name: str) -> Path:
        """Resolve a configuration file path, checking for primary and example fallbacks."""
        primary = self.config_dir / f"{base_name}.yaml"
        if primary.exists():
            return primary
        example = self.config_dir / f"{base_name}.example.yaml"
        if example.exists():
            return example
        raise FileNotFoundError(
            f"Could not find {base_name}.yaml or {base_name}.example.yaml in {self.config_dir}"
        )

    def _read_yaml(self, path: Path) -> dict[str, Any]:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise ValueError(f"YAML content in {path} must be a dictionary.")
        return data

    def load_candidate_profile(
        self, custom_path: str | Path | None = None
    ) -> tuple[CandidateProfileConfig, Path]:
        path = Path(custom_path) if custom_path else self._resolve_file("candidate_profile")
        data = self._read_yaml(path)
        return CandidateProfileConfig.model_validate(data), path

    def load_job_search(
        self, custom_path: str | Path | None = None
    ) -> tuple[JobSearchConfig, Path]:
        path = Path(custom_path) if custom_path else self._resolve_file("job_search")
        data = self._read_yaml(path)
        return JobSearchConfig.model_validate(data), path

    def load_platforms(self, custom_path: str | Path | None = None) -> tuple[PlatformsConfig, Path]:
        path = Path(custom_path) if custom_path else self._resolve_file("platforms")
        data = self._read_yaml(path)
        return PlatformsConfig.model_validate(data), path

    def load_model_routing(
        self, custom_path: str | Path | None = None
    ) -> tuple[ModelRoutingConfig, Path]:
        path = Path(custom_path) if custom_path else self._resolve_file("model_routing")
        data = self._read_yaml(path)
        return ModelRoutingConfig.model_validate(data), path

    def load_policy_registry(
        self, custom_path: str | Path | None = None
    ) -> tuple[PolicyRegistryConfig, Path]:
        path = Path(custom_path) if custom_path else self._resolve_file("policy_registry")
        data = self._read_yaml(path)
        return PolicyRegistryConfig.model_validate(data), path

    def validate_all(self) -> ConfigValidationReport:
        report = ConfigValidationReport()

        # 1. Candidate profile
        try:
            profile, path = self.load_candidate_profile()
            report.loaded_files["candidate_profile"] = str(path)
            unresolved = profile.check_unresolved_facts()
            report.unresolved_facts = unresolved

            for category, items in unresolved.items():
                if items:
                    report.add_warning(
                        f"Candidate profile has unresolved facts in [{category}]: {', '.join(items)}. "
                        f"These facts must not be fabricated."
                    )
        except Exception as e:
            report.add_error(f"Candidate profile validation failed: {e}")

        # 2. Job search
        try:
            search, path = self.load_job_search()
            report.loaded_files["job_search"] = str(path)
            if search.global_config.compensation_basis == "confirm_base_vs_total_comp":
                report.add_warning(
                    "Job search compensation basis is set to 'confirm_base_vs_total_comp'. "
                    "Confirmation is required before enforcing as hard reject."
                )
        except Exception as e:
            report.add_error(f"Job search validation failed: {e}")

        # 3. Platforms
        try:
            platforms, path = self.load_platforms()
            report.loaded_files["platforms"] = str(path)
            # Verify 4-hour Gmail polling cadence
            if platforms.email.polling_minutes != 240:
                report.add_warning(
                    f"Email polling interval is {platforms.email.polling_minutes}m (standard default is 240m / 4h)."
                )
            if platforms.email.realtime_push_required:
                report.add_error(
                    "realtime_push_required is True. System requires periodic polling, not realtime push."
                )
        except Exception as e:
            report.add_error(f"Platforms validation failed: {e}")

        # 4. Model routing
        try:
            model_routing, path = self.load_model_routing()
            report.loaded_files["model_routing"] = str(path)
        except Exception as e:
            report.add_error(f"Model routing validation failed: {e}")

        # 5. Policy registry
        try:
            policy_reg, path = self.load_policy_registry()
            report.loaded_files["policy_registry"] = str(path)
            if policy_reg.default.decision != "blocked":
                report.add_error("Policy registry default must be 'blocked' (deny-by-default).")
        except Exception as e:
            report.add_error(f"Policy registry validation failed: {e}")

        return report
