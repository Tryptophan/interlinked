from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import lib 

app = FastAPI()

class TranslationRequest(BaseModel):
    from_lang: str
    to_lang: str
    text: str

@app.get("/api/hello")
def read_root():
    return {"message": "Hello World"}

@app.post("/api/translate")
def translate(request: TranslationRequest):
    try:
        translated_text = lib.translate_text(request.from_lang, request.to_lang, request.text)
        return {"translated_text": translated_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=9000, log_level="info", reload=True)