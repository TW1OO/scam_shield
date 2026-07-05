from fastapi import FastAPI
from routers import chat

app = FastAPI(title="Scam Shield API - Chat")

app.include_router(chat.router, prefix="/api")


@app.get("/")
def root():
    return {"message": "Backend Running"}
