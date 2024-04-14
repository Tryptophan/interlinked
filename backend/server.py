from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import lib

app = FastAPI()

# Add CORS middleware to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


class TranslationRequest(BaseModel):
    from_lang: str
    to_lang: str
    text: str


@app.get("/api/hello")
def read_root():
    return {"message": "Hello World"}


@app.post("/api/translate")
async def translate(request: TranslationRequest):
    try:
        translated_text = await lib.translate_text(request.from_lang, request.to_lang, request.text)
        return {"translated_text": translated_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/translate-emphasize")
async def translate(request: TranslationRequest):
    try:
        translated_text = await lib.translate_text(request.from_lang, request.to_lang, request.text)
        add_emphasis = await lib.add_emphasis(request.to_lang, translated_text)
        return {"translated_text": translated_text, "add_emphasis": add_emphasis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/translate-imagegen")
async def translate(request: TranslationRequest):
    try:
        if request.from_lang != "English":
            translated_text = await lib.translate_text(request.from_lang, "English", request.text)
        else:
            translated_text = request.text

        print("fishing for images")
        image_gen_result = await lib.generate_images(translated_text)
        return {"translated_text": translated_text,
                "image_gen_result": image_gen_result
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1",
                port=9000, log_level="info", reload=True)
