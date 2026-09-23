from jobs_automation.intelligence.role_family import RoleFamilyClassifier

def test_role_family_classifier_known():
    classifier = RoleFamilyClassifier()
    assert classifier.classify("Senior iOS Developer") == "mobile_ios"
    assert classifier.classify("SAP consultant") == "sap_btp"
    assert classifier.classify("Product Manager") == "technical_product"
    assert classifier.classify("Applied AI Engineer") == "ai_software_engineer"

def test_role_family_classifier_unknown():
    classifier = RoleFamilyClassifier()
    assert classifier.classify("Barista") == "other"
    assert classifier.classify("") == "other"

def test_role_family_classifier_longest_match():
    # If title has "ios" and "product", which wins?
    # "product" is length 7, "ios" is length 3. Longest keyword match wins!
    classifier = RoleFamilyClassifier()
    assert classifier.classify("iOS Product Manager") == "technical_product"

def test_role_family_classifier_override():
    classifier = RoleFamilyClassifier(overrides={"barista": "coffee_master"})
    assert classifier.classify("Senior Barista") == "coffee_master"
