import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ALLOWED_USERS = os.getenv("ALLOWED_USERS", "").split(",") if os.getenv("ALLOWED_USERS") else []

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Railway deployment configuration
PORT = int(os.getenv("PORT", 8080))

# Validate required environment variables
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is required")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is required")
if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL is required")
if not SUPABASE_KEY:
    raise ValueError("SUPABASE_KEY is required")

print("✅ Configuration loaded successfully")