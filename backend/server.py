from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/api/hello")
def read_root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=9000, log_level="info", reload=True)