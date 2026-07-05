import cv2
import os

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


def extract_frames(video_path: str, interval: int = 30):
    """
    interval 프레임마다 이미지를 추출한다.
    interval=30이면 약 1초마다 저장(30fps 기준)
    """

    os.makedirs(FRAME_DIR, exist_ok=True)

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

            print(f"저장: {frame_path} / 성공 여부: {success}")

            saved_index += 1

        frame_index += 1

    cap.release()

    return frame_paths