

from fastapi import FastAPI

from src.routers.ocr_router import router as ocr_router


def create_app() -> FastAPI:
    app = FastAPI(title="Invocto OCR API", version="1.0.0")

    @app.get("/")
    async def root() -> dict:
        return {"name": "Invocto OCR API", "status": "ok"}

    app.include_router(ocr_router)

    return app