import mss
import cv2
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wavfile
import threading
import time
import os
import logging
from database import SessionLocal
from models import Recording
from services.deepvoice_service import detect_ai_voice
from services.video_service import detect_ai_video

DURATION = 5
FPS = 10
SAMPLE_RATE = 44100
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "recordings")


def _record_screen(output_path: str, duration: int):
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        width, height = monitor["width"], monitor["height"]

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_path, fourcc, FPS, (width, height))

        start = time.time()
        while time.time() - start < duration:
            frame = np.array(sct.grab(monitor))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            out.write(frame)
            time.sleep(1 / FPS)

        out.release()


def _record_audio(output_path: str, duration: int):
    recording = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=2,
        dtype="int16",
    )
    sd.wait()
    wavfile.write(output_path, SAMPLE_RATE, recording)


def record(duration: int = DURATION) -> dict:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    timestamp = int(time.time())
    video_path = os.path.join(OUTPUT_DIR, f"screen_{timestamp}.mp4")
    audio_path = os.path.join(OUTPUT_DIR, f"audio_{timestamp}.wav")

    video_thread = threading.Thread(target=_record_screen, args=(video_path, duration))
    audio_thread = threading.Thread(target=_record_audio, args=(audio_path, duration))

    video_thread.start()
    audio_thread.start()

    video_thread.join()
    audio_thread.join()

    try:
        audio_result = detect_ai_voice(audio_path)
    except Exception as e:
        logging.exception("Audio analysis failed")
        audio_result = {
            "status": "ERROR",
            "message": str(e),
        }

    try:
        video_result = detect_ai_video(video_path)
    except Exception as e:
        logging.exception("Video analysis failed")
        video_result = {
            "status": "ERROR",
            "message": str(e),
        }

    db = SessionLocal()
    try:
        record_entry = Recording(
            video_path=video_path,
            audio_path=audio_path,
            duration=duration,
        )
        db.add(record_entry)
        db.commit()
        db.refresh(record_entry)
        return {
            "id": record_entry.id,
            "video_path": os.path.basename(video_path),
            "audio_path": os.path.basename(audio_path),
            "duration": duration,
            "created_at": record_entry.created_at.isoformat(),
            "audio_analysis": audio_result,
            "video_analysis": video_result,
            }
    finally:
        db.close()
