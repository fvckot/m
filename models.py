"""
Data models for the Aurevtech AI Coder medical coding engine.
"""

from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class Patient(BaseModel):
    age: int
    sex: Literal["F", "M", "U"]


class Encounter(BaseModel):
    date: str = Field(pattern=r'\d{4}-\d{2}-\d{2}')
    pos_code: str
    payer: str
    provider_type: str


class Vitals(BaseModel):
    bp: str = ""
    hr: str = ""
    temp: str = ""


class MedAdministered(BaseModel):
    drug: str
    dose: str
    route: str
    time: str  # ISO format


class StructuredData(BaseModel):
    diagnoses: List[str] = Field(default_factory=list)
    orders: List[str] = Field(default_factory=list)
    procedures: List[str] = Field(default_factory=list)
    vitals: Vitals = Field(default_factory=Vitals)
    meds_administered: List[MedAdministered] = Field(default_factory=list)


class InputRequest(BaseModel):
    mode: Literal["analyze", "explain"] = "analyze"
    patient: Patient
    encounter: Encounter
    clinical_note: str
    structured: StructuredData = Field(default_factory=StructuredData)


class ClinicalFacts(BaseModel):
    problems: List[str] = Field(default_factory=list)
    findings: List[str] = Field(default_factory=list)
    orders: List[str] = Field(default_factory=list)
    procedures: List[str] = Field(default_factory=list)
    imaging_labs: List[str] = Field(default_factory=list)
    indications: List[str] = Field(default_factory=list)


class CodeSuggestion(BaseModel):
    code: str
    system: Literal["CPT", "HCPCS", "ICD10"]
    description: str
    modifiers: List[str] = Field(default_factory=list)
    units: int = 1
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)
    flags: List[Literal["Needs-Review", "Missing-Docs", "Check-Payer-Policy"]] = Field(default_factory=list)


class NCCIEdit(BaseModel):
    primary: str
    secondary: str
    status: Literal["bundled", "allowed"]
    modifier_allowed: bool
    modifier_candidates: List[str] = Field(default_factory=list)
    note: str = ""


class MUEEdit(BaseModel):
    code: str
    proposed_units: int
    mue_limit: int
    status: Literal["ok", "exceeds"]
    note: str = ""


class LCDNCDEdit(BaseModel):
    policy_id: str
    meets_criteria: bool
    covered_icd10: List[str] = Field(default_factory=list)
    missing_icd10: List[str] = Field(default_factory=list)
    frequency_ok: bool
    note: str = ""


class PayerRuleEdit(BaseModel):
    rule_id: str
    status: Literal["pass", "fail", "unknown"]
    note: str = ""


class ComplianceEdits(BaseModel):
    ncci_ptp: List[NCCIEdit] = Field(default_factory=list)
    mue: List[MUEEdit] = Field(default_factory=list)
    lcd_ncd: List[LCDNCDEdit] = Field(default_factory=list)
    payer_rules: List[PayerRuleEdit] = Field(default_factory=list)


class ClaimReadiness(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    issues: List[str] = Field(default_factory=list)
    actions: List[str] = Field(default_factory=list)
    submit_ready: bool


class AuditTraceStep(BaseModel):
    step: Literal["extract", "map", "ncci", "mue", "lcd", "payer", "score"]
    detail: str


class ExplanationData(BaseModel):
    notes: List[str] = Field(default_factory=list)
    audit_trace: List[AuditTraceStep] = Field(default_factory=list)


class ProcessingError(BaseModel):
    code: Literal["INPUT_VALIDATION", "INSUFFICIENT_EVIDENCE", "POLICY_CONFLICT"]
    message: str


class OutputResponse(BaseModel):
    version: str = "AAC-0.2"
    generated_at: str
    patient: Patient
    encounter: Encounter
    facts: ClinicalFacts
    suggestions: List[CodeSuggestion]
    edits: ComplianceEdits
    readiness: ClaimReadiness
    explanation: ExplanationData
    errors: List[ProcessingError] = Field(default_factory=list)