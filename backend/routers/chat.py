from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.chat_service import analyze_chat

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


@router.post("/analyze", response_model=ChatResponse)
def analyze(request: ChatRequest):
    messages = [{"sender": m.sender, "content": m.content} for m in request.messages]

    if not messages:
        raise HTTPException(status_code=400, detail="채팅 내역이 비어 있습니다.")

    result = analyze_chat(messages)
    return result
