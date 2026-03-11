import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# PharmaIQ Configuration
DB_PATH = "db/pharmaiq.db"
CHROMA_PATH = "vector_store/chroma"

# Operational Thresholds
TEMP_THRESHOLD_UPPER = 8.0
TEMP_THRESHOLD_LOWER = 2.0
EXPIRY_WINDOW_DAYS = 30

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SHEETS_ID = "your-sheet-id-here"
