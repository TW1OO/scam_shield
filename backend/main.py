from fastapi import FastAPI
from routers import chat

app = FastAPI(title="Scam Shield API")

app.include_router(chat.router)

@app.get("/")
def root():
    return {"message": "Backend Running"}
