import re

content = open("src/jobs_automation/intelligence/strategy.py").read()

new_classes = """
class StrategyRecommendation(BaseModel):
    resume_variant_id: str | None
    resume_family: str
    rationale: str
    strategy_used: Literal['highest_conversion', 'explore', 'fallback']
    confidence: str
"""

content = content.replace("class ResumeStrategyRow(BaseModel):", new_classes + "\n\nclass ResumeStrategyRow(BaseModel):")

method = """
    def get_best_resume_variant(self, job_id: str | None, role_family: str, strategy: Literal['highest_conversion', 'explore'] = 'highest_conversion') -> StrategyRecommendation:
        resume_rows = self.resume_strategy()
        
        # Filter for the requested role_family
        family_rows = [r for r in resume_rows if r.resume_family == role_family]
        if not family_rows:
            return StrategyRecommendation(
                resume_variant_id=None,
                resume_family=role_family,
                rationale="No variants found for family.",
                strategy_used="fallback",
                confidence="LOW"
            )
            
        if strategy == 'highest_conversion':
            # Find robust variants
            robust_rows = [r for r in family_rows if r.interview.n >= self.guardrails.min_n_descriptive]
            if robust_rows:
                best = max(robust_rows, key=lambda x: x.interview.rate or 0.0)
                return StrategyRecommendation(
                    resume_variant_id=best.resume_variant_id,
                    resume_family=best.resume_family,
                    rationale=f"Highest interview rate ({best.interview.rate}) with N={best.interview.n}",
                    strategy_used="highest_conversion",
                    confidence="HIGH"
                )
            else:
                # Fallback to explore or just highest N
                best = max(family_rows, key=lambda x: x.interview.n)
                return StrategyRecommendation(
                    resume_variant_id=best.resume_variant_id,
                    resume_family=best.resume_family,
                    rationale=f"Low N fallback to variant with most usage (N={best.interview.n})",
                    strategy_used="fallback",
                    confidence="LOW"
                )
        else:
            # Explore: just pick one with lowest N
            best = min(family_rows, key=lambda x: x.interview.n)
            return StrategyRecommendation(
                resume_variant_id=best.resume_variant_id,
                resume_family=best.resume_family,
                rationale=f"Exploration: lowest N ({best.interview.n})",
                strategy_used="explore",
                confidence="LOW"
            )
"""

content = content.replace("    def source_strategy(self, window_days: int | None = None) -> list[Any]:", method + "\n    def source_strategy(self, window_days: int | None = None) -> list[Any]:")

with open("src/jobs_automation/intelligence/strategy.py", "w") as f:
    f.write(content)
