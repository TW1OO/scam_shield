from fastapi import FastAPI
from routers import chat, call
from database import engine
from models import Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Scam Shield API")

app.include_router(chat.router)
app.include_router(call.router)

@app.get("/")
def root():
    return {"message": "Backend Running"}
