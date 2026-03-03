import os
from fastapi import FastAPI

app = FastAPI(title="Test Azure Oryx Build")


@app.get("/")
def root():
    return {"status": "ok", "env": os.getenv("ENV", "unknown")}


@app.get("/check-opencv")
def check_opencv():
    try:
        import cv2
        return {"opencv": "ok", "version": cv2.__version__, "package": "opencv-python-headless (expected)"}
    except ImportError as e:
        return {"opencv": "error", "message": str(e)}


@app.get("/check-docling")
def check_docling():
    try:
        from docling.document_converter import DocumentConverter
        return {"docling": "ok"}
    except ImportError as e:
        return {"docling": "error", "message": str(e)}
