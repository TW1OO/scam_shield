import os
from dotenv import load_dotenv
from realitydefender import RealityDefender

load_dotenv() # .env읽기

API_KEY = os.getenv("REALITY_DEFENDER_API_KEY") # api키 가져오기

client = RealityDefender(api_key=API_KEY) # 클라이언트 생성

def detect_ai_voice(audio_path: str):
    """
    저장된 음성 파일을 AI 음성 탐지 API로 분석한다.
    """
    result = client.detect_file(audio_path)

    return {
        "is_ai": result["status"] != "AUTHENTIC",
        "status": result["status"],
        "confidence": result["score"],
        "provider": "Reality Defender",
        "models": result["models"],
        }