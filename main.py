"""
FastAPI application for the Aurevtech AI Coder medical coding engine.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import Dict, Any
import uvicorn

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

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize the engine
engine = AurevtechEngine()


@app.get("/")
async def root():
    """Root endpoint - serve the web interface."""
    from fastapi.responses import FileResponse
    return FileResponse("static/index.html")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
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


# Example endpoint for testing
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


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )