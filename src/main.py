
import os

from dotenv import load_dotenv

load_dotenv()

from src.app import create_app  # noqa: E402

app = create_app()

PORT = int(os.getenv("PORT", "5003"))

print(f"OCR API prête sur http://localhost:{PORT}")