# app.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from engine.interpreter import AIQLInterpreter
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/run-pipeline")
async def run_pipeline(request: Request):
    try:
        ast = await request.json()
        print("Received AST:", ast)  # Debug log
        interpreter = AIQLInterpreter(ast)
        result = interpreter.run()
        print("Interpreter result:", result)  # Debug log
        return JSONResponse(content={"result": result})
    except Exception as e:
        print("Error in run_pipeline:", e)
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/api/ping")
async def ping():
    return {"ping": "pong"}

# Serve React production build (make sure to build frontend first)
frontend_build_dir = os.path.join("frontend", "dist")  # or "build" if CRA

app.mount("/", StaticFiles(directory=frontend_build_dir, html=True), name="frontend")
