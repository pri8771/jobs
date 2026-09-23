import re
from jobs_automation.preparation.tailoring import ROLE_FAMILY_KEYWORDS

class RoleFamilyClassifier:
    def __init__(self, overrides: dict[str, str] | None = None):
        self.overrides = overrides or {}

    def classify(self, title: str) -> str:
        if not title:
            return "other"
            
        # 1. Strip punctuation and lowercase
        clean_title = re.sub(r'[^\w\s]', ' ', title.lower()).strip()
        
        # 2. Check overrides first
        for override_key, family in self.overrides.items():
            if override_key.lower() in clean_title:
                return family
                
        # 3. Check keyword tables
        best_match = "other"
        longest_match_len = -1
        
        for family, keywords in ROLE_FAMILY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in clean_title:
                    # Longest match wins
                    if len(keyword) > longest_match_len:
                        best_match = family
                        longest_match_len = len(keyword)
                        
        return best_match

    def families(self) -> list[str]:
        base_families = list(ROLE_FAMILY_KEYWORDS.keys()) + ["other"]
        return list(set(base_families + list(self.overrides.values())))
