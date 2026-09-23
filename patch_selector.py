content = open("src/jobs_automation/preparation/tailoring.py").read()

import re

new_method = """
    @staticmethod
    def select_variant(
        job: JobModel, 
        matched_role_family: str | None = None,
        session: Any = None,
        config: Any = None
    ) -> str:
        title_lower = (job.normalized_title or "").lower()
        fam_lower = (matched_role_family or "").lower()
        
        # New V2.3 Dynamic selection logic
        if session and config:
            from jobs_automation.intelligence.role_family import RoleFamilyClassifier
            from jobs_automation.intelligence.strategy import StrategyLearningService
            from jobs_automation.db.models import ResumeVariantModel
            
            classifier = RoleFamilyClassifier()
            expected_family = matched_role_family or classifier.classify(job.normalized_title)
            
            # OpportunityGraph is assumed to be handled previously or we can call it here if needed,
            # but getting the best variant directly:
            strategy_val = config.tailoring.resume_strategy if getattr(config, 'tailoring', None) else 'highest_conversion'
            svc = StrategyLearningService(session, config.strategy_guardrails)
            rec = svc.get_best_resume_variant(str(job.id), expected_family, strategy=strategy_val)
            
            if rec.resume_variant_id:
                # Find the variant name from DB
                v_model = session.get(ResumeVariantModel, rec.resume_variant_id)
                if v_model:
                    return v_model.name

        # Fallback to static logic
        if any(k in title_lower or k in fam_lower for k in ROLE_FAMILY_KEYWORDS["sap_btp"]):
            return "resume_sap_btp"
        elif any(k in title_lower for k in ROLE_FAMILY_KEYWORDS["mobile_ios"]):
            return "resume_mobile_ios"
        elif any(k in title_lower for k in ROLE_FAMILY_KEYWORDS["technical_product"]):
            return "resume_technical_product"
        elif any(k in title_lower for k in ROLE_FAMILY_KEYWORDS["ai_software_engineer"]):
            return "resume_ai_software_engineer"
        else:
            return "resume_enterprise_automation"
"""

content = re.sub(r"    @staticmethod\s+def select_variant\(job: JobModel, matched_role_family: str \| None = None\) -> str:.*?(?=\s+@classmethod)", new_method, content, flags=re.DOTALL)

with open("src/jobs_automation/preparation/tailoring.py", "w") as f:
    f.write(content)
