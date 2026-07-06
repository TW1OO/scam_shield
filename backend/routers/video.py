import os
import asyncio
import tempfile
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from services.video_service import analyze_video_file

router = APIRouter(prefix="/video", tags=["video"])

# 프레임 수 x HuggingFace 호출 시간이 누적되므로 여유 있게 잡는다.
ANALYSIS_TIMEOUT = 120


class VideoAnalyzeResponse(BaseModel):
    risk_level: str
    probability: int
    detected_patterns: list[str]
    reasons: list[str]
    recommendation: str


@router.post("/analyze", response_model=VideoAnalyzeResponse)
async def analyze(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="영상 파일만 업로드할 수 있습니다.")

    video_bytes = await file.read()
    if not video_bytes:
        raise HTTPException(status_code=400, detail="영상 파일이 비어 있습니다.")

    suffix = os.path.splitext(file.filename or "")[1] or ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(video_bytes)
        tmp_path = tmp.name

    try:
        return await asyncio.wait_for(
            asyncio.to_thread(analyze_video_file, tmp_path), timeout=ANALYSIS_TIMEOUT
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=502, detail="영상 분석 응답 시간이 초과되었습니다. 다시 시도해주세요.")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"영상 분석에 실패했습니다: {e}")
    finally:
        os.remove(tmp_path)
