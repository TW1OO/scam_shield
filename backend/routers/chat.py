"""보이스피싱 채팅 분석 라우터.

/chat/analyze       : 텍스트로 직접 입력된 대화 분석
/chat/analyze-image : 채팅 스크린샷 1장을 업로드해 대화 추출 후 분석
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from services.chat_service import analyze_chat, extract_messages_from_image, InvalidAIResponseError

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    sender: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


class ChatResponse(BaseModel):
    risk_level: str
    probability: int
    detected_patterns: list[str]
    reasons: list[str]
    recommendation: str


class ImageAnalyzeResponse(ChatResponse):
    # 프론트에서 "실제로 무엇을 분석했는지" 확인할 수 있도록
    # 이미지에서 추출된 원본 메시지도 함께 반환한다.
    extracted_messages: list[ChatMessage]


def _raise_ai_timeout() -> None:
    """AI 응답 실패를 라우터 전용 502 에러로 통일해서 던진다."""
    raise HTTPException(status_code=502, detail="AI 응답을 처리하지 못했습니다. 다시 시도해주세요.")


@router.post("/analyze", response_model=ChatResponse)
def analyze(request: ChatRequest):
    """사용자가 직접 입력/붙여넣은 채팅 내역을 분석한다."""
    messages = [{"sender": m.sender, "content": m.content} for m in request.messages]

    if not messages:
        raise HTTPException(status_code=400, detail="채팅 내역이 비어 있습니다.")

    try:
        result = analyze_chat(messages)
    except InvalidAIResponseError:
        _raise_ai_timeout()

    return result


@router.post("/analyze-image", response_model=ImageAnalyzeResponse)
async def analyze_image(file: UploadFile = File(...)):
    """채팅 스크린샷 1장을 업로드받아: 대화 추출 -> 위험도 분석 순으로 처리한다."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드할 수 있습니다.")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="이미지가 비어 있습니다.")

    try:
        messages = extract_messages_from_image(image_bytes, mime_type=file.content_type)
    except InvalidAIResponseError:
        _raise_ai_timeout()

    if not messages:
        raise HTTPException(status_code=422, detail="이미지에서 채팅 내역을 찾을 수 없습니다.")

    try:
        result = analyze_chat(messages)
    except InvalidAIResponseError:
        _raise_ai_timeout()

    return {**result, "extracted_messages": messages}
