import os
import asyncio
import tempfile
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from services.deepvoice_service import analyze_voice_file

router = APIRouter(prefix="/deepvoice", tags=["deepvoice"])

# Reality Defender는 자체 폴링 타임아웃(60초)이 있지만, 드물게 그보다도
# 오래 걸리는 경우가 있어 우리 쪽에서도 상한을 둔다.
ANALYSIS_TIMEOUT = 90


class DeepvoiceResponse(BaseModel):
    risk_level: str
    probability: int
    detected_patterns: list[str]
    reasons: list[str]
    recommendation: str


@router.post("/analyze", response_model=DeepvoiceResponse)
async def analyze(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="음성 파일만 업로드할 수 있습니다.")

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="음성 파일이 비어 있습니다.")

    suffix = os.path.splitext(file.filename or "")[1] or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        return await asyncio.wait_for(
            asyncio.to_thread(analyze_voice_file, tmp_path), timeout=ANALYSIS_TIMEOUT
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=502, detail="음성 분석 응답 시간이 초과되었습니다. 다시 시도해주세요.")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"음성 분석에 실패했습니다: {e}")
    finally:
        os.remove(tmp_path)
