
import os
from pathlib import Path

from dotenv import load_dotenv


# Project paths
BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent

# Load environment variables from the project root
load_dotenv(PROJECT_ROOT / ".env")

# Application settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY was not found. "
        "Check the .env file in the project root."
    )

# Storage paths
DOCUMENTS_DIR = BACKEND_DIR / "documents"
CACHE_FILE = BACKEND_DIR / "documents_embedding.pkl"
SOURCES_METADATA_FILE = DOCUMENTS_DIR / "sources_metadata.json"

WIDGET_SETTINGS_FILE = BACKEND_DIR / "widget_settings.json"

# Public widget limits: (window in seconds, max requests) per visitor IP.
PUBLIC_RATE_LIMITS = [(60, 10), (86400, 100)]


ASSISTANT_SETTINGS_FILE = BACKEND_DIR / "assistant_settings.json"

# Upload settings
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_UPLOAD_EXTENSIONS = {".pdf"}


# Admin auth (single admin for now). Both must be set in .env to enable login.
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
AUTH_SECRET = os.getenv("AUTH_SECRET")
AUTH_TOKEN_TTL_SECONDS = 12 * 60 * 60

# Login brute-force limits per IP: (window in seconds, max attempts).
LOGIN_RATE_LIMITS = [(60, 5), (3600, 20)]

# Number of reverse proxies in front of the app (0 = none, local dev).
# Set TRUSTED_PROXY_HOPS=1 in production behind one proxy (Render, Railway, nginx).
# Never set it above 0 if clients can reach the app directly, or the
# X-Forwarded-For header can be spoofed.
TRUSTED_PROXY_HOPS = int(os.getenv("TRUSTED_PROXY_HOPS", "0"))


# Browser origins allowed to call the API (comma-separated in env).
# Defaults to local dev. In production set CORS_ORIGINS=https://your-frontend-domain
DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"


def parse_origins(raw):
    return [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]


CORS_ORIGINS = parse_origins(os.getenv("CORS_ORIGINS") or DEFAULT_CORS_ORIGINS)
