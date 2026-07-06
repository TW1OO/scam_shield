"""보이스피싱 탐지 채팅 서비스.

두 가지 분석 경로를 제공한다:
1. analyze_chat            : 텍스트 채팅 내역을 받아 위험도를 분석
2. extract_messages_from_image : 채팅 스크린샷에서 대화 내용을 추출 (분석은 analyze_chat에 위임)

모든 LLM 호출은 NVIDIA의 OpenAI 호환 API(integrate.api.nvidia.com)를 통해
meta/llama 계열 모델로 이루어진다.
"""

from openai import OpenAI, APIConnectionError
from dotenv import load_dotenv
from io import BytesIO
from PIL import Image
import os
import json
import base64

load_dotenv()

# max_retries=0: openai SDK가 내부적으로 자체 재시도(기본 2회)를 하지 않도록 끈다.
# SDK 자체 재시도 + 아래 _create_completion의 수동 재시도가 중첩되면
# 타임아웃이 최대 3배까지 누적되어 Vercel 함수 제한(300초)까지 응답 없이
# 멈추는 문제가 있었다. 재시도는 _create_completion 한 곳에서만 관리한다.
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY"),
    max_retries=0,
)

# ── 모델 설정 ─────────────────────────────────────────────
# meta/llama-3.3-70b-instruct가 NVIDIA 쪽에서 응답 없음(장애) 상태라
# MoE 구조라 훨씬 빠르고(테스트 기준 2~5초) 정확도도 검증된
# Llama 4 Maverick으로 교체했다.
TEXT_MODEL = "meta/llama-4-maverick-17b-128e-instruct"  # 순수 텍스트 위험도 분석 전용
VISION_MODEL = "meta/llama-3.2-90b-vision-instruct"     # 이미지 속 대화 추출 전용

# 호출 1회당 대기 시간과 총 시도 횟수. 최악의 경우 REQUEST_TIMEOUT * MAX_ATTEMPTS
# 만큼만 기다리고 끝난다 (기존에는 SDK 자체 재시도까지 겹쳐 훨씬 더 길게,
# 예측 불가능하게 걸렸음). NVIDIA API는 가끔 일시적으로 응답이 느려질 때가
# 있어서 재시도 횟수를 넉넉히 둬야 실사용 성공률이 떨어지지 않는다.
REQUEST_TIMEOUT = 45.0
MAX_ATTEMPTS = 3

# 응답이 비정상적으로 길어져 지연되는 것을 막기 위한 출력 토큰 상한.
# 이 서비스의 응답은 항상 짧은 JSON이므로 넉넉히 잡아도 정상 응답엔 영향 없다.
MAX_RESPONSE_TOKENS = 2048


class InvalidAIResponseError(Exception):
    """LLM 응답이 비정상(타임아웃, JSON 파싱 실패 등)일 때 발생시키는 예외.

    라우터 계층에서 이 예외를 잡아 502로 변환한다.
    """


def _create_completion(**kwargs):
    """LLM 호출 공통 래퍼. 타임아웃/연결 오류 시 최대 MAX_ATTEMPTS번까지 재시도한다.

    모든 시도가 실패하면 InvalidAIResponseError로 변환해서 호출자가
    항상 하나의 예외 타입만 신경 쓰면 되게 한다.
    """
    kwargs.setdefault("timeout", REQUEST_TIMEOUT)
    kwargs.setdefault("max_tokens", MAX_RESPONSE_TOKENS)

    last_error: APIConnectionError | None = None
    for _ in range(MAX_ATTEMPTS):
        try:
            return client.chat.completions.create(**kwargs)
        except APIConnectionError as e:
            last_error = e

    raise InvalidAIResponseError("AI 응답 시간이 초과되었습니다. 다시 시도해주세요.") from last_error


def _strip_json_fence(raw: str) -> str:
    """```json ... ``` 코드 펜스가 섞여 와도 순수 JSON 문자열만 남긴다."""
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return raw


# ══════════════════════════════════════════════════════════
# 1) 텍스트 기반 보이스피싱 위험도 분석
# ══════════════════════════════════════════════════════════

