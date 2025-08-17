# Aurevtech AI Coder - Medical Coding Engine

## Overview

The Aurevtech AI Coder is a sophisticated medical coding engine that processes clinical documentation and returns structured medical codes with comprehensive compliance checking. The system extracts clinical facts from unstructured notes, suggests appropriate CPT/HCPCS/ICD-10 codes, and performs compliance validation against NCCI, MUE, LCD/NCD, and payer-specific rules.

## Features

- **Clinical Fact Extraction**: Extracts problems, findings, procedures, and orders from clinical notes
- **Medical Code Mapping**: Suggests CPT/HCPCS and ICD-10 codes based on clinical facts
- **E/M Code Determination**: Automatically determines appropriate Evaluation & Management codes
- **Compliance Checking**: 
  - NCCI Procedure-to-Procedure (PTP) edits
  - Medically Unlikely Edits (MUE) validation
  - Local/National Coverage Determination (LCD/NCD) checking
  - Payer-specific rule validation
- **Claim Readiness Scoring**: Calculates readiness score and identifies issues/actions
- **Dual Modes**: `analyze` (JSON only) and `explain` (JSON + human-readable explanations)

## API Specification

### Input Contract

```json
{
  "mode": "analyze | explain",
  "patient": {"age": 0, "sex": "F|M|U"},
  "encounter": {
    "date": "YYYY-MM-DD",
    "pos_code": "string",
    "payer": "string",
    "provider_type": "string"
  },
  "clinical_note": "free text with HPI/ROS/PE/MDM/Orders/Results",
  "structured": {
    "diagnoses": ["ICD10? optional"],
    "orders": ["text"],
    "procedures": ["text"],
    "vitals": {"bp":"", "hr":"", "temp":""},
    "meds_administered": [{"drug":"", "dose":"", "route":"", "time":"ISO"}]
  }
}
```

### Output Contract

```json
{
  "version": "AAC-0.2",
  "generated_at": "ISO8601",
  "patient": {"age": 0, "sex": "F|M|U"},
  "encounter": {"date": "YYYY-MM-DD", "pos_code": "string", "payer": "string", "provider_type": "string"},
  "facts": {
    "problems": ["string"],
    "findings": ["string"],
    "orders": ["string"],
    "procedures": ["string"],
    "imaging_labs": ["string"],
    "indications": ["string"]
  },
  "suggestions": [
    {
      "code": "string",
      "system": "CPT|HCPCS|ICD10",
      "description": "string",
      "modifiers": ["string"],
      "units": 1,
      "rationale": "string",
      "confidence": 0.0,
      "flags": ["Needs-Review|Missing-Docs|Check-Payer-Policy"]
    }
  ],
  "edits": {
    "ncci_ptp": [...],
    "mue": [...],
    "lcd_ncd": [...],
    "payer_rules": [...]
  },
  "readiness": {
    "score": 0.0,
    "issues": ["string"],
    "actions": ["string"],
    "submit_ready": true
  },
  "explanation": {
    "notes": ["string"],
    "audit_trace": [...]
  },
  "errors": [...]
}
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd medical_coding_engine
   ```

2. **Set up Python environment**:
   ```bash
   uv venv
   .venv\Scripts\activate  # Windows
   uv pip install -r requirements.txt
   ```

3. **Install dependencies**:
   ```bash
   uv pip install fastapi uvicorn pydantic python-multipart requests regex nltk scikit-learn
   ```

## Usage

### Running the API Server

```bash
python main.py
```

The API will be available at `http://127.0.0.1:8000`

### API Endpoints

- `GET /` - System information
- `GET /health` - Health check
- `POST /code` - Main medical coding endpoint
- `POST /code/validate` - Validate input without processing
- `GET /example` - Get example request for testing
- `GET /docs` - Interactive API documentation

### Testing

Run the comprehensive test suite:

```bash
python test_engine.py
```

### Example Usage

