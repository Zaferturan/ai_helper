import os
from datetime import timedelta

# Database
DATABASE_URL = "sqlite:///./ai_helper.db"

# JWT Settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Authentication System
LOGIN_TOKEN_TTL_MINUTES = 10  # 10 minutes
LOGIN_CODE_TTL_MINUTES = 10   # 10 minutes

# Rate Limiting
RATE_LIMIT_LOGIN_SECONDS = 60      # 1 minute between login attempts
RATE_LIMIT_DAILY_LOGINS = 10       # Max 10 login attempts per day per email
RATE_LIMIT_CODE_ATTEMPTS = 5       # Max 5 code verification attempts per token

# Email Settings
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "True").lower() == "true"

# Frontend URL
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://yardimci.niluferyzeka.tr")

# Backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000") 