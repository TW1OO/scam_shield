import os
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from services.call_service import record, OUTPUT_DIR
from database import get_db
from models import Recording

router = APIRouter(prefix="/call", tags=["call"])


@router.post("/record")
def start_record():
    result = record(duration=5)
    return {"message": "녹화 완료", **result}


@router.get("/recordings")
def list_recordings(db: Session = Depends(get_db)):
    recordings = db.query(Recording).order_by(Recording.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "video": os.path.basename(r.video_path),
            "audio": os.path.basename(r.audio_path),
            "duration": r.duration,
            "created_at": r.created_at.isoformat(),
        }
        for r in recordings
    ]


@router.get("/files/{filename}")
def download_file(filename: str):
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    return FileResponse(filepath, filename=filename)
