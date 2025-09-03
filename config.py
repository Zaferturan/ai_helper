import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Production URL configuration
PRODUCTION_URL = os.getenv("PRODUCTION_URL", "https://yardimci.niluferyapayzeka.tr")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8500")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Database configuration
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "ai_helper")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")

# Ollama configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_API_URL = os.getenv("GEMINI_API_URL", "https://generativelanguage.googleapis.com/v1beta/models")

# Authentication configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 15  # 15 hours (until 18:00)

# SMTP configuration for login emails
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")

# Login token system configuration
LOGIN_TOKEN_TTL_MIN = int(os.getenv("LOGIN_TOKEN_TTL_MIN", "10"))  # 10 minutes
RESEND_COOLDOWN_SEC = int(os.getenv("RESEND_COOLDOWN_SEC", "30"))  # 30 seconds
RATE_LIMIT_LOGIN_PER_HOUR = int(os.getenv("RATE_LIMIT_LOGIN_PER_HOUR", "5"))  # 5 per hour
RATE_LIMIT_CODE_ATTEMPTS = int(os.getenv("RATE_LIMIT_CODE_ATTEMPTS", "5"))  # 5 attempts

# Rate limiting configuration
RATE_LIMIT_LOGIN_SECONDS = 30  # 30 seconds between login requests
RATE_LIMIT_DAILY_LOGINS = 20   # Max 20 login attempts per day per IP+email
RATE_LIMIT_LOCKOUT_MINUTES = 10  # 10 minutes lockout

# Login token settings
LOGIN_TOKEN_EXPIRE_MINUTES = 10  # 10 minutes
CODE_LENGTH = 6

# Logging configuration
LOG_RETENTION_DAYS = int(os.getenv("LOG_RETENTION_DAYS", "30"))

# Debug configuration
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_TO_FILE = os.getenv("LOG_TO_FILE", "false").lower() == "true"
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "logs/app.log")

# Database URL for SQLAlchemy
# Use environment variable or default to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ai_helper.db")

# Settings class for easy access
class Settings:
    def __init__(self):
        self.database_url = DATABASE_URL
        self.jwt_secret_key = JWT_SECRET_KEY
        self.jwt_algorithm = JWT_ALGORITHM
        self.access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
        self.smtp_host = SMTP_HOST
        self.smtp_port = SMTP_PORT
        self.smtp_username = SMTP_USERNAME
        self.smtp_password = SMTP_PASSWORD
        self.sender_email = SENDER_EMAIL
        self.login_token_ttl_min = LOGIN_TOKEN_TTL_MIN
        self.resend_cooldown_sec = RESEND_COOLDOWN_SEC
        self.rate_limit_login_per_hour = RATE_LIMIT_LOGIN_PER_HOUR
        self.rate_limit_code_attempts = RATE_LIMIT_CODE_ATTEMPTS
        self.rate_limit_login_seconds = RATE_LIMIT_LOGIN_SECONDS
        self.rate_limit_daily_logins = RATE_LIMIT_DAILY_LOGINS
        self.rate_limit_lockout_minutes = RATE_LIMIT_LOCKOUT_MINUTES
        self.login_token_expire_minutes = LOGIN_TOKEN_EXPIRE_MINUTES
        self.code_length = CODE_LENGTH
        self.log_retention_days = LOG_RETENTION_DAYS

# Global settings instance
settings = Settings() 