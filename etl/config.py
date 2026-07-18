import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://trials_user:trials_pass@localhost:5433/clinical_trials",
)
API_BASE_URL = os.getenv("API_BASE_URL", "https://clinicaltrials.gov/api/v2")
PAGE_SIZE = int(os.getenv("PAGE_SIZE", "100"))
MAX_STUDIES = int(os.getenv("MAX_STUDIES", "5000"))