SYSTEM_PROMPT = """당신은 보이스피싱 탐지 전문 AI입니다.
사용자가 채팅 내역을 제공하면, 대화 전체의 문맥을 분석하여 보이스피싱 가능성을 판단하세요.

다음 패턴들을 중점적으로 분석하세요:
- 기관 사칭: 검찰, 경찰, 금융감독원, 국세청, 은행 직원 등을 사칭
- 급박감 조성: "지금 당장", "오늘 안에", "빨리 하지 않으면 큰일" 등의 압박
- 금전/계좌 요구: 송금, 계좌번호 요청, 현금 인출 요구
- 개인정보 요구: 주민등록번호, 계좌 비밀번호, 카드번호 등
- 비밀 유지 요청: 가족이나 주변인에게 말하지 말라는 요구
- 대출 빙자: 저금리 대출, 정부 지원금 등을 미끼로 사용
- 가족 사칭: 납치, 사고를 빙자한 가족 사칭

위험도 판단 시 반드시 지켜야 할 규칙:
- 위 패턴 중 단 하나만 발견됐다고 곧바로 "높음"이나 "매우 높음"으로 판단하지 마세요. 실제 보이스피싱은 보통 여러 패턴이 동시에 나타납니다 (예: 기관 사칭 + 급박감 + 계좌 요구).
- 계좌·금전 언급이 있어도 동아리, 학교 행사, 모임 회비·참가비 정산, 더치페이, 중고거래처럼 또래·지인 간의 자연스러운 일상 대화 맥락이면 위험도를 낮게 판단하세요.
- 참여자들이 서로 이름을 편하게 부르고 사적인 농담을 주고받는 등 지인 관계로 보이면, 낯선 사람의 일방적 요구가 아니므로 위험도를 낮추세요.
- "높음"/"매우 높음"은 계좌·금전 요구와 함께 기관 사칭, 급박감 조성, 비밀 유지 요청 등 다른 패턴이 최소 하나 더 동반될 때만 사용하세요.
- 단일 패턴만 있고 나머지 맥락이 일상적 대화면 "낮음" 또는 "보통"으로, probability도 30 이하로 매기세요.

반드시 아래 JSON 형식으로만 답변하세요. JSON 외 다른 텍스트는 절대 포함하지 마세요:
{
  "risk_level": "낮음 | 보통 | 높음 | 매우 높음",
  "probability": 0~100 사이의 정수,
  "detected_patterns": ["탐지된 패턴 목록"],
  "reasons": ["판단 근거 목록"],
  "recommendation": "사용자에게 전달할 행동 지침"
}"""


def analyze_chat(messages: list[dict]) -> dict:
    """채팅 메시지 목록(sender/content)을 받아 보이스피싱 위험도를 반환한다.

    입력은 텍스트 직접 입력, 이미지 추출 결과 어느 쪽에서 와도 동일한
    형식(list[{"sender", "content"}])이면 그대로 사용할 수 있다.
    """
    conversation = "\n".join(
        f"[{msg['sender']}]: {msg['content']}" for msg in messages
    )

    response = _create_completion(
        model=TEXT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"다음 채팅 내역을 분석해주세요:\n\n{conversation}"},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content.strip()
    try:
        return json.loads(_strip_json_fence(raw))
    except json.JSONDecodeError as e:
        raise InvalidAIResponseError(f"분석 응답이 올바른 JSON이 아닙니다: {e}") from e


# ══════════════════════════════════════════════════════════
# 2) 이미지(채팅 스크린샷)에서 대화 내용 추출
# ══════════════════════════════════════════════════════════

OCR_SYSTEM_PROMPT = """당신은 메신저 대화 스크린샷을 읽어 대화 내용을 정리하는 도우미입니다.
이미지 속 말풍선들을 위에서 아래 순서대로 읽고, 각 메시지의 발신자와 내용을 추출하세요.

발신자 판별 규칙:
- 말풍선 위나 옆, 즉 채팅 UI 자체에 프로필 사진과 이름이 표시되어 있으면, 그 이름을 발신자로 그대로 사용하세요.
- 같은 사람이 연속으로 여러 메시지를 보내 이름이 매 말풍선마다 반복 표시되지 않으면, 새 이름이 나오기 전까지는 직전 발신자를 유지하세요.
- 이름이나 프로필 없이 화면 오른쪽에 단독으로 표시되는 말풍선만 "나"로 표시하세요.
- 공유된 사진, 카드, 스티커 "안에" 적힌 문구는 발신자 이름이 아닙니다. 발신자는 반드시 채팅 UI가 실제로 표시하는 이름표에서만 가져오세요.

내용 작성 규칙:
- 텍스트 메시지는 말풍선 안의 글자를 그대로 옮기세요.
- 사진, 스티커, 이모티콘, 카드 등 텍스트가 아닌 첨부물은 내용을 "[사진]"으로 표시하세요. 첨부물 안의 문구는 옮기지 말고 항상 "[사진]"으로만 표시하세요.
- 리액션 이모지 개수(예: 😍 8, ❤ 2), 시간 표시(예: 오후 5:30), 읽음 수 숫자는 메시지가 아니므로 무시하고 절대 별도 항목으로 만들지 마세요.
- sender와 content는 항상 비어 있지 않은 문자열이어야 합니다. 발신자를 알 수 없으면 그 말풍선은 결과에서 제외하세요.

반드시 아래 JSON 형식으로만 답변하세요. JSON 외 다른 텍스트는 절대 포함하지 마세요:
{
  "messages": [
    {"sender": "발신자", "content": "메시지 내용"}
  ]
}"""

