content = open("src/jobs_automation/intelligence/strategy.py").read()

import re

# Remove StrategyGuardrails from strategy.py
content = re.sub(r"class StrategyGuardrails\(BaseModel\):.*?return self", "", content, flags=re.DOTALL)

with open("src/jobs_automation/intelligence/strategy.py", "w") as f:
    f.write(content)

# Add it to core/job_search.py
js_content = open("src/jobs_automation/core/job_search.py").read()
js_content = js_content.replace("from jobs_automation.intelligence.strategy import StrategyGuardrails\n", "")
js_content = js_content.replace("from typing import Literal", "from pydantic import model_validator\nfrom typing import Literal\n\nclass StrategyGuardrails(BaseModel):\n    min_n_descriptive: int = 5\n    min_n_comparison: int = 10\n    min_n_per_arm: int = 5\n    default_window_days: int = 90\n    stale_after_days: int = 180\n    \n    @model_validator(mode='after')\n    def validate_positive(self) -> 'StrategyGuardrails':\n        if self.min_n_descriptive < 0 or self.min_n_comparison < 0 or self.min_n_per_arm < 0 or self.default_window_days < 0 or self.stale_after_days < 0:\n            raise ValueError(\"Guardrail values cannot be negative\")\n        return self\n")
with open("src/jobs_automation/core/job_search.py", "w") as f:
    f.write(js_content)
