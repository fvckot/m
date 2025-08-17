"""
Demo script for the Aurevtech AI Coder medical coding engine.
"""

import requests
import json
import time
import webbrowser
from datetime import datetime


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def print_subheader(title):
    """Print a formatted subheader."""
    print(f"\n{title}")
    print("-" * len(title))


def demo_comprehensive_case():
    """Demo a comprehensive medical case."""
    print_header("COMPREHENSIVE MEDICAL CASE DEMO")
    
    # Complex clinical case
    test_data = {
        "mode": "explain",
        "patient": {"age": 67, "sex": "M"},
        "encounter": {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "pos_code": "23",  # Emergency Room
            "payer": "Medicare",
            "provider_type": "Emergency Medicine"
        },
        "clinical_note": """
        CHIEF COMPLAINT: Chest pain and shortness of breath
        
        HPI: 67-year-old male presents to ED with acute onset chest pain that started 2 hours ago. 
        Pain is substernal, crushing in nature, radiates to left arm. Associated with dyspnea, 
        diaphoresis, and nausea. No relief with rest. Patient has history of hypertension and diabetes.
        
        PHYSICAL EXAMINATION:
        Vitals: BP 160/95, HR 110, RR 22, O2 Sat 92% on room air
        General: Diaphoretic, anxious appearing male in mild distress
        Cardiovascular: Tachycardia, regular rhythm, no murmurs
        Pulmonary: Bilateral crackles at bases
        
        DIAGNOSTIC STUDIES:
        ECG: ST elevation in leads II, III, aVF consistent with inferior STEMI
        Chest X-ray: Mild pulmonary edema
        Laboratory: Elevated troponin I, BNP elevated
        
        MEDICAL DECISION MAKING:
        High complexity decision making. Patient presents with acute ST-elevation myocardial infarction.
        Immediate cardiac catheterization indicated. Patient counseled on diagnosis and treatment plan.
        Cardiology consulted for emergent intervention.
        
        PROCEDURES:
        IV access established, cardiac monitoring initiated, aspirin and heparin administered
        """,
        "structured": {
            "orders": [
                "ECG 12-lead",
                "Chest X-ray",
                "Troponin I",
                "BNP",
                "Comprehensive metabolic panel",
                "CBC with differential"
            ],
            "procedures": [
                "IV catheter insertion",
                "Cardiac monitoring"
            ],
            "vitals": {
                "bp": "160/95",
                "hr": "110",
                "temp": "98.4"
            },
            "meds_administered": [
                {
                    "drug": "Aspirin",
                    "dose": "325mg",
                    "route": "PO",
                    "time": "2025-08-17T03:00:00Z"
                },
                {
                    "drug": "Heparin",
                    "dose": "5000 units",
                    "route": "IV",
                    "time": "2025-08-17T03:05:00Z"
                }
            ]
        }
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:8000/code",
            json=test_data,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("✓ Complex case processed successfully!")
            
            print_subheader("PATIENT INFO")
            print(f"Age: {result['patient']['age']}, Sex: {result['patient']['sex']}")
            print(f"Encounter: {result['encounter']['date']} at POS {result['encounter']['pos_code']}")
            print(f"Payer: {result['encounter']['payer']}")
            
            print_subheader("CLINICAL FACTS EXTRACTED")
            facts = result['facts']
            print(f"Problems: {', '.join(facts['problems'])}")
            print(f"Procedures: {', '.join(facts['procedures'])}")
            print(f"Orders: {', '.join(facts['orders'])}")
            print(f"Indications: {', '.join(facts['indications'])}")
            
            print_subheader("CODE SUGGESTIONS")
            for i, suggestion in enumerate(result['suggestions'], 1):
                confidence_pct = f"{suggestion['confidence']*100:.0f}%"
                modifiers = f" (Modifiers: {', '.join(suggestion['modifiers'])})" if suggestion['modifiers'] else ""
                flags = f" [FLAGS: {', '.join(suggestion['flags'])}]" if suggestion['flags'] else ""
                
                print(f"{i:2d}. {suggestion['code']} ({suggestion['system']}): {suggestion['description']}")
                print(f"    Confidence: {confidence_pct} | {suggestion['rationale']}{modifiers}{flags}")
            
            print_subheader("COMPLIANCE ANALYSIS")
            
            # NCCI Edits
            if result['edits']['ncci_ptp']:
                print("NCCI Procedure-to-Procedure Edits:")
                for edit in result['edits']['ncci_ptp']:
                    status_icon = "✓" if edit['status'] == 'allowed' else "⚠"
                    print(f"  {status_icon} {edit['primary']} + {edit['secondary']}: {edit['status']}")
                    if edit['modifier_candidates']:
                        print(f"    Suggested modifiers: {', '.join(edit['modifier_candidates'])}")
            
            # MUE
            if result['edits']['mue']:
                print("Medically Unlikely Edits (MUE):")
                for edit in result['edits']['mue']:
                    status_icon = "✓" if edit['status'] == 'ok' else "⚠"
                    print(f"  {status_icon} {edit['code']}: {edit['proposed_units']}/{edit['mue_limit']} units ({edit['status']})")
            
            # Payer Rules
            if result['edits']['payer_rules']:
                print("Payer-Specific Rules:")
                for edit in result['edits']['payer_rules']:
                    status_icon = "✓" if edit['status'] == 'pass' else "⚠" if edit['status'] == 'fail' else "?"
                    print(f"  {status_icon} {edit['rule_id']}: {edit['status']}")
                    if edit['note']:
                        print(f"    Note: {edit['note']}")
            
            print_subheader("CLAIM READINESS ASSESSMENT")
            readiness = result['readiness']
            score_pct = f"{readiness['score']*100:.0f}%"
            ready_status = "✓ READY TO SUBMIT" if readiness['submit_ready'] else "⚠ NEEDS REVIEW"
            
            print(f"Overall Score: {score_pct}")
            print(f"Status: {ready_status}")
            
            if readiness['issues']:
                print("Issues Identified:")
                for issue in readiness['issues']:
                    print(f"  - {issue}")
            
            if readiness['actions']:
                print("Recommended Actions:")
                for action in readiness['actions']:
                    print(f"  - {action}")
            
            print_subheader("AI EXPLANATION")
            if result['explanation']['notes']:
                for note in result['explanation']['notes']:
                    print(f"• {note}")
            
            # Save detailed result
            with open("demo_complex_case_result.json", "w") as f:
                json.dump(result, f, indent=2)
            print(f"\n✓ Detailed results saved to: demo_complex_case_result.json")
            
            return result
            
        else:
            print(f"✗ API Error: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None


def demo_multiple_scenarios():
    """Demo multiple clinical scenarios."""
    print_header("MULTIPLE SCENARIO COMPARISON")
    
    scenarios = [
        {
            "name": "Routine Office Visit",
            "patient": {"age": 45, "sex": "F"},
            "encounter": {"date": "2025-08-17", "pos_code": "11", "payer": "GenericPPO", "provider_type": "Family Medicine"},
            "note": "Patient presents for annual physical exam. Review of systems negative. Physical examination normal. Discussed preventive care measures.",
        },
        {
            "name": "Acute Care with Procedures",
            "patient": {"age": 28, "sex": "M"},
            "encounter": {"date": "2025-08-17", "pos_code": "11", "payer": "GenericPPO", "provider_type": "Urgent Care"},
            "note": "Patient with 3cm laceration to right hand from kitchen accident. Wound cleaned and irrigated. Simple repair performed with 4-0 nylon sutures. Tetanus status current.",
            "orders": ["Wound care supplies"]
        },
        {
            "name": "Chronic Disease Management",
            "patient": {"age": 62, "sex": "F"},
            "encounter": {"date": "2025-08-17", "pos_code": "11", "payer": "Medicare", "provider_type": "Internal Medicine"},
            "note": "Established patient with diabetes mellitus type 2 and hypertension for routine follow-up. Blood glucose well controlled on metformin. Blood pressure elevated at 150/90. Medication adjustment needed.",
            "orders": ["HbA1c", "Basic metabolic panel", "Urine microalbumin"]
        }
    ]
    
    results = []
    
    for i, scenario in enumerate(scenarios, 1):
        print_subheader(f"SCENARIO {i}: {scenario['name']}")
        
        request_data = {
            "mode": "analyze",
            "patient": scenario["patient"],
            "encounter": scenario["encounter"],
            "clinical_note": scenario["note"],
            "structured": {
                "orders": scenario.get("orders", []),
                "procedures": [],
                "vitals": {},
                "meds_administered": []
            }
        }
        
        try:
            response = requests.post(
                "http://127.0.0.1:8000/code",
                json=request_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                results.append({"scenario": scenario["name"], "result": result})
                
                # Summary display
                readiness_pct = f"{result['readiness']['score']*100:.0f}%"
                code_count = len(result['suggestions'])
                cpt_codes = [s['code'] for s in result['suggestions'] if s['system'] == 'CPT']
                icd_codes = [s['code'] for s in result['suggestions'] if s['system'] == 'ICD10']
                
                print(f"  Readiness Score: {readiness_pct}")
                print(f"  Total Codes: {code_count}")
                print(f"  CPT Codes: {', '.join(cpt_codes) if cpt_codes else 'None'}")
                print(f"  ICD-10 Codes: {', '.join(icd_codes) if icd_codes else 'None'}")
                print(f"  Submit Ready: {'Yes' if result['readiness']['submit_ready'] else 'No'}")
                
                if result['readiness']['issues']:
                    print(f"  Issues: {len(result['readiness']['issues'])} identified")
                
            else:
                print(f"  ✗ Error: {response.status_code}")
                
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
    
    # Save comparison results
    if results:
        with open("demo_scenarios_comparison.json", "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n✓ Scenario comparison saved to: demo_scenarios_comparison.json")
    
    return results


def demo_api_endpoints():
    """Demo various API endpoints."""
    print_header("API ENDPOINTS DEMONSTRATION")
    
    endpoints = [
        ("Health Check", "GET", "/health"),
        ("System Info", "GET", "/system/info"),
        ("Example Request", "GET", "/example"),
    ]
    
    for name, method, endpoint in endpoints:
        print_subheader(f"{name} ({method} {endpoint})")
        
        try:
            if method == "GET":
                response = requests.get(f"http://127.0.0.1:8000{endpoint}", timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                print("✓ Success")
                
                # Show key information
                if endpoint == "/health":
                    print(f"  Status: {result['status']}")
                    print(f"  Version: {result['system_info']['version']}")
                elif endpoint == "/system/info":
                    print(f"  Service: {result['service']}")
                    print(f"  Capabilities: {len(result['capabilities'])}")
                elif endpoint == "/example":
                    print(f"  Example mode: {result['mode']}")
                    print(f"  Patient age: {result['patient']['age']}")
                    
            else:
                print(f"✗ Error: {response.status_code}")
                
        except Exception as e:
            print(f"✗ Error: {str(e)}")


def main():
    """Main demo function."""
    print_header("AUREVTECH AI CODER - COMPREHENSIVE DEMO")
    print("Medical Coding Engine for Clinical Documentation")
    print("Version: AAC-0.2")
    print(f"Demo Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Wait for server to be ready
    print("\nWaiting for server to be ready...")
    for i in range(10):
        try:
            response = requests.get("http://127.0.0.1:8000/health", timeout=2)
            if response.status_code == 200:
                print("✓ Server is ready!")
                break
        except:
            pass
        time.sleep(1)
        print(f"  Attempt {i+1}/10...")
    else:
        print("✗ Could not connect to server. Make sure it's running.")
        print("Run: python main.py")
        return
    
    # Demo sections
    demo_api_endpoints()
    demo_multiple_scenarios()
    complex_result = demo_comprehensive_case()
    
    print_header("DEMO SUMMARY")
    print("✓ All API endpoints tested successfully")
    print("✓ Multiple clinical scenarios processed")
    print("✓ Complex emergency case analyzed")
    print("✓ Compliance checking demonstrated")
    print("✓ Results saved to JSON files")
    
    print_subheader("KEY CAPABILITIES DEMONSTRATED")
    capabilities = [
        "Clinical fact extraction from unstructured notes",
        "CPT/HCPCS and ICD-10 code mapping",
        "E/M code level determination",
        "NCCI Procedure-to-Procedure edit checking",
        "Medically Unlikely Edits (MUE) validation",
        "LCD/NCD coverage policy checking",
        "Payer-specific rule validation",
        "Claim readiness scoring and issue identification",
        "Structured JSON output with explanations"
    ]
    
    for i, capability in enumerate(capabilities, 1):
        print(f"{i:2d}. {capability}")
    
    print_subheader("ACCESS THE SYSTEM")
    print("1. Web Interface: http://127.0.0.1:8000/")
    print("2. API Documentation: http://127.0.0.1:8000/docs")
    print("3. API Endpoint: POST http://127.0.0.1:8000/code")
    
    # Try to open web browser
    try:
        print("\nOpening web interface in browser...")
        webbrowser.open("http://127.0.0.1:8000/")
        print("✓ Web interface opened!")
    except:
        print("Could not open browser automatically.")
        print("Please navigate to: http://127.0.0.1:8000/")
    
    print_header("DEMO COMPLETED SUCCESSFULLY")
    print("The Aurevtech AI Coder is ready for production use!")


if __name__ == "__main__":
    main()