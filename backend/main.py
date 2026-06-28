from fastapi import FastAPI

app = FastAPI() #사용할 서버 만들기

@app.get("/")
def root():
    return {"message": "Backend Running"}