"""
Medical code mapping and suggestion engine.
"""

import re
from typing import List, Dict, Set, Tuple
from models import CodeSuggestion, ClinicalFacts
from medical_data import (
    find_codes_for_term, get_cpt_description, get_icd10_description,
    EM_LEVEL_INDICATORS, CPT_CODES, ICD10_CODES
)


class MedicalCodeMapper:
    """Maps clinical facts to medical codes (CPT/HCPCS/ICD-10)."""
    
    def __init__(self):
        self.confidence_threshold = 0.5
    
    def generate_suggestions(self, facts: ClinicalFacts, encounter_data: Dict) -> List[CodeSuggestion]:
        """Generate code suggestions based on clinical facts."""
        suggestions = []
        
        # Generate ICD-10 suggestions (diagnoses)
        icd_suggestions = self._suggest_icd10_codes(facts)
        suggestions.extend(icd_suggestions)
        
        # Generate CPT suggestions (procedures)
        cpt_suggestions = self._suggest_cpt_codes(facts, encounter_data)
        suggestions.extend(cpt_suggestions)
        
        # Generate E/M code suggestions
        em_suggestions = self._suggest_em_codes(facts, encounter_data)
        suggestions.extend(em_suggestions)
        
        # Remove duplicates and sort by confidence
        unique_suggestions = self._deduplicate_suggestions(suggestions)
        unique_suggestions.sort(key=lambda x: x.confidence, reverse=True)
        
        return unique_suggestions
    
    def _suggest_icd10_codes(self, facts: ClinicalFacts) -> List[CodeSuggestion]:
        """Suggest ICD-10 diagnostic codes."""
        suggestions = []
        
        # Use existing indications
        for indication in facts.indications:
            if indication in ICD10_CODES:
                confidence = 0.9  # High confidence for direct matches
                suggestions.append(CodeSuggestion(
                    code=indication,
                    system="ICD10",
                    description=get_icd10_description(indication),
                    rationale=f"Direct diagnostic code from clinical documentation",
                    confidence=confidence
                ))
        
        # Map problems to ICD-10 codes
        for problem in facts.problems:
            codes = find_codes_for_term(problem)
            for code in codes:
                if code.startswith(('R', 'I', 'E', 'J', 'K', 'L', 'M', 'N', 'S', 'Z')):
                    confidence = self._calculate_icd_confidence(problem, code)
                    flags = []
                    if confidence < 0.7:
                        flags.append("Needs-Review")
                    
                    suggestions.append(CodeSuggestion(
                        code=code,
                        system="ICD10",
                        description=get_icd10_description(code),
                        rationale=f"Mapped from clinical problem: {problem}",
                        confidence=confidence,
                        flags=flags
                    ))
        
        return suggestions
    
    def _suggest_cpt_codes(self, facts: ClinicalFacts, encounter_data: Dict) -> List[CodeSuggestion]:
        """Suggest CPT/HCPCS procedure codes."""
        suggestions = []
        
        # Map procedures to CPT codes
        all_procedures = facts.procedures + facts.orders + facts.imaging_labs
        
        for procedure in all_procedures:
            codes = find_codes_for_term(procedure)
            for code in codes:
                if code.isdigit() and len(code) == 5:  # CPT code format
                    confidence = self._calculate_cpt_confidence(procedure, code)
                    flags = self._determine_cpt_flags(procedure, code, facts)
                    
                    suggestions.append(CodeSuggestion(
                        code=code,
                        system="CPT",
                        description=get_cpt_description(code),
                        rationale=f"Mapped from procedure: {procedure}",
                        confidence=confidence,
                        flags=flags
                    ))
        
        return suggestions
    
    def _suggest_em_codes(self, facts: ClinicalFacts, encounter_data: Dict) -> List[CodeSuggestion]:
        """Suggest E/M codes based on clinical complexity."""
        suggestions = []
        
        # Determine if this is a new or established patient
        provider_type = encounter_data.get("provider_type", "").lower()
        is_new_patient = "new" in provider_type
        
        # Assess complexity level
        complexity_level = self._assess_complexity_level(facts)
        
        # Get appropriate E/M code
        em_code = self._get_em_code(complexity_level, is_new_patient, encounter_data)
        
        if em_code:
            confidence = self._calculate_em_confidence(facts, complexity_level)
            flags = self._determine_em_flags(facts, encounter_data)
            modifiers = self._determine_em_modifiers(facts, encounter_data)
            
            suggestions.append(CodeSuggestion(
                code=em_code,
                system="CPT",
                description=get_cpt_description(em_code),
                modifiers=modifiers,
                rationale=f"E/M code for {complexity_level} complexity encounter",
                confidence=confidence,
                flags=flags
            ))
        
        return suggestions
    
    def _calculate_icd_confidence(self, problem: str, code: str) -> float:
        """Calculate confidence score for ICD-10 mapping."""
        base_confidence = 0.7
        
        # Boost confidence for exact matches
        description = get_icd10_description(code).lower()
        if problem.lower() in description or description in problem.lower():
            base_confidence += 0.2
        
        # Reduce confidence for generic codes
        if code.endswith('.9') or 'unspecified' in description:
            base_confidence -= 0.1
        
        return min(1.0, max(0.1, base_confidence))
    
    def _calculate_cpt_confidence(self, procedure: str, code: str) -> float:
        """Calculate confidence score for CPT mapping."""
        base_confidence = 0.8
        
        # Boost confidence for common procedures
        common_procedures = ['ecg', 'x-ray', 'blood draw', 'suture']
        if any(proc in procedure.lower() for proc in common_procedures):
            base_confidence += 0.1
        
        return min(1.0, max(0.1, base_confidence))
    
    def _calculate_em_confidence(self, facts: ClinicalFacts, complexity_level: str) -> float:
        """Calculate confidence score for E/M code."""
        base_confidence = 0.8
        
        # Boost confidence based on documentation completeness
        if facts.problems and facts.findings:
            base_confidence += 0.1
        
        if complexity_level == "high":
            base_confidence += 0.05
        
        return min(1.0, base_confidence)
    
    def _assess_complexity_level(self, facts: ClinicalFacts) -> str:
        """Assess the complexity level of the encounter."""
        complexity_score = 0
        
        # Score based on number of problems
        complexity_score += min(len(facts.problems), 3)
        
        # Score based on procedures
        complexity_score += min(len(facts.procedures), 2)
        
        # Score based on orders/tests
        complexity_score += min(len(facts.orders), 2)
        
        # Determine level
        if complexity_score >= 5:
            return "high"
        elif complexity_score >= 3:
            return "moderate"
        else:
            return "low"
    
    def _get_em_code(self, complexity_level: str, is_new_patient: bool, encounter_data: Dict) -> str:
        """Get appropriate E/M code."""
        pos_code = encounter_data.get("pos_code", "")
        
        # Emergency department
        if pos_code == "23":
            if complexity_level == "high":
                return "99284"
            elif complexity_level == "moderate":
                return "99283"
            else:
                return "99282"
        
        # Office/outpatient
        else:
            if is_new_patient:
                if complexity_level == "high":
                    return "99205"
                elif complexity_level == "moderate":
                    return "99204"
                else:
                    return "99203"
            else:
                if complexity_level == "high":
                    return "99215"
                elif complexity_level == "moderate":
                    return "99214"
                else:
                    return "99213"
    
    def _determine_cpt_flags(self, procedure: str, code: str, facts: ClinicalFacts) -> List[str]:
        """Determine flags for CPT codes."""
        flags = []
        
        # Check if indication is missing
        if not facts.indications:
            flags.append("Missing-Docs")
        
        # Check for complex procedures that need review
        complex_procedures = ['repair', 'excision', 'biopsy']
        if any(proc in procedure.lower() for proc in complex_procedures):
            flags.append("Needs-Review")
        
        return flags
    
    def _determine_em_flags(self, facts: ClinicalFacts, encounter_data: Dict) -> List[str]:
        """Determine flags for E/M codes."""
        flags = []
        
        # Check if documentation supports E/M level
        if len(facts.problems) == 0 and len(facts.findings) == 0:
            flags.append("Missing-Docs")
        
        return flags
    
    def _determine_em_modifiers(self, facts: ClinicalFacts, encounter_data: Dict) -> List[str]:
        """Determine modifiers for E/M codes."""
        modifiers = []
        
        # Check if significant separate E/M service (modifier 25)
        if len(facts.procedures) > 0 and len(facts.problems) > 1:
            modifiers.append("25")
        
        return modifiers
    
    def _deduplicate_suggestions(self, suggestions: List[CodeSuggestion]) -> List[CodeSuggestion]:
        """Remove duplicate code suggestions."""
        seen_codes = set()
        unique_suggestions = []
        
        for suggestion in suggestions:
            key = (suggestion.code, suggestion.system)
            if key not in seen_codes:
                seen_codes.add(key)
                unique_suggestions.append(suggestion)
        
        return unique_suggestions