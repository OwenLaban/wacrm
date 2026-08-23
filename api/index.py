# Entrypoint serverless Vercel: expose app FastAPI sebagai ASGI function
import os
import sys

# Tambahkan folder backend ke path supaya package `app` bisa di-import
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_BASE, "backend"))

from app.main import app  # noqa: E402,F401
