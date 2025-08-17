"""
Medical coding reference data and lookup tables.
"""

from typing import Dict, List, Set, Tuple


# Common CPT codes with descriptions and MUE limits
CPT_CODES = {
    # E/M Codes
    "99213": {"desc": "Office/outpatient E/M, established patient", "mue": 1},
    "99214": {"desc": "Office/outpatient E/M, established patient", "mue": 1},
    "99203": {"desc": "Office/outpatient E/M, new patient", "mue": 1},
    "99204": {"desc": "Office/outpatient E/M, new patient", "mue": 1},
    "99282": {"desc": "Emergency department visit", "mue": 1},
    "99283": {"desc": "Emergency department visit", "mue": 1},
    
    # Diagnostic Tests
    "93000": {"desc": "ECG, routine 12-lead with interp and report", "mue": 1},
    "71020": {"desc": "Chest X-ray", "mue": 4},
    "80053": {"desc": "Comprehensive metabolic panel", "mue": 1},
    "85025": {"desc": "Complete blood count with differential", "mue": 1},
    "36415": {"desc": "Venipuncture", "mue": 3},
    
    # Procedures
    "12001": {"desc": "Simple repair superficial wound", "mue": 35},
    "17110": {"desc": "Destruction benign lesion", "mue": 14},
    "99213": {"desc": "Office visit established patient", "mue": 1},
    "90471": {"desc": "Immunization administration", "mue": 6},
    "90715": {"desc": "Tetanus, diphtheria toxoids vaccine", "mue": 1},
}


# Common ICD-10 codes
ICD10_CODES = {
    "R00.2": "Palpitations",
    "R06.02": "Shortness of breath",
    "R50.9": "Fever unspecified",
    "Z23": "Encounter for immunization",
    "I10": "Essential hypertension",
    "E11.9": "Type 2 diabetes mellitus without complications",
    "J02.9": "Acute pharyngitis, unspecified",
    "S61.401A": "Unspecified open wound of right hand, initial encounter",
    "L03.90": "Cellulitis, unspecified",
    "K59.00": "Constipation, unspecified",
    "R51.9": "Headache, unspecified",
    "M25.50": "Pain in unspecified joint",
    "N39.0": "Urinary tract infection, site not specified",
    "R10.9": "Unspecified abdominal pain",
    "J00": "Acute nasopharyngitis [common cold]",
}


# NCCI PTP pairs (primary, secondary) -> bundling rules
NCCI_PTP_RULES = {
    ("99213", "93000"): {"bundled": False, "modifier_allowed": True, "modifiers": ["25"]},
    ("99213", "36415"): {"bundled": False, "modifier_allowed": True, "modifiers": ["25"]},
    ("99214", "12001"): {"bundled": False, "modifier_allowed": True, "modifiers": ["25"]},
    ("12001", "17110"): {"bundled": True, "modifier_allowed": True, "modifiers": ["59", "XS"]},
    ("93000", "71020"): {"bundled": False, "modifier_allowed": False, "modifiers": []},
}


# Common clinical terms to CPT/ICD mappings
CLINICAL_TERM_MAPPINGS = {
    # Symptoms to ICD-10
    "palpitation": ["R00.2"],
    "palpitations": ["R00.2"],
    "chest pain": ["R07.89"],
    "shortness of breath": ["R06.02"],
    "dyspnea": ["R06.02"],
    "fever": ["R50.9"],
    "headache": ["R51.9"],
    "nausea": ["R11.10"],
    "vomiting": ["R11.10"],
    "abdominal pain": ["R10.9"],
    "joint pain": ["M25.50"],
    "wound": ["S61.401A"],
    "laceration": ["S61.401A"],
    "uti": ["N39.0"],
    "urinary tract infection": ["N39.0"],
    
    # Procedures to CPT
    "ecg": ["93000"],
    "ekg": ["93000"],
    "electrocardiogram": ["93000"],
    "chest x-ray": ["71020"],
    "chest xray": ["71020"],
    "cxr": ["71020"],
    "blood draw": ["36415"],
    "venipuncture": ["36415"],
    "suture": ["12001"],
    "repair": ["12001"],
    "immunization": ["90471"],
    "vaccination": ["90471"],
    "vaccine": ["90471"],
    "cbc": ["85025"],
    "complete blood count": ["85025"],
    "metabolic panel": ["80053"],
    "comprehensive metabolic": ["80053"],
}


# E/M level determination keywords
EM_LEVEL_INDICATORS = {
    "straightforward": {"level": "low", "codes": ["99213", "99203"]},
    "low complexity": {"level": "low", "codes": ["99213", "99203"]},
    "moderate complexity": {"level": "moderate", "codes": ["99214", "99204"]},
    "high complexity": {"level": "high", "codes": ["99215", "99205"]},
    "detailed": {"level": "moderate", "codes": ["99214", "99204"]},
    "comprehensive": {"level": "high", "codes": ["99215", "99205"]},
}


