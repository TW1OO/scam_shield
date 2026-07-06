import cv2
import os

from transformers import pipeline

DEEPFAKE_THRESHOLD = 0.7
SUSPICIOUS_THRESHOLD = 0.4
FRAME_INTERVAL = 10

classifier = pipeline(
    task="image-classification",
    model="prithivMLmods/Deep-Fake-Detector-v2-Model"
)

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

    result = classifier(image_path)

    for item in result:
        if item["label"] == "Deepfake":
            return item["score"]

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