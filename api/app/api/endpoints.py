import time
from typing import List
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import Response

from app.models.schemas import SCTRequest
from app.services.ai_extractor import extract_parts_from_images
from app.services.sct_builder import generate_sct

router = APIRouter()

@router.post("/extract")
async def extract_measurements(files: List[UploadFile] = File(...)):
    """Receives one or more images, passing them to an LLM Vision service to extract cuts."""
    try:
        parts = await extract_parts_from_images(files)
        return {"parts": [p.dict() for p in parts]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image(s): {str(e)}")

@router.post("/generate-sct")
async def create_sct_file(request: SCTRequest):
    """Takes JSON parts and returns a downloadable .sct file"""
    try:
        sct_content = generate_sct(request.parts)
        
        timestamp = int(time.time())
        filename = f"cortes_{timestamp}.sct"
        
        return Response(
            content=sct_content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating file: {str(e)}")
