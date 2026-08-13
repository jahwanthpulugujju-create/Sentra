"""Environment / configuration loading for Sentra Authority Engine."""
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "").strip()
SECRET_KEY: str = os.getenv("SECRET_KEY", "sentra-authority-master-signing-key-hackathon-2026").strip()
POLICY_VERSION: str = os.getenv("POLICY_VERSION", "v1.0.0-sentra-kernel").strip()
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
LLM_CONFIGURED: bool = bool(GEMINI_API_KEY)
