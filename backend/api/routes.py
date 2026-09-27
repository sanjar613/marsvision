from fastapi import APIRouter, UploadFile, File, HTTPException
from schemas.response import AnalysisResponse
from services.video_service import process_video_file

router = APIRouter()

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_endpoint(file: UploadFile = File(...)):
    filename = file.filename or ''
    if not filename.lower().endswith(('.mp4', '.avi', '.mov')):
        raise HTTPException(status_code=400, detail="Unsupported file format")
    
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        result = await process_video_file(file_bytes)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return result