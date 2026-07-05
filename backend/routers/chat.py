import asyncio
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
    extracted_messages: list[ChatMessage]


@router.post("/analyze", response_model=ChatResponse)
def analyze(request: ChatRequest):
    messages = [{"sender": m.sender, "content": m.content} for m in request.messages]

    if not messages:
        raise HTTPException(status_code=400, detail="채팅 내역이 비어 있습니다.")

    try:
        result = analyze_chat(messages)
    except InvalidAIResponseError:
        raise HTTPException(status_code=502, detail="AI 응답을 처리하지 못했습니다. 다시 시도해주세요.")

    return result


@router.post("/analyze-image", response_model=ImageAnalyzeResponse)
async def analyze_image(files: list[UploadFile] = File(...)):
    for file in files:
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="이미지 파일만 업로드할 수 있습니다.")

    image_payloads = [(await f.read(), f.content_type) for f in files]
    if not any(data for data, _ in image_payloads):
        raise HTTPException(status_code=400, detail="이미지가 비어 있습니다.")

    try:
        per_image_messages = await asyncio.gather(*[
            asyncio.to_thread(extract_messages_from_image, data, mime_type=mime_type)
            for data, mime_type in image_payloads
        ])
    except InvalidAIResponseError:
        raise HTTPException(status_code=502, detail="AI 응답을 처리하지 못했습니다. 다시 시도해주세요.")

    messages = [msg for chunk in per_image_messages for msg in chunk]

    if not messages:
        raise HTTPException(status_code=422, detail="이미지에서 채팅 내역을 찾을 수 없습니다.")

    try:
        result = analyze_chat(messages)
    except InvalidAIResponseError:
        raise HTTPException(status_code=502, detail="AI 응답을 처리하지 못했습니다. 다시 시도해주세요.")

    return {**result, "extracted_messages": messages}
