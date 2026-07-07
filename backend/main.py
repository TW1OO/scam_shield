from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import chat, call, deepvoice, video
from database import engine
from models import Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Scam Shield API")

# 프론트(별도 포트/도메인)에서 직접 fetch 할 수 있도록 허용.
# 데모 단계라 전체 허용, 운영 단계에서는 실제 프론트 도메인으로 좁혀야 함.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(call.router)
app.include_router(deepvoice.router)
app.include_router(video.router)

@app.get("/")
def root():
    return {"message": "Backend Running"}
