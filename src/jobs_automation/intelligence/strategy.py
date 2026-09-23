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
