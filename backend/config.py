"""Environment / configuration loading. See Docs/BUILD_PLAN.md §10."""
import os

from dotenv import load_dotenv

# Load backend/.env (no-op if the file is absent).
load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "").strip()
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()

# True when a Gemini key is present; drives the /health badge and whether the
# intent-match check runs the real model vs the keyword fallback (M3).
LLM_CONFIGURED: bool = bool(GEMINI_API_KEY)