# Common modifier explanations
MODIFIER_EXPLANATIONS = {
    "25": "Significant, separately identifiable E/M service",
    "59": "Distinct procedural service",
    "XS": "Separate structure",
    "XU": "Unusual non-overlapping service",
    "50": "Bilateral procedure",
    "RT": "Right side",
    "LT": "Left side",
    "76": "Repeat procedure by same physician",
    "77": "Repeat procedure by another physician",
    "GT": "Synchronous telemedicine service",
    "95": "Synchronous telemedicine service",
}


# Payer-specific rules
PAYER_RULES = {
    "Medicare": {
        "bilateral_preference": "50",  # Prefer modifier 50 over RT/LT
        "telehealth_modifiers": ["95", "GT"],
        "frequency_limits": {"93000": {"per_year": 12}},
    },
    "GenericPPO": {
        "bilateral_preference": "RT_LT",  # Prefer RT/LT over 50
        "telehealth_modifiers": ["95"],
        "frequency_limits": {},
    },
    "Medicaid": {
        "bilateral_preference": "RT_LT",
        "telehealth_modifiers": ["GT"],
        "frequency_limits": {"17110": {"per_visit": 3}},
    }
}


# LCD/NCD policies (simplified)
LCD_NCD_POLICIES = {
    "ECG_ROUTINE": {
        "policy_id": "L33832",
        "codes": ["93000"],
        "covered_icd10": ["R00.2", "I10", "R06.02", "R07.89"],
        "frequency": {"per_year": 12},
        "documentation_required": ["indication", "interpretation"],
    },
    "CHEST_XRAY": {
        "policy_id": "L34542",
        "codes": ["71020"],
        "covered_icd10": ["R06.02", "R05", "J44.1", "Z87.891"],
        "frequency": {"per_episode": 1},
        "documentation_required": ["indication", "findings"],
    },
}


def get_cpt_description(code: str) -> str:
    """Get CPT code description."""
    return CPT_CODES.get(code, {}).get("desc", f"Unknown CPT code {code}")


def get_mue_limit(code: str) -> int:
    """Get MUE limit for a CPT code."""
    return CPT_CODES.get(code, {}).get("mue", 1)


def get_icd10_description(code: str) -> str:
    """Get ICD-10 code description."""
    return ICD10_CODES.get(code, f"Unknown ICD-10 code {code}")


def find_codes_for_term(term: str) -> List[str]:
    """Find CPT/ICD codes related to a clinical term."""
    term_lower = term.lower()
    codes = []
    
    # Direct lookup
    if term_lower in CLINICAL_TERM_MAPPINGS:
        codes.extend(CLINICAL_TERM_MAPPINGS[term_lower])
    
    # Partial matching
    for mapping_term, mapping_codes in CLINICAL_TERM_MAPPINGS.items():
        if term_lower in mapping_term or mapping_term in term_lower:
            codes.extend(mapping_codes)
    
    return list(set(codes))  # Remove duplicates


def get_ncci_rule(primary: str, secondary: str) -> Dict:
    """Get NCCI PTP rule for code pair."""
    rule_key = (primary, secondary)
    reverse_key = (secondary, primary)
    
    if rule_key in NCCI_PTP_RULES:
        return NCCI_PTP_RULES[rule_key]
    elif reverse_key in NCCI_PTP_RULES:
        # Return reverse rule with swapped primary/secondary
        rule = NCCI_PTP_RULES[reverse_key].copy()
        return rule
    
    # Default: assume allowed if not in bundling table
    return {"bundled": False, "modifier_allowed": False, "modifiers": []}


def get_payer_rules(payer: str) -> Dict:
    """Get payer-specific rules."""
    # Try exact match first
    if payer in PAYER_RULES:
        return PAYER_RULES[payer]
    
    # Try partial matching
    payer_lower = payer.lower()
    for payer_name, rules in PAYER_RULES.items():
        if payer_name.lower() in payer_lower or payer_lower in payer_name.lower():
            return rules
    
    # Default rules for unknown payers
    return {
        "bilateral_preference": "RT_LT",
        "telehealth_modifiers": ["95"],
        "frequency_limits": {},
    }


def find_lcd_ncd_policy(codes: List[str]) -> Dict:
    """Find relevant LCD/NCD policy for given codes."""
    for policy_name, policy_data in LCD_NCD_POLICIES.items():
        if any(code in policy_data["codes"] for code in codes):
            return policy_data
    
    return {
        "policy_id": "unknown",
        "codes": [],
        "covered_icd10": [],
        "frequency": {},
        "documentation_required": [],
    }