```python
import requests

# Example request
test_data = {
    "mode": "analyze",
    "patient": {"age": 46, "sex": "F"},
    "encounter": {
        "date": "2025-08-16",
        "pos_code": "11",
        "payer": "GenericPPO",
        "provider_type": "Internal Medicine"
    },
    "clinical_note": "Patient presents with palpitations. Normal physical examination. ECG performed and interpreted showing normal sinus rhythm.",
    "structured": {
        "orders": ["ECG 12-lead"],
        "vitals": {"bp": "118/72", "hr": "92", "temp": "98.6"}
    }
}

# Make request
response = requests.post(
    "http://127.0.0.1:8000/code",
    json=test_data
)

result = response.json()
print(f"Readiness Score: {result['readiness']['score']}")
print(f"Suggested Codes: {[s['code'] for s in result['suggestions']]}")
```

## Architecture

The system consists of several key components:

### Core Modules

1. **models.py** - Pydantic data models for request/response structures
2. **fact_extractor.py** - Clinical fact extraction from unstructured notes
3. **code_mapper.py** - Medical code mapping and suggestion engine
4. **compliance_checker.py** - Compliance validation (NCCI, MUE, LCD/NCD, payer rules)
5. **aurevtech_engine.py** - Main orchestration engine
6. **main.py** - FastAPI web application
7. **medical_data.py** - Medical coding reference data and lookup tables

### Processing Flow

1. **Input Validation** - Validate request structure and required fields
2. **Fact Extraction** - Extract clinical facts from unstructured notes
3. **Code Mapping** - Map clinical facts to appropriate medical codes
4. **Compliance Checking** - Validate codes against various compliance rules
5. **Readiness Scoring** - Calculate claim readiness and identify issues
6. **Response Generation** - Format structured JSON response

## Configuration

### Medical Data

The system includes reference data for:
- Common CPT/HCPCS codes with descriptions and MUE limits
- ICD-10 diagnostic codes
- NCCI PTP bundling rules
- Clinical term to code mappings
- Payer-specific rules
- LCD/NCD policies (simplified)

### Customization

To customize the system:

1. **Add new codes**: Update `medical_data.py` with new CPT/ICD codes
2. **Modify rules**: Adjust compliance rules in `compliance_checker.py`
3. **Enhance extraction**: Improve clinical fact extraction in `fact_extractor.py`
4. **Add payers**: Include new payer rules in `medical_data.py`

## Compliance Features

### NCCI PTP (Procedure-to-Procedure) Edits
- Checks code pairs for bundling rules
- Identifies when modifiers are allowed
- Suggests appropriate modifiers (25, 59, XS, XU, etc.)

### MUE (Medically Unlikely Edits)
- Validates proposed units against MUE limits
- Flags codes that exceed limits
- Suggests unit reduction or split billing

### LCD/NCD Coverage
- Checks services against coverage policies
- Validates supporting ICD-10 diagnoses
- Identifies missing documentation requirements

### Payer-Specific Rules
- Bilateral procedure preferences (modifier 50 vs RT/LT)
- Telehealth modifier requirements
- Frequency limitations
- Coverage policies

## Scoring Algorithm

The claim readiness score starts at 1.0 and is reduced based on:
- NCCI bundling without proper justification (-0.2)
- MUE exceedances (-0.1 each)
- LCD/NCD criteria not met (-0.1)
- Payer rule violations (-0.1)
- Low confidence codes (-0.05 each)
- Flagged codes (-0.05 each)

Submit ready = (score ≥ 0.8 && no errors)

## Error Handling

The system handles various error conditions:
- `INPUT_VALIDATION` - Missing or invalid input fields
- `INSUFFICIENT_EVIDENCE` - Unable to extract sufficient clinical information
- `POLICY_CONFLICT` - Conflicting compliance rules or policies

## Development

### Adding New Features

1. **New clinical terms**: Add to `CLINICAL_TERM_MAPPINGS` in `medical_data.py`
2. **New compliance rules**: Extend `compliance_checker.py`
3. **New code types**: Update `code_mapper.py` and models
4. **New payer rules**: Add to `PAYER_RULES` in `medical_data.py`

### Testing

The test suite includes:
- Direct engine testing
- API endpoint testing
- Multiple clinical scenarios
- Edge case validation

## License

This software is proprietary and confidential. All rights reserved.

## Support

For technical support or questions, please contact the development team.

---

**Version**: AAC-0.2  
**Last Updated**: August 2025