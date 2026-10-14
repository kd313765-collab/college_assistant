import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# db url nahi diya to sqlite chalega
DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///" + os.path.join(BASE_DIR, "college.db")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY", "")
ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")

UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
SYLLABUS_DIR = os.path.join(BASE_DIR, "data", "syllabus")

TIMEZONE = "Asia/Kolkata"
PASS_PERCENT = 40   # itne % se kam = fail

# 1 rakho to agent ke error ka asli reason chat mein dikhega (development ke liye)
SHOW_ERRORS = os.getenv("SHOW_ERRORS", "1") == "1"