# 비전 모델은 세로로 매우 긴 스크린샷을 리사이즈하는 과정에서 글자가
# 뭉개져 못 읽는 경우가 많다. 아래 상수는 "얼마나 길면 자를지"와
# "얼마나 겹치게 잘라서 말풍선이 잘리지 않게 할지"를 결정한다.
CHUNK_ASPECT_THRESHOLD = 2.2   # height/width가 이 값을 넘으면 분할 대상
CHUNK_HEIGHT_RATIO = 1.8       # 조각 하나의 높이 = width * 이 값
CHUNK_OVERLAP_RATIO = 0.12     # 조각 간 겹치는 비율 (말풍선 잘림 방지)


def extract_messages_from_image(image_bytes: bytes, mime_type: str = "image/png") -> list[dict]:
    """스크린샷 원본 바이트를 받아 [{"sender", "content"}] 목록으로 변환한다.

    세로로 긴 이미지는 내부적으로 여러 조각으로 나눠 각각 추출한 뒤,
    조각 경계에서 겹쳐 중복 추출된 메시지를 제거하고 순서대로 합친다.
    """
    chunks = _split_tall_image(image_bytes)

    all_messages: list[dict] = []
    for chunk_bytes in chunks:
        # 분할된 조각은 항상 JPEG로 재인코딩되므로 mime_type도 그에 맞춘다.
        chunk_mime = "image/jpeg" if len(chunks) > 1 else mime_type
        chunk_messages = _extract_messages_from_chunk(chunk_bytes, chunk_mime)
        all_messages.extend(_drop_leading_duplicates(all_messages, chunk_messages))

    return all_messages


def _split_tall_image(image_bytes: bytes) -> list[bytes]:
    """세로 비율이 임계값을 넘는 이미지를 겹치는 여러 조각으로 자른다.

    짧은/정상 비율 이미지는 그대로 1개짜리 리스트로 반환한다.
    """
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    width, height = image.size

    if height / width <= CHUNK_ASPECT_THRESHOLD:
        return [image_bytes]

    chunk_height = int(width * CHUNK_HEIGHT_RATIO)
    overlap = int(chunk_height * CHUNK_OVERLAP_RATIO)
    step = chunk_height - overlap

    chunks = []
    top = 0
    while top < height:
        bottom = min(top + chunk_height, height)
        buf = BytesIO()
        image.crop((0, top, width, bottom)).save(buf, format="JPEG", quality=90)
        chunks.append(buf.getvalue())
        if bottom >= height:
            break
        top += step

    return chunks


def _drop_leading_duplicates(accumulated: list[dict], new_messages: list[dict]) -> list[dict]:
    """새 조각의 앞부분이 이전 조각과 겹쳐 재추출된 메시지를 잘라낸다.

    직전까지 누적된 메시지의 마지막 5개와 새 조각 앞부분을 비교해서,
    일치하는 선두 구간만 건너뛰고 나머지를 반환한다.
    """
    tail = accumulated[-5:]
    start = 0
    for i, msg in enumerate(new_messages):
        if msg in tail:
            start = i + 1
        else:
            break
    return new_messages[start:]


def _extract_messages_from_chunk(image_bytes: bytes, mime_type: str) -> list[dict]:
    """이미지 조각 하나를 비전 모델에 보내 [{"sender", "content"}] 목록을 얻는다."""
    encoded = base64.b64encode(image_bytes).decode("utf-8")

    response = _create_completion(
        model=VISION_MODEL,
        messages=[
            {"role": "system", "content": OCR_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "이 채팅 스크린샷의 대화 내용을 추출해주세요."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{encoded}"},
                    },
                ],
            },
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content.strip()
    try:
        parsed = json.loads(_strip_json_fence(raw))
    except json.JSONDecodeError as e:
        raise InvalidAIResponseError(f"이미지 추출 응답이 올바른 JSON이 아닙니다: {e}") from e

    return [
        {"sender": str(item["sender"]), "content": str(item["content"])}
        for item in parsed.get("messages", [])
    ]
