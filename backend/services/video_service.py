import cv2
import os

from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

DEEPFAKE_MODEL = "prithivMLmods/Deep-Fake-Detector-v2-Model"
DEEPFAKE_THRESHOLD = 0.7
SUSPICIOUS_THRESHOLD = 0.4
FRAME_INTERVAL = 10

# 로컬에서 torch/transformers로 모델을 직접 돌리는 대신, HuggingFace의
# 무료 Inference API로 호출한다 (설치 용량과 모델 다운로드 시간을 줄이기 위함).
client = InferenceClient(api_key=os.getenv("HUGGINGFACE_API_KEY"))

FRAME_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "frames"
)


def save_image(frame_path, frame):
    """
    한글 경로에서도 이미지 저장 가능하도록 저장
    """
    ext = os.path.splitext(frame_path)[1]

    success, encoded = cv2.imencode(ext, frame)

    if success:
        with open(frame_path, "wb") as f:
            encoded.tofile(f)

    return success


def extract_frames(video_path: str, interval: int = FRAME_INTERVAL):
    """
    interval 프레임마다 이미지를 추출한다.
    interval=30이면 약 1초마다 저장(30fps 기준)
    """

    os.makedirs(FRAME_DIR, exist_ok=True)

    # 기존 프레임 삭제
    for file in os.listdir(FRAME_DIR):
        if file.endswith(".jpg"):
            os.remove(os.path.join(FRAME_DIR, file))

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise Exception(f"영상을 열 수 없습니다: {video_path}")

    frame_paths = []

    frame_index = 0
    saved_index = 0

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        if frame_index % interval == 0:

            frame_path = os.path.join(
                FRAME_DIR,
                f"frame_{saved_index}.jpg"
            )

            success = save_image(frame_path, frame)

            if success:
                frame_paths.append(frame_path)


            saved_index += 1

        frame_index += 1

    cap.release()

    return frame_paths

def detect_deepfake_image(image_path: str):
    """
    이미지 한 장을 분석하여 Deepfake 점수를 반환
    """

    result = client.image_classification(image_path, model=DEEPFAKE_MODEL)

    for item in result:
        if item.label == "Deepfake":
            return item.score

    return 0.0

def detect_ai_video(video_path: str):

    frames = extract_frames(video_path)

    if len(frames) == 0:
        raise Exception("프레임을 추출하지 못했습니다.")

    scores = []

    for frame in frames:
        score = detect_deepfake_image(frame)
        scores.append(score)

    average_score = sum(scores) / len(scores)

    if average_score >= DEEPFAKE_THRESHOLD:
        status = "DEEPFAKE"
    elif average_score >= SUSPICIOUS_THRESHOLD:
        status = "SUSPICIOUS"
    else:
        status = "REAL"

    return {
        "status": status,
        "score": round(average_score, 4),
        "frames": len(frames)
    }
    """
    반환 예시
    {
    "status": "DEEPFAKE",
    "score": 0.6173,
    "frames": 12
    }
    """


def _risk_level(probability: int) -> str:
    if probability >= 70:
        return "매우 높음"
    if probability >= 40:
        return "높음"
    if probability >= 20:
        return "보통"
    return "낮음"


def analyze_video_file(video_path: str) -> dict:
    """
    영상 파일을 분석해 chat_service의 위험도 응답과 동일한 형식으로 반환한다.
    (프론트가 risk_level/probability/detected_patterns/reasons/recommendation
    형식을 그대로 재사용할 수 있도록)
    """
    detection = detect_ai_video(video_path)
    probability = round(detection["score"] * 100)
    is_deepfake = detection["status"] != "REAL"

    return {
        "risk_level": _risk_level(probability),
        "probability": probability,
        "detected_patterns": ["AI 생성 영상(딥페이크) 의심"] if is_deepfake else [],
        "reasons": [
            f"프레임 {detection['frames']}개 분석 결과: {detection['status']} "
            f"(딥페이크 평균 점수 {probability}%)"
        ],
        "recommendation": (
            "AI로 조작됐을 가능성이 있는 영상입니다. 화면 속 인물의 신원을 "
            "다른 방법으로 반드시 재확인하세요."
            if is_deepfake
            else "AI 생성 영상 징후는 발견되지 않았습니다."
        ),
    }
