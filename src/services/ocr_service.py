
import base64
import json
import os

import ollama
from groq import Groq

from src.schemas.invoice_schema import OcrResult

PROVIDER = (os.getenv("OCR_PROVIDER") or "ollama").strip().lower()
MODEL = os.getenv("MODEL_NAME", "qwen2.5vl:7b")

_groq_client: Groq | None = None

EXTRACTION_PROMPT = """You are an OCR + document-parsing engine for invoices and receipts.

You receive one or more page images from a single upload, numbered in order starting at 1.

Tasks:
1. Read every page.
2. Group pages belonging to the same invoice (same invoice number, vendor, continuing line items).
3. Return ONLY valid JSON with this exact shape:

{
  "invoices": [
    {
      "pages": [1, 2],
      "document_type": "invoice" | "receipt" | "unknown",
      "vendor": { "name": null, "address": null, "tax_number": null },
      "client": { "name": null, "address": null, "email": null, "tax_number": null },
      "number": null,
      "issued_at": null,
      "due_at": null,
      "currency": null,
      "line_items": [
        { "description": "", "quantity": 0, "unit_price": 0, "tax_rate": null, "total": 0 }
      ],
      "sub_total": null,
      "tax_total": null,
      "grand_total": null,
      "raw_text": ""
    }
  ]
}

Rules:
- Never invent values not visible; use null.
- All numeric fields must be JSON numbers without currency symbols,
  spaces or percentage signs.
- Return tax_rate as a decimal: 20% must be returned as 0.20.
- Example: "4 300,00 MAD" must be returned as 4300.00.
- No commentary outside JSON."""


class OcrError(Exception):
    """Erreur métier OCR (entrée invalide, config manquante, etc.)."""


def _get_groq_client() -> Groq:
    global _groq_client
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        raise OcrError("GROQ_API_KEY manquante ou non configurée dans .env")
    if _groq_client is None:
        _groq_client = Groq(api_key=api_key)
    return _groq_client


def _to_data_url(content: bytes, mimetype: str | None) -> str:
    mime = mimetype or "image/png"
    encoded = base64.b64encode(content).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def _parse_with_groq(files: list[tuple[bytes, str | None, str]]) -> dict:
    client = _get_groq_client()

    content: list[dict] = [{"type": "text", "text": EXTRACTION_PROMPT}]
    for index, (data, mimetype, _name) in enumerate(files, start=1):
        content.append({"type": "text", "text": f"Page {index}:"})
        content.append({"type": "image_url", "image_url": {"url": _to_data_url(data, mimetype)}})

    completion = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": content}],
    )
    raw = completion.choices[0].message.content or "{}"
    return json.loads(raw)

_ollama_client: ollama.Client | None = None


def _get_ollama_client() -> ollama.Client:
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = ollama.Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
    return _ollama_client

def _parse_with_ollama(files: list[tuple[bytes, str | None, str]]) -> dict:
    images = [data for data, _mimetype, _name in files]
    client = _get_ollama_client()

    response = client.chat(
        model=MODEL,
        messages=[{"role": "user", "content": EXTRACTION_PROMPT, "images": images}],
        format="json",
    )
    raw = response["message"]["content"]
    return json.loads(raw)


async def parse_images(files: list[tuple[bytes, str | None, str]]) -> OcrResult:
    """files: liste de tuples (contenu_bytes, mimetype, nom_fichier)."""
    if not files:
        raise OcrError("Au moins une image est requise.")

    try:
        if PROVIDER == "groq":
            parsed = _parse_with_groq(files)
        elif PROVIDER == "ollama":
            parsed = _parse_with_ollama(files)
        else:
            raise OcrError(f"OCR_PROVIDER '{PROVIDER}' non supporté (attendu: groq | ollama)")
    except json.JSONDecodeError:
        parsed = {"invoices": [{"pages": list(range(1, len(files) + 1)), "raw_text": ""}]}

    return OcrResult.model_validate(parsed)