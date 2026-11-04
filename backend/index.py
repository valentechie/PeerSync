# Entrada de Vercel: `@vercel/python` carga la variable `app` de este archivo.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.main import app  # noqa: E402, F401
