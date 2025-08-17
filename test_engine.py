"""
Test script for the Aurevtech AI Coder medical coding engine.
"""

import json
import requests
from models import InputRequest
from aurevtech_engine import AurevtechEngine


def test_engine_directly():
    """Test the engine directly without API."""
    print("Testing Aurevtech Engine Directly...")
    print("=" * 50)
    
    # Initialize engine
    engine = AurevtechEngine()
    
    # Create test request
    test_request = InputRequest(
        mode="explain",
        patient={"age": 46, "sex": "F"},
        encounter={
            "date": "2025-08-16",
            "pos_code": "11",
            "payer": "GenericPPO",
            "provider_type": "Internal Medicine"
        },
        clinical_note="Patient presents with palpitations. Normal physical examination. ECG performed and interpreted showing normal sinus rhythm. Separate visit-level assessment for new complaint of palpitations.",
        structured={
            "diagnoses": [],
            "orders": ["ECG 12-lead"],
            "procedures": [],
            "vitals": {"bp": "118/72", "hr": "92", "temp": "98.6"},
            "meds_administered": []
        }
    )
    
    # Process request
    response = engine.process_request(test_request)
    
    # Display results
    print(f"Version: {response.version}")
    print(f"Generated at: {response.generated_at}")
    print()
    
    print("CLINICAL FACTS:")
    print(f"Problems: {response.facts.problems}")
    print(f"Findings: {response.facts.findings}")
    print(f"Orders: {response.facts.orders}")
    print(f"Procedures: {response.facts.procedures}")
    print(f"Indications: {response.facts.indications}")
    print()
    
    print("CODE SUGGESTIONS:")
    for suggestion in response.suggestions:
        print(f"  {suggestion.code} ({suggestion.system}): {suggestion.description}")
        print(f"    Confidence: {suggestion.confidence:.2f}")
        print(f"    Rationale: {suggestion.rationale}")
        if suggestion.modifiers:
            print(f"    Modifiers: {suggestion.modifiers}")
        if suggestion.flags:
            print(f"    Flags: {suggestion.flags}")
        print()
    
    print("COMPLIANCE EDITS:")
    if response.edits.ncci_ptp:
        print("  NCCI PTP:")
        for edit in response.edits.ncci_ptp:
            print(f"    {edit.primary} + {edit.secondary}: {edit.status}")
            if edit.modifier_candidates:
                print(f"      Modifier candidates: {edit.modifier_candidates}")
            print(f"      {edit.note}")
    
    if response.edits.mue:
        print("  MUE:")
        for edit in response.edits.mue:
            print(f"    {edit.code}: {edit.proposed_units}/{edit.mue_limit} ({edit.status})")
    
    if response.edits.payer_rules:
        print("  Payer Rules:")
        for edit in response.edits.payer_rules:
            print(f"    {edit.rule_id}: {edit.status}")
            print(f"      {edit.note}")
    print()
    
    print("CLAIM READINESS:")
    print(f"Score: {response.readiness.score:.2f}")
    print(f"Submit Ready: {response.readiness.submit_ready}")
    if response.readiness.issues:
        print(f"Issues: {response.readiness.issues}")
    if response.readiness.actions:
        print(f"Actions: {response.readiness.actions}")
    print()
    
    if response.explanation.notes:
        print("EXPLANATION NOTES:")
        for note in response.explanation.notes:
            print(f"  - {note}")
        print()
    
    print("AUDIT TRACE:")
    for step in response.explanation.audit_trace:
        print(f"  {step.step}: {step.detail}")
    
    return response


def test_api_endpoint():
    """Test the API endpoint (requires server to be running)."""
    print("\nTesting API Endpoint...")
    print("=" * 50)
    
    # Test data
    test_data = {
        "mode": "analyze",
        "patient": {"age": 46, "sex": "F"},
        "encounter": {
            "date": "2025-08-16",
            "pos_code": "11",
            "payer": "GenericPPO",
            "provider_type": "Internal Medicine"
        },
        "clinical_note": "Patient presents with palpitations. Normal physical examination. ECG performed and interpreted showing normal sinus rhythm. Separate visit-level assessment for new complaint of palpitations.",
        "structured": {
            "diagnoses": [],
            "orders": ["ECG 12-lead"],
            "procedures": [],
            "vitals": {"bp": "118/72", "hr": "92", "temp": "98.6"},
            "meds_administered": []
        }
    }
    
    try:
        # Make request to API
        response = requests.post(
            "http://127.0.0.1:8000/code",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("API Response successful!")
            print(f"Readiness Score: {result['readiness']['score']:.2f}")
            print(f"Suggestions: {len(result['suggestions'])}")
            print(f"Submit Ready: {result['readiness']['submit_ready']}")
        else:
            print(f"API Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("Could not connect to API. Make sure the server is running.")
        print("Run: python main.py")


def test_multiple_scenarios():
    """Test multiple clinical scenarios."""
    print("\nTesting Multiple Scenarios...")
    print("=" * 50)
    
    scenarios = [
        {
            "name": "Simple Office Visit",
            "note": "Patient presents for routine follow-up. Feeling well. Physical exam normal.",
            "expected_codes": ["99213"]
        },
        {
            "name": "Chest Pain with ECG",
            "note": "Patient complains of chest pain. ECG performed showing normal results. Reassurance given.",
            "expected_codes": ["99213", "93000", "R07.89"]
        },
        {
            "name": "Wound Repair",
            "note": "Patient with laceration to hand. Simple repair performed with sutures.",
            "expected_codes": ["12001", "S61.401A"]
        }
    ]
    
    engine = AurevtechEngine()
    
    for scenario in scenarios:
        print(f"\nScenario: {scenario['name']}")
        print("-" * 30)
        
        request = InputRequest(
            mode="analyze",
            patient={"age": 35, "sex": "M"},
            encounter={
                "date": "2025-08-17",
                "pos_code": "11",
                "payer": "Medicare",
                "provider_type": "Family Medicine"
            },
            clinical_note=scenario["note"]
        )
        
        response = engine.process_request(request)
        
        print(f"Suggested codes: {[s.code for s in response.suggestions]}")
        print(f"Readiness score: {response.readiness.score:.2f}")
        
        # Check if expected codes are present
        suggested_codes = [s.code for s in response.suggestions]
        found_expected = [code for code in scenario.get("expected_codes", []) if code in suggested_codes]
        
        if found_expected:
            print(f"✓ Found expected codes: {found_expected}")
        else:
            print("✗ Expected codes not found")


if __name__ == "__main__":
    # Test the engine directly
    response = test_engine_directly()
    
    # Test API endpoint
    test_api_endpoint()
    
    # Test multiple scenarios
    test_multiple_scenarios()
    
    print("\n" + "=" * 50)
    print("Testing complete!")
    
    # Save sample response to file
    with open("sample_response.json", "w") as f:
        json.dump(response.model_dump(), f, indent=2)
    print("Sample response saved to sample_response.json")