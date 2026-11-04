
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

# Storage paths. In production set DATA_DIR to the mounted volume path
# (for example /data) so documents, cache and settings survive restarts.
DATA_DIR = Path(os.getenv("DATA_DIR") or BACKEND_DIR)
DOCUMENTS_DIR = DATA_DIR / "documents"
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

CACHE_FILE = DATA_DIR / "documents_embedding.pkl"
SOURCES_METADATA_FILE = DOCUMENTS_DIR / "sources_metadata.json"
WIDGET_SETTINGS_FILE = DATA_DIR / "widget_settings.json"
ASSISTANT_SETTINGS_FILE = DATA_DIR / "assistant_settings.json"

# Public widget limits: (window in seconds, max requests) per visitor IP.
PUBLIC_RATE_LIMITS = [(60, 10), (86400, 100)]

# Upload settings
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_UPLOAD_EXTENSIONS = {".pdf"}



# Free plan limits (per workspace). Kept as constants: PLANS["free"] uses them.
FREE_MAX_DOCUMENTS = 5
FREE_MAX_QUESTIONS_PER_MONTH = 200

# Limits per plan. A workspace's plan is stored on its document.
# Missing or unknown plan = DEFAULT_PLAN.
DEFAULT_PLAN = "free"
PLANS = {
    "free": {
        "name": "Free",
        "max_documents": FREE_MAX_DOCUMENTS,
        "max_questions_per_month": FREE_MAX_QUESTIONS_PER_MONTH,
    },
    "pro": {
        "name": "Pro",
        "max_documents": 50,
        "max_questions_per_month": 5000,
    },
}


# Login tokens are signed with AUTH_SECRET (without it, login and signup return 503).
AUTH_SECRET = os.getenv("AUTH_SECRET")
AUTH_TOKEN_TTL_SECONDS = 12 * 60 * 60

# Login brute-force limits per IP: (window in seconds, max attempts).
LOGIN_RATE_LIMITS = [(60, 5), (3600, 20)]

# Password reset. Forgot-password sends an email, so it is limited harder.
FORGOT_PASSWORD_RATE_LIMITS = [(60, 3), (3600, 10)]
PASSWORD_RESET_TTL_SECONDS = 60 * 60

# Email (Resend). Without RESEND_API_KEY the reset link is printed to the
# server console instead of emailed (local dev).
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
MAIL_FROM = os.getenv("MAIL_FROM") or "Knowvia <onboarding@resend.dev>"

# Base URL used in emailed links.
FRONTEND_URL = (os.getenv("FRONTEND_URL") or "http://localhost:5173").rstrip("/")

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

# MongoDB (Atlas). Both are read from .env / host env vars.
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB") or "knowvia"



# How many workspaces keep their embeddings in memory at once. The least
# recently used one is dropped and reloaded from the database on next use.
MAX_LOADED_WORKSPACES = max(1, int(os.getenv("MAX_LOADED_WORKSPACES", "5")))