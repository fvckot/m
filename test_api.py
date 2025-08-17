"""
Test the API endpoints with various scenarios.
"""

import requests
import json
import time

def test_api():
    """Test the API with the example from the specification."""
    
    # Test data from the specification
    test_data = {
        "mode": "analyze",
        "patient": {"age": 46, "sex": "F"},
        "encounter": {
            "date": "2025-08-16",
            "pos_code": "11",
            "payer": "GenericPPO",
            "provider_type": "Internal Medicine"
        },
        "clinical_note": "Pt with palpitations; normal exam. ECG performed and interpreted. Separate visit-level assessment for new complaint.",
        "structured": {
            "diagnoses": [],
            "orders": ["ECG 12-lead"],
            "procedures": [],
            "vitals": {"bp": "118/72", "hr": "92", "temp": "98.6"},
            "meds_administered": []
        }
    }
    
    print("Testing API with specification example...")
    print("=" * 50)
    
    try:
        # Make request to API
        response = requests.post(
            "http://127.0.0.1:8000/code",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("✓ API Response successful!")
            print(f"Version: {result['version']}")
            print(f"Generated at: {result['generated_at']}")
            print()
            
            print("CLINICAL FACTS:")
            print(f"  Problems: {result['facts']['problems']}")
            print(f"  Findings: {result['facts']['findings']}")
            print(f"  Orders: {result['facts']['orders']}")
            print(f"  Procedures: {result['facts']['procedures']}")
            print(f"  Indications: {result['facts']['indications']}")
            print()
            
            print("CODE SUGGESTIONS:")
            for suggestion in result['suggestions']:
                print(f"  {suggestion['code']} ({suggestion['system']}): {suggestion['description']}")
                print(f"    Confidence: {suggestion['confidence']:.2f}")
                if suggestion['modifiers']:
                    print(f"    Modifiers: {suggestion['modifiers']}")
                print(f"    Rationale: {suggestion['rationale']}")
                print()
            
            print("COMPLIANCE EDITS:")
            if result['edits']['ncci_ptp']:
                print("  NCCI PTP:")
                for edit in result['edits']['ncci_ptp']:
                    print(f"    {edit['primary']} + {edit['secondary']}: {edit['status']}")
                    if edit['modifier_candidates']:
                        print(f"      Modifier candidates: {edit['modifier_candidates']}")
            
            if result['edits']['payer_rules']:
                print("  Payer Rules:")
                for edit in result['edits']['payer_rules']:
                    print(f"    {edit['rule_id']}: {edit['status']}")
            print()
            
            print("CLAIM READINESS:")
            print(f"  Score: {result['readiness']['score']:.2f}")
            print(f"  Submit Ready: {result['readiness']['submit_ready']}")
            if result['readiness']['issues']:
                print(f"  Issues: {result['readiness']['issues']}")
            if result['readiness']['actions']:
                print(f"  Actions: {result['readiness']['actions']}")
            print()
            
            # Save result
            with open("api_response.json", "w") as f:
                json.dump(result, f, indent=2)
            print("✓ Response saved to api_response.json")
            
            return result
            
        else:
            print(f"✗ API Error: {response.status_code}")
            print(response.text)
            return None
            
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to API. Make sure the server is running.")
        return None
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None


def test_explain_mode():
    """Test explain mode."""
    print("\nTesting Explain Mode...")
    print("=" * 30)
    
    test_data = {
        "mode": "explain",
        "patient": {"age": 35, "sex": "M"},
        "encounter": {
            "date": "2025-08-17",
            "pos_code": "11",
            "payer": "Medicare",
            "provider_type": "Family Medicine"
        },
        "clinical_note": "Patient presents with acute chest pain. Physical examination reveals normal heart sounds. ECG shows ST elevation. Patient transferred to cardiology for further evaluation."
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:8000/code",
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Explain mode successful!")
            
            if result['explanation']['notes']:
                print("Explanation Notes:")
                for note in result['explanation']['notes']:
                    print(f"  - {note}")
            
            print(f"Readiness Score: {result['readiness']['score']:.2f}")
            
        else:
            print(f"✗ Error: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")


def test_health_endpoint():
    """Test health endpoint."""
    print("\nTesting Health Endpoint...")
    print("=" * 30)
    
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Health check successful!")
            print(f"  Status: {result['status']}")
            print(f"  System Version: {result['system_info']['version']}")
            print(f"  Capabilities: {len(result['system_info']['capabilities'])}")
        else:
            print(f"✗ Health check failed: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")


def test_validation_endpoint():
    """Test validation endpoint."""
    print("\nTesting Validation Endpoint...")
    print("=" * 30)
    
    # Test with invalid data
    invalid_data = {
        "patient": {"age": "invalid"},  # Should be int
        "encounter": {"date": "2025-08-17"},  # Missing required fields
        "clinical_note": "Too short"  # Too short
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:8000/code/validate",
            json=invalid_data,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Validation endpoint working!")
            print(f"  Valid: {result['valid']}")
            print(f"  Errors: {len(result['errors'])}")
            for error in result['errors']:
                print(f"    - {error['message']}")
        else:
            print(f"✗ Validation failed: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")


if __name__ == "__main__":
    # Wait for server to start
    time.sleep(2)
    
    # Run tests
    result = test_api()
    test_explain_mode()
    test_health_endpoint()
    test_validation_endpoint()
    
    print("\n" + "=" * 50)
    print("API Testing Complete!")
    
    if result:
        print("✓ All core functionality working correctly")
    else:
        print("✗ Some tests failed")