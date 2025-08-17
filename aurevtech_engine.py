"""
Main Aurevtech AI Coder engine for medical coding.
"""

from datetime import datetime, timezone
from typing import Dict, List
from models import (
    InputRequest, OutputResponse, ClinicalFacts, 
    ExplanationData, AuditTraceStep, ProcessingError
)
from fact_extractor import ClinicalFactExtractor
from code_mapper import MedicalCodeMapper
from compliance_checker import ComplianceChecker


class AurevtechEngine:
    """Main engine for the Aurevtech AI Coder medical coding system."""
    
    def __init__(self):
        self.fact_extractor = ClinicalFactExtractor()
        self.code_mapper = MedicalCodeMapper()
        self.compliance_checker = ComplianceChecker()
        self.version = "AAC-0.2"
    
    def process_request(self, request: InputRequest) -> OutputResponse:
        """Process a medical coding request and return structured response."""
        
        # Initialize response
        response = OutputResponse(
            version=self.version,
            generated_at=datetime.now(timezone.utc).isoformat(),
            patient=request.patient,
            encounter=request.encounter,
            facts=ClinicalFacts(),
            suggestions=[],
            edits=self.compliance_checker.check_compliance([], {})[0],
            readiness=self.compliance_checker.check_compliance([], {})[1],
            explanation=ExplanationData(),
            errors=[]
        )
        
        try:
            # Step 1: Extract clinical facts
            response.explanation.audit_trace.append(
                AuditTraceStep(step="extract", detail="Extracting clinical facts from note")
            )
            
            response.facts = self.fact_extractor.extract_facts(
                request.clinical_note, 
                request.structured.model_dump() if request.structured else {}
            )
            
            response.explanation.audit_trace.append(
                AuditTraceStep(
                    step="extract", 
                    detail=f"Extracted {len(response.facts.problems)} problems, "
                           f"{len(response.facts.procedures)} procedures"
                )
            )
            
            # Step 2: Generate code suggestions
            response.explanation.audit_trace.append(
                AuditTraceStep(step="map", detail="Mapping clinical facts to medical codes")
            )
            
            encounter_data = {
                "pos_code": request.encounter.pos_code,
                "payer": request.encounter.payer,
                "provider_type": request.encounter.provider_type,
                "date": request.encounter.date
            }
            
            response.suggestions = self.code_mapper.generate_suggestions(
                response.facts, 
                encounter_data
            )
            
            response.explanation.audit_trace.append(
                AuditTraceStep(
                    step="map", 
                    detail=f"Generated {len(response.suggestions)} code suggestions"
                )
            )
            
            # Step 3: Check compliance
            response.explanation.audit_trace.append(
                AuditTraceStep(step="ncci", detail="Checking NCCI PTP edits")
            )
            
            response.edits, response.readiness = self.compliance_checker.check_compliance(
                response.suggestions, 
                encounter_data
            )
            
            response.explanation.audit_trace.append(
                AuditTraceStep(
                    step="score", 
                    detail=f"Calculated readiness score: {response.readiness.score:.2f}"
                )
            )
            
            # Step 4: Add explanation notes if in explain mode
            if request.mode == "explain":
                response.explanation.notes = self._generate_explanation_notes(response)
            
        except Exception as e:
            # Handle processing errors
            error = ProcessingError(
                code="INSUFFICIENT_EVIDENCE",
                message=f"Error processing request: {str(e)}"
            )
            response.errors.append(error)
            
            # Provide basic response even on error
            response.readiness.score = 0.0
            response.readiness.submit_ready = False
            response.readiness.issues = ["Processing error occurred"]
            response.readiness.actions = ["Review input data and try again"]
        
        return response
    
    def _generate_explanation_notes(self, response: OutputResponse) -> List[str]:
        """Generate human-readable explanation notes."""
        notes = []
        
        # Summary note
        notes.append(
            f"Analyzed clinical note and generated {len(response.suggestions)} code suggestions "
            f"with {response.readiness.score:.0%} claim readiness"
        )
        
        # Code suggestions summary
        if response.suggestions:
            cpt_count = len([s for s in response.suggestions if s.system in ["CPT", "HCPCS"]])
            icd_count = len([s for s in response.suggestions if s.system == "ICD10"])
            notes.append(f"Suggested {cpt_count} CPT/HCPCS codes and {icd_count} ICD-10 codes")
        
        # Compliance issues
        if response.readiness.issues:
            notes.append(f"Identified {len(response.readiness.issues)} compliance issues requiring attention")
        
        # High-confidence codes
        high_conf_codes = [s for s in response.suggestions if s.confidence >= 0.8]
        if high_conf_codes:
            notes.append(f"{len(high_conf_codes)} codes have high confidence (≥80%)")
        
        # Flagged codes
        flagged_codes = [s for s in response.suggestions if s.flags]
        if flagged_codes:
            notes.append(f"{len(flagged_codes)} codes require additional review or documentation")
        
        return notes
    
    def validate_input(self, request_data: Dict) -> List[ProcessingError]:
        """Validate input request data."""
        errors = []
        
        # Check required fields
        required_fields = ["patient", "encounter", "clinical_note"]
        for field in required_fields:
            if field not in request_data:
                errors.append(ProcessingError(
                    code="INPUT_VALIDATION",
                    message=f"Missing required field: {field}"
                ))
        
        # Check patient data
        if "patient" in request_data:
            patient = request_data["patient"]
            if "age" not in patient or not isinstance(patient["age"], int):
                errors.append(ProcessingError(
                    code="INPUT_VALIDATION",
                    message="Patient age must be an integer"
                ))
            
            if "sex" not in patient or patient["sex"] not in ["F", "M", "U"]:
                errors.append(ProcessingError(
                    code="INPUT_VALIDATION",
                    message="Patient sex must be F, M, or U"
                ))
        
        # Check encounter data
        if "encounter" in request_data:
            encounter = request_data["encounter"]
            required_encounter_fields = ["date", "pos_code", "payer", "provider_type"]
            for field in required_encounter_fields:
                if field not in encounter:
                    errors.append(ProcessingError(
                        code="INPUT_VALIDATION",
                        message=f"Missing encounter field: {field}"
                    ))
        
        # Check clinical note
        if "clinical_note" in request_data:
            if not request_data["clinical_note"] or len(request_data["clinical_note"].strip()) < 10:
                errors.append(ProcessingError(
                    code="INPUT_VALIDATION",
                    message="Clinical note must contain at least 10 characters"
                ))
        
        return errors
    
    def get_system_info(self) -> Dict:
        """Get system information and status."""
        return {
            "version": self.version,
            "status": "operational",
            "capabilities": [
                "clinical_fact_extraction",
                "cpt_hcpcs_coding", 
                "icd10_coding",
                "ncci_ptp_checking",
                "mue_validation",
                "lcd_ncd_checking",
                "payer_rule_validation",
                "claim_readiness_scoring"
            ],
            "supported_modes": ["analyze", "explain"]
        }