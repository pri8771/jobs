content = open("src/jobs_automation/core/job_search.py").read()

tailoring_code = """
from typing import Literal

class TailoringStrategyConfig(BaseModel):
    resume_strategy: Literal['highest_conversion', 'explore'] = 'highest_conversion'
"""

content = content.replace("class JobSearchConfig(BaseModel):", tailoring_code + "\nclass JobSearchConfig(BaseModel):")
content = content.replace("    strategy_guardrails: StrategyGuardrails = Field(default_factory=StrategyGuardrails)", "    strategy_guardrails: StrategyGuardrails = Field(default_factory=StrategyGuardrails)\n    tailoring: TailoringStrategyConfig = Field(default_factory=TailoringStrategyConfig)")

with open("src/jobs_automation/core/job_search.py", "w") as f:
    f.write(content)
