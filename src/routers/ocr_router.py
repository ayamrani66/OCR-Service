

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.datastructures import UploadFile

from src.services.ocr_service import OcrError, parse_images

MAX_FILE_SIZE = 15 * 1024 * 1024
MAX_FILES = 50

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


async def _read_files(request: Request) -> list[tuple[bytes, str | None, str]]:
    form = await request.form()
    uploads: list[UploadFile] = [
        v for v in form.getlist("images") if isinstance(v, UploadFile)
    ] + [v for v in form.getlist("image") if isinstance(v, UploadFile)]

    files: list[tuple[bytes, str | None, str]] = []
    for upload in uploads[:MAX_FILES]:
        data = await upload.read()
        if len(data) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File '{upload.filename}' exceeds 15MB limit.")
        files.append((data, upload.content_type, upload.filename or "unknown"))

    return files


@router.post("/ocr")
async def ocr(request: Request) -> JSONResponse:
    files = await _read_files(request)

    if not files:
        return JSONResponse(
            status_code=400,
            content={"error": "Missing image file(s). Send multipart field 'image' and/or 'images'."},
        )

    try:
        result = await parse_images(files)
        return JSONResponse(content={"data": result.model_dump()})
    except OcrError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(status_code=500, content={"error": str(exc) or "OCR failed"})