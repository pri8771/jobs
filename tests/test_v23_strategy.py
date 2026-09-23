import pytest
from pydantic import ValidationError
from jobs_automation.intelligence.strategy import StrategyGuardrails
from jobs_automation.core.job_search import JobSearchConfig
import yaml

def test_strategy_guardrails_defaults():
    g = StrategyGuardrails()
    assert g.min_n_descriptive == 5
    assert g.min_n_comparison == 10
    assert g.min_n_per_arm == 5
    assert g.default_window_days == 90
    assert g.stale_after_days == 180

def test_strategy_guardrails_negative_rejected():
    with pytest.raises(ValueError, match="cannot be negative"):
        StrategyGuardrails(min_n_descriptive=-1)

def test_job_search_config_with_strategy_guardrails():
    yaml_doc = """
version: 1
global:
  enabled: true
  freshness_days: 7
strategy_guardrails:
  min_n_descriptive: 20
    """
    data = yaml.safe_load(yaml_doc)
    config = JobSearchConfig(**data)
    assert config.strategy_guardrails.min_n_descriptive == 20
    assert config.strategy_guardrails.min_n_comparison == 10 # default

def test_job_search_config_without_strategy_guardrails():
    yaml_doc = """
version: 1
global:
  enabled: true
  freshness_days: 7
    """
    data = yaml.safe_load(yaml_doc)
    config = JobSearchConfig(**data)
    assert config.strategy_guardrails.min_n_descriptive == 5

