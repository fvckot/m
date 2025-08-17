"""
Railway-optimized version of the medical coding engine.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
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

@app.get("/")
async def root():
    """Root endpoint - simple HTML page."""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Aurevtech AI Coder</title>
        <style>
            body { font-family: Arial; margin: 40px; text-align: center; }
            .container { max-width: 600px; margin: 0 auto; }
            .btn { background: #007bff; color: white; padding: 10px 20px; 
                   text-decoration: none; border-radius: 5px; margin: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏥 Aurevtech AI Coder</h1>
            <h2>Medical Coding Engine</h2>
            <p>AI-powered medical coding with compliance checking</p>
            
            <div style="margin: 30px 0;">
                <a href="/docs" class="btn">📚 API Documentation</a>
                <a href="/health" class="btn">💚 Health Check</a>
                <a href="/example" class="btn">📋 Example Request</a>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3>Quick Test API</h3>
                <p>POST to <code>/code</code> with medical data</p>
                <p>See <a href="/docs">/docs</a> for interactive testing</p>
            </div>
        </div>
    </body>
    </html>
    """)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Aurevtech AI Coder",
        "version": "AAC-0.2"
    }

@app.post("/code", response_model=OutputResponse)
async def process_medical_coding(request: InputRequest):
    """Process medical coding request."""
    try:
        response = engine.process_request(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/example")
async def get_example():
    """Get example request."""
    return {
        "mode": "analyze",
        "patient": {"age": 46, "sex": "F"},
        "encounter": {
            "date": "2025-01-17",
            "pos_code": "11",
            "payer": "GenericPPO",
            "provider_type": "Internal Medicine"
        },
        "clinical_note": "Patient with palpitations. ECG performed showing normal rhythm.",
        "structured": {"orders": ["ECG 12-lead"], "vitals": {"bp": "120/80"}}
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=False
    )
