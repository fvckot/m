"""
Enhanced FastAPI application for the Aurevtech AI Coder medical coding engine.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import Dict, Any
import uvicorn
import os

from models import InputRequest, OutputResponse
from aurevtech_engine import AurevtechEngine

# Initialize FastAPI app
app = FastAPI(
    title="Aurevtech AI Coder",
    description="AI medical coding engine for clinical documentation",
    version="0.2.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files if directory exists
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize the engine
engine = AurevtechEngine()

@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    """Custom 404 handler."""
    return HTMLResponse(
        content="""
        <html>
            <head><title>Aurevtech AI Coder - Page Not Found</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 50px;">
                <h1>Aurevtech AI Coder</h1>
                <h2>404 - Page Not Found</h2>
                <p>The requested page could not be found.</p>
                <p><a href="/" style="color: #007bff;">Go to Home Page</a></p>
                <hr style="width: 50%; margin: 30px auto;">
                <p><strong>Available Endpoints:</strong></p>
                <ul style="text-align: left; display: inline-block;">
                    <li><a href="/">Web Interface</a></li>
                    <li><a href="/health">Health Check</a></li>
                    <li><a href="/docs">API Documentation</a></li>
                    <li><a href="/system/info">System Information</a></li>
                </ul>
            </body>
        </html>
        """,
        status_code=404
    )

@app.get("/")
async def root():
    """Root endpoint - serve the web interface."""
    try:
        if os.path.exists("static/index.html"):
            return FileResponse("static/index.html")
        else:
            # Return a simple HTML page if static files don't exist
            return HTMLResponse(content=get_simple_frontend())
    except Exception as e:
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Aurevtech AI Coder</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 50px;">
                    <h1>Aurevtech AI Coder</h1>
                    <h2>Medical Coding Engine</h2>
                    <p style="color: red;">Frontend loading error: {str(e)}</p>
                    <p><a href="/docs" style="color: #007bff;">Access API Documentation</a></p>
                    <p><a href="/health" style="color: #007bff;">Check System Health</a></p>
                </body>
            </html>
            """
        )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Aurevtech AI Coder",
        "version": "AAC-0.2",
        "system_info": engine.get_system_info()
    }

@app.post("/code", response_model=OutputResponse)
async def process_medical_coding(request: InputRequest):
    """
    Process medical coding request.
    
    Takes clinical documentation and returns structured medical codes
    with compliance checking and claim readiness assessment.
    """
    try:
        # Validate input
        errors = engine.validate_input(request.model_dump())
        if errors:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Input validation failed",
                    "errors": [{"code": e.code, "message": e.message} for e in errors]
                }
            )
        
        # Process request
        response = engine.process_request(request)
        
        # Return appropriate response based on mode
        if request.mode == "analyze":
            # Remove explanation notes for analyze mode
            response.explanation.notes = []
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Internal server error",
                "error": str(e)
            }
        )

@app.post("/code/validate")
async def validate_input(request_data: Dict[Any, Any]):
    """Validate input data without processing."""
    try:
        errors = engine.validate_input(request_data)
        return {
            "valid": len(errors) == 0,
            "errors": [{"code": e.code, "message": e.message} for e in errors]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Validation error",
                "error": str(e)
            }
        )

@app.get("/system/info")
async def system_info():
    """Get detailed system information."""
    return {
        "service": "Aurevtech AI Coder",
        "version": "AAC-0.2",
        "status": "operational",
        "endpoints": {
            "/": "Web interface",
            "/health": "Health check",
            "/code": "Medical coding endpoint",
            "/docs": "API documentation"
        },
        **engine.get_system_info()
    }

@app.get("/example")
async def get_example_request():
    """Get an example request for testing."""
    return {
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

def get_simple_frontend():
    """Return a simple frontend if static files are not available."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aurevtech AI Coder</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        textarea { height: 100px; }
        .btn { background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%; }
        .btn:hover { background: #2980b9; }
        .result { margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 4px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Aurevtech AI Coder</h1>
        <p style="text-align: center; color: #7f8c8d;">AI Medical Coding Engine for Clinical Documentation</p>
        
        <form id="codingForm">
            <div class="form-group">
                <label>Mode</label>
                <select id="mode" name="mode">
                    <option value="analyze">Analyze</option>
                    <option value="explain">Explain</option>
                </select>
            </div>
            
            <div class="grid">
                <div class="form-group">
                    <label>Patient Age</label>
                    <input type="number" id="age" name="age" value="46" required>
                </div>
                <div class="form-group">
                    <label>Patient Sex</label>
                    <select id="sex" name="sex" required>
                        <option value="F">Female</option>
                        <option value="M">Male</option>
                        <option value="U">Unknown</option>
                    </select>
                </div>
            </div>
            
            <div class="grid">
                <div class="form-group">
                    <label>Date</label>
                    <input type="date" id="date" name="date" required>
                </div>
                <div class="form-group">
                    <label>Place of Service</label>
                    <select id="pos_code" name="pos_code" required>
                        <option value="11">Office</option>
                        <option value="23">Emergency Room</option>
                        <option value="22">Hospital</option>
                    </select>
                </div>
            </div>
            
            <div class="grid">
                <div class="form-group">
                    <label>Payer</label>
                    <input type="text" id="payer" name="payer" value="GenericPPO" required>
                </div>
                <div class="form-group">
                    <label>Provider Type</label>
                    <input type="text" id="provider_type" name="provider_type" value="Internal Medicine" required>
                </div>
            </div>
            
            <div class="form-group">
                <label>Clinical Note</label>
                <textarea id="clinical_note" name="clinical_note" required placeholder="Enter clinical documentation...">Patient presents with palpitations. Normal physical examination. ECG performed and interpreted showing normal sinus rhythm.</textarea>
            </div>
            
            <button type="submit" class="btn">Process Medical Coding</button>
        </form>
        
        <div id="result" class="result" style="display: none;">
            <h3>Results</h3>
            <pre id="resultContent"></pre>
        </div>
    </div>

    <script>
        // Set today's date
        document.getElementById('date').valueAsDate = new Date();
        
        document.getElementById('codingForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const requestData = {
                mode: formData.get('mode'),
                patient: {
                    age: parseInt(formData.get('age')),
                    sex: formData.get('sex')
                },
                encounter: {
                    date: formData.get('date'),
                    pos_code: formData.get('pos_code'),
                    payer: formData.get('payer'),
                    provider_type: formData.get('provider_type')
                },
                clinical_note: formData.get('clinical_note'),
                structured: {
                    diagnoses: [],
                    orders: [],
                    procedures: [],
                    vitals: {},
                    meds_administered: []
                }
            };

            try {
                const response = await fetch('/code', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(requestData)
                });

                const result = await response.json();
                
                document.getElementById('result').style.display = 'block';
                document.getElementById('resultContent').textContent = JSON.stringify(result, null, 2);
                
                if (!response.ok) {
                    document.getElementById('resultContent').style.color = 'red';
                }
            } catch (error) {
                document.getElementById('result').style.display = 'block';
                document.getElementById('resultContent').textContent = 'Error: ' + error.message;
                document.getElementById('resultContent').style.color = 'red';
            }
        });
    </script>
</body>
</html>
    """

if __name__ == "__main__":
    print("🚀 Starting Aurevtech AI Coder Server...")
    print("📊 Medical Coding Engine v0.2.0")
    print("🌐 Web Interface: http://127.0.0.1:8000/")
    print("📚 API Documentation: http://127.0.0.1:8000/docs")
    print("💚 Health Check: http://127.0.0.1:8000/health")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 50)
    
    uvicorn.run(
        "enhanced_main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )