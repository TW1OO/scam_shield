import os
from dotenv import load_dotenv
from realitydefender import RealityDefender

load_dotenv() # .env읽기

API_KEY = os.getenv("REALITY_DEFENDER_API_KEY") # api키 가져오기

client = RealityDefender(api_key=API_KEY) # 클라이언트 생성

# Reality Defender의 overall status는 문서상 "MANIPULATED"/"AUTHENTIC" 둘 중
# 하나로 안내되지만, 실제로는 음성이 너무 짧거나 분석 불가한 경우
# "NOT_APPLICABLE"도 반환된다. 이건 "가짜로 판정"된 게 아니라 "판단 불가"이므로
# 절대 AUTHENTIC이 아니라고 해서 곧바로 AI로 취급하면 안 된다.
MANIPULATED_STATUSES = {"MANIPULATED", "FAKE", "DEEPFAKE"}
INCONCLUSIVE_STATUSES = {"NOT_APPLICABLE", "ANALYZING"}


def detect_ai_voice(audio_path: str):
    """
    저장된 음성 파일을 AI 음성 탐지 API로 분석한다.
    """
    result = client.detect_file(audio_path)
    status = result["status"]

    return {
        "is_ai": status in MANIPULATED_STATUSES,
        "is_inconclusive": status in INCONCLUSIVE_STATUSES,
        "status": status,
        "confidence": result["score"],
        "provider": "Reality Defender",
        "models": result["models"],
        }


def _risk_level(probability: int) -> str:
    if probability >= 80:
        return "매우 높음"
    if probability >= 50:
        return "높음"
    if probability >= 20:
        return "보통"
    return "낮음"


def analyze_voice_file(audio_path: str) -> dict:
    """
    음성 파일을 분석해 chat_service의 위험도 응답과 동일한 형식으로 반환한다.
    (프론트가 risk_level/probability/detected_patterns/reasons/recommendation
    형식을 그대로 재사용할 수 있도록)
    """
    detection = detect_ai_voice(audio_path)
    confidence = detection["confidence"]
    probability = round(confidence) if confidence is not None else 0

    if detection["is_inconclusive"]:
        return {
            "risk_level": "낮음",
            "probability": 0,
            "detected_patterns": [],
            "reasons": ["음성이 너무 짧거나 분석하기에 적절하지 않아 판정할 수 없습니다."],
            "recommendation": "더 길고 명확한 음성으로 다시 시도해주세요.",
        }

    return {
        "risk_level": _risk_level(probability),
        "probability": probability,
        "detected_patterns": ["AI 생성 음성(딥보이스) 의심"] if detection["is_ai"] else [],
        "reasons": [f"Reality Defender 판정: {detection['status']} (신뢰도 {probability}%)"],
        "recommendation": (
            "AI로 생성됐을 가능성이 있는 음성입니다. 전화를 끊고 상대방에게 "
            "알고 있는 다른 연락처로 직접 확인하세요."
            if detection["is_ai"]
            else "AI 생성 음성 징후는 발견되지 않았습니다."
        ),
    }