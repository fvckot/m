"""
Clinical fact extraction from unstructured notes.
"""

import re
import nltk
from typing import List, Dict, Set
from models import ClinicalFacts
from medical_data import find_codes_for_term, get_icd10_description


class ClinicalFactExtractor:
    """Extracts clinical facts from unstructured clinical notes."""
    
    def __init__(self):
        # Download required NLTK data
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
            nltk.download('stopwords', quiet=True)
        except:
            pass  # Continue if download fails
    
    def extract_facts(self, clinical_note: str, structured_data: Dict = None) -> ClinicalFacts:
        """Extract clinical facts from note and structured data."""
        facts = ClinicalFacts()
        
        # Clean and normalize the note
        note = self._clean_note(clinical_note)
        
        # Extract problems (symptoms, diagnoses)
        facts.problems = self._extract_problems(note)
        
        # Extract findings (physical exam findings, observations)
        facts.findings = self._extract_findings(note)
        
        # Extract orders (lab orders, imaging orders)
        facts.orders = self._extract_orders(note)
        
        # Extract procedures (performed procedures)
        facts.procedures = self._extract_procedures(note)
        
        # Extract imaging/labs (completed tests)
        facts.imaging_labs = self._extract_imaging_labs(note)
        
        # Extract indications (diagnostic codes)
        facts.indications = self._extract_indications(facts.problems)
        
        # Merge with structured data if provided
        if structured_data:
            self._merge_structured_data(facts, structured_data)
        
        return facts
    
    def _clean_note(self, note: str) -> str:
        """Clean and normalize clinical note."""
        # Remove extra whitespace
        note = re.sub(r'\s+', ' ', note.strip())
        
        # Normalize common abbreviations
        abbreviations = {
            r'\bpt\b': 'patient',
            r'\bc/o\b': 'complains of',
            r'\bs/p\b': 'status post',
            r'\bw/\b': 'with',
            r'\bw/o\b': 'without',
            r'\bhx\b': 'history',
            r'\bfhx\b': 'family history',
            r'\bpmh\b': 'past medical history',
            r'\brx\b': 'prescription',
            r'\bdx\b': 'diagnosis',
            r'\btx\b': 'treatment',
        }
        
        for abbrev, expansion in abbreviations.items():
            note = re.sub(abbrev, expansion, note, flags=re.IGNORECASE)
        
        return note
    
    def _extract_problems(self, note: str) -> List[str]:
        """Extract clinical problems and symptoms."""
        problems = set()
        
        # Common problem patterns
        problem_patterns = [
            r'chief complaint[:\s]+([^\.]+)',
            r'complains? of[:\s]+([^\.]+)',
            r'presents with[:\s]+([^\.]+)',
            r'symptoms? include[:\s]+([^\.]+)',
            r'patient (?:has|reports|endorses)[:\s]+([^\.]+)',
            r'history of[:\s]+([^\.]+)',
        ]
        
        for pattern in problem_patterns:
            matches = re.finditer(pattern, note, re.IGNORECASE)
            for match in matches:
                problem = match.group(1).strip().lower()
                problems.add(self._clean_clinical_term(problem))
        
        # Look for specific symptom keywords
        symptom_keywords = [
            'pain', 'ache', 'discomfort', 'soreness',
            'fever', 'chills', 'nausea', 'vomiting',
            'headache', 'dizziness', 'fatigue',
            'shortness of breath', 'dyspnea', 'sob',
            'palpitations', 'chest pain',
            'cough', 'congestion', 'runny nose',
            'abdominal pain', 'stomach pain',
            'joint pain', 'muscle pain',
            'rash', 'swelling', 'inflammation',
        ]
        
        for keyword in symptom_keywords:
            if re.search(rf'\b{keyword}\b', note, re.IGNORECASE):
                problems.add(keyword)
        
        return list(problems)
    
    def _extract_findings(self, note: str) -> List[str]:
        """Extract physical exam findings and observations."""
        findings = set()
        
        # Physical exam patterns
        exam_patterns = [
            r'(?:physical exam|examination)[:\s]*([^\.]+)',
            r'(?:vital signs?|vs)[:\s]*([^\.]+)',
            r'(?:normal|abnormal|unremarkable)[:\s]+([^\.]+)',
            r'(?:auscultation|palpation|inspection)[:\s]*([^\.]+)',
            r'(?:heart rate|blood pressure|temperature|bp|hr|temp)[:\s]*([^\.]+)',
        ]
        
        for pattern in exam_patterns:
            matches = re.finditer(pattern, note, re.IGNORECASE)
            for match in matches:
                finding = match.group(1).strip().lower()
                findings.add(self._clean_clinical_term(finding))
        
        # Look for vital signs
        vital_patterns = [
            r'bp[:\s]*(\d+/\d+)',
            r'blood pressure[:\s]*(\d+/\d+)',
            r'heart rate[:\s]*(\d+)',
            r'hr[:\s]*(\d+)',
            r'temperature[:\s]*(\d+\.?\d*)',
            r'temp[:\s]*(\d+\.?\d*)',
        ]
        
        for pattern in vital_patterns:
            matches = re.finditer(pattern, note, re.IGNORECASE)
            for match in matches:
                findings.add(f"vital sign: {match.group(0).lower()}")
        
        return list(findings)
    
    def _extract_orders(self, note: str) -> List[str]:
        """Extract orders for tests, procedures, medications."""
        orders = set()
        
        # Order patterns
        order_patterns = [
            r'order(?:ed)?[:\s]+([^\.]+)',
            r'plan[:\s]+([^\.]+)',
            r'(?:will|to) obtain[:\s]+([^\.]+)',
            r'(?:will|to) perform[:\s]+([^\.]+)',
            r'recommended[:\s]+([^\.]+)',
            r'prescribed[:\s]+([^\.]+)',
        ]
        
        for pattern in order_patterns:
            matches = re.finditer(pattern, note, re.IGNORECASE)
            for match in matches:
                order = match.group(1).strip().lower()
                orders.add(self._clean_clinical_term(order))
        
        # Look for common test orders
        test_keywords = [
            'ecg', 'ekg', 'electrocardiogram',
            'chest x-ray', 'chest xray', 'cxr',
            'blood work', 'labs', 'laboratory',
            'cbc', 'complete blood count',
            'metabolic panel', 'basic metabolic',
            'urinalysis', 'urine test',
        ]
        
        for keyword in test_keywords:
            if re.search(rf'\b{keyword}\b', note, re.IGNORECASE):
                orders.add(keyword)
        
        return list(orders)
    
    def _extract_procedures(self, note: str) -> List[str]:
        """Extract performed procedures."""
        procedures = set()
        
        # Procedure patterns
        procedure_patterns = [
            r'performed[:\s]+([^\.]+)',
            r'procedure[:\s]*[:]?[:\s]*([^\.]+)',
            r'(?:did|completed)[:\s]+([^\.]+)',
            r'administered[:\s]+([^\.]+)',
            r'given[:\s]+([^\.]+)',
        ]
        
        for pattern in procedure_patterns:
            matches = re.finditer(pattern, note, re.IGNORECASE)
            for match in matches:
                procedure = match.group(1).strip().lower()
                procedures.add(self._clean_clinical_term(procedure))
        
        # Look for specific procedures
        procedure_keywords = [
            'injection', 'immunization', 'vaccination',
            'suture', 'repair', 'wound care',
            'blood draw', 'venipuncture',
            'ecg obtained', 'ekg performed',
        ]
        
        for keyword in procedure_keywords:
            if re.search(rf'\b{keyword}\b', note, re.IGNORECASE):
                procedures.add(keyword)
        
        return list(procedures)
    
    def _extract_imaging_labs(self, note: str) -> List[str]:
        """Extract completed imaging and lab results."""
        imaging_labs = set()
        
        # Results patterns
        results_patterns = [
            r'results?[:\s]+([^\.]+)',
            r'findings?[:\s]+([^\.]+)',
            r'shows?[:\s]+([^\.]+)',
            r'reveals?[:\s]+([^\.]+)',
            r'impression[:\s]+([^\.]+)',
        ]
        
        for pattern in results_patterns:
            matches = re.finditer(pattern, note, re.IGNORECASE)
            for match in matches:
                result = match.group(1).strip().lower()
                imaging_labs.add(self._clean_clinical_term(result))
        
        return list(imaging_labs)
    
    def _extract_indications(self, problems: List[str]) -> List[str]:
        """Convert problems to ICD-10 diagnostic codes."""
        indications = set()
        
        for problem in problems:
            # Find matching ICD-10 codes
            codes = find_codes_for_term(problem)
            for code in codes:
                if code.startswith(('R', 'I', 'E', 'J', 'K', 'L', 'M', 'N', 'S', 'Z')):  # ICD-10 prefixes
                    description = get_icd10_description(code)
                    indications.add(f"{code}")
        
        return list(indications)
    
    def _clean_clinical_term(self, term: str) -> str:
        """Clean and normalize clinical terms."""
        # Remove punctuation and extra spaces
        term = re.sub(r'[^\w\s\-/]', ' ', term)
        term = re.sub(r'\s+', ' ', term).strip()
        
        # Remove common stop words
        stop_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        words = term.split()
        filtered_words = [word for word in words if word.lower() not in stop_words]
        
        return ' '.join(filtered_words) if filtered_words else term
    
    def _merge_structured_data(self, facts: ClinicalFacts, structured_data: Dict):
        """Merge structured data into facts."""
        if 'diagnoses' in structured_data:
            facts.indications.extend(structured_data['diagnoses'])
        
        if 'orders' in structured_data:
            facts.orders.extend(structured_data['orders'])
        
        if 'procedures' in structured_data:
            facts.procedures.extend(structured_data['procedures'])
        
        # Remove duplicates
        facts.indications = list(set(facts.indications))
        facts.orders = list(set(facts.orders))
        facts.procedures = list(set(facts.procedures))