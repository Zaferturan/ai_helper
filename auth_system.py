from datetime import datetime, timedelta, time
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer
import jwt
from jwt.exceptions import InvalidTokenError as JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from connection import get_db
from models import User, LoginAttempt, LoginToken
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import logging
from config import (
    settings,
    PRODUCTION_URL,
    RATE_LIMIT_LOGIN_SECONDS,
    RATE_LIMIT_DAILY_LOGINS,
    JWT_SECRET_KEY,
    ACCESS_TOKEN_EXPIRE_HOURS,
    LOGIN_TOKEN_EXPIRE_MINUTES,
    DEBUG_MODE,
)
import os
import secrets
import string
import hashlib

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if DEBUG_MODE:
    logging.getLogger().setLevel(logging.DEBUG)
    logger.setLevel(logging.DEBUG)

# Security settings — require configured secret in production
SECRET_KEY = JWT_SECRET_KEY or os.getenv("JWT_SECRET_KEY") or ""
if not SECRET_KEY or SECRET_KEY in ("your-secret-key-here", "change-me", "secret"):
    raise RuntimeError("JWT_SECRET_KEY must be set to a strong non-placeholder value")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(ACCESS_TOKEN_EXPIRE_HOURS) * 60

# Rate limiting settings
RATE_LIMIT_EMAIL_SECONDS = 60  # 60 seconds between email requests
RATE_LIMIT_DAILY_EMAILS = 10   # Max 10 emails per day
RATE_LIMIT_OTP_ATTEMPTS = 5    # Max 5 OTP attempts
RATE_LIMIT_LOCKOUT_MINUTES = 15  # 15 minutes lockout

# Magic link and OTP settings (≤15 min)
MAGIC_LINK_EXPIRE_MINUTES = int(LOGIN_TOKEN_EXPIRE_MINUTES or 15)
OTP_LENGTH = 6

# Email settings
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
# SMTP_PASSWORD'i temizle: tırnakları kaldır
_smtp_password_raw = os.getenv("SMTP_PASSWORD", "")
SMTP_PASSWORD = _smtp_password_raw.strip('"\'') if _smtp_password_raw else ""
# SENDER_EMAIL yoksa SMTP_USERNAME; ikisi de yoksa boş string (None SMTP hatalarını önler)
SENDER_EMAIL = os.getenv("SENDER_EMAIL") or SMTP_USERNAME or ""

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token bearer
security = HTTPBearer()

class AuthService:
    def __init__(self):
        self.rate_limit_cache: Dict[str, Any] = {}
    
    def generate_otp(self) -> str:
        """Generate 6-digit OTP"""
        return ''.join(secrets.choice(string.digits) for _ in range(OTP_LENGTH))
    
    def generate_magic_link(self, user_id: int) -> str:
        """Generate magic link with JWT token"""
        expire = datetime.utcnow() + timedelta(minutes=MAGIC_LINK_EXPIRE_MINUTES)
        to_encode = {"sub": str(user_id), "exp": expire, "type": "magic_link"}
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    def verify_email_domain(self, email: str) -> bool:
        """Verify email domain is @nilufer.bel.tr"""
        return email.lower().endswith("@nilufer.bel.tr")
    
    def check_rate_limit_login(self, ip_address: str, email: str) -> bool:
        """Check rate limit for login attempts (IP + email based)"""
        now = datetime.utcnow()
        cache_key = f"{ip_address}:{email}"
        
        if cache_key not in self.rate_limit_cache:
            self.rate_limit_cache[cache_key] = {
                "last_request": now,
                "daily_count": 1,
                "last_reset": now.date()
            }
            logger.debug(f"New login rate limit entry for {cache_key}")
            return True
        
        cache = self.rate_limit_cache[cache_key]
        
        # Reset daily count if it's a new day
        if now.date() > cache["last_reset"]:
            cache["daily_count"] = 0
            cache["last_reset"] = now.date()
            logger.debug(f"Daily count reset for {cache_key}")
        
        # Check 30-second limit
        if (now - cache["last_request"]).total_seconds() < RATE_LIMIT_LOGIN_SECONDS:
            logger.debug(f"30-second limit hit for {cache_key}")
            return False
        
        # Check daily limit
        if cache["daily_count"] >= RATE_LIMIT_DAILY_LOGINS:
            logger.debug(f"Daily limit hit for {cache_key}")
            return False
        
        # Update cache
        cache["last_request"] = now
        cache["daily_count"] += 1
        logger.debug(f"Login rate limit updated for {cache_key}: {cache['daily_count']}")
        
        return True
    
    def check_rate_limit_otp(self, email: str) -> bool:
        """Check rate limit for OTP attempts"""
        now = datetime.utcnow()
        
        if email not in self.rate_limit_cache:
            return True
        
        cache = self.rate_limit_cache[email]
        
        # Check if user is locked out
        if "lockout_until" in cache and now < cache["lockout_until"]:
            return False
        
        # Check OTP attempts
        if "otp_attempts" not in cache:
            cache["otp_attempts"] = 0
        
        if cache["otp_attempts"] >= RATE_LIMIT_OTP_ATTEMPTS:
            cache["lockout_until"] = now + timedelta(minutes=RATE_LIMIT_LOCKOUT_MINUTES)
            return False
        
        return True
    
    def increment_otp_attempts(self, email: str):
        """Increment OTP attempt counter"""
        if email not in self.rate_limit_cache:
            self.rate_limit_cache[email] = {}
        
        if "otp_attempts" not in self.rate_limit_cache[email]:
            self.rate_limit_cache[email]["otp_attempts"] = 0
        
        self.rate_limit_cache[email]["otp_attempts"] += 1
    
    def reset_otp_attempts(self, email: str):
        """Reset OTP attempt counter"""
        if email in self.rate_limit_cache:
            self.rate_limit_cache[email]["otp_attempts"] = 0
            if "lockout_until" in self.rate_limit_cache[email]:
                del self.rate_limit_cache[email]["lockout_until"]
    
    def clear_rate_limit_cache(self):
        """Clear all rate limiting cache (for testing/debugging)"""
        self.rate_limit_cache.clear()
        logger.debug("Rate limiting cache cleared")
    
    def get_rate_limit_status(self, email: str) -> dict:
        """Get current rate limit status for an email (for debugging)"""
        if email in self.rate_limit_cache:
            return self.rate_limit_cache[email].copy()
        return {"status": "no_cache_entry"}
    
    async def send_magic_link_email(self, email: str, magic_link: str, otp: str) -> bool:
        """Send magic link and OTP email"""
        try:
            logger.info("Sending login email to %s", email)
            
            msg = MIMEMultipart('alternative')
            msg['From'] = SENDER_EMAIL
            msg['To'] = email
            msg['Subject'] = "AI Helper - Giriş Bağlantısı"
            ttl_note = f"{MAGIC_LINK_EXPIRE_MINUTES} dakika"
            
            # HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>AI Helper Giriş</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c5aa0;">AI Helper - Giriş Bağlantısı</h2>
                    <p>Merhaba,</p>
                    <p>AI Helper sistemine giriş yapmak için aşağıdaki seçeneklerden birini kullanabilirsiniz:</p>
                    
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #2c5aa0; margin-top: 0;">Seçenek 1: Magic Link</h3>
                        <p>Aşağıdaki bağlantıya tıklayarak giriş yapın:</p>
                        <a href="{magic_link}" style="background: #2c5aa0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Giriş Yap</a>
                        <p style="font-size: 12px; color: #666;">Bu bağlantı {ttl_note} geçerlidir ve tek kullanımlıktır.</p>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #2c5aa0; margin-top: 0;">Seçenek 2: Tek Kullanımlık Kod</h3>
                        <p>Kod: <strong style="font-size: 18px; color: #2c5aa0;">{otp}</strong></p>
                        <p style="font-size: 12px; color: #666;">Bu kod {ttl_note} geçerlidir.</p>
                    </div>
                    
                    <p><strong>Not:</strong> Her iki seçenek de {ttl_note} geçerlidir.</p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    <p style="font-size: 12px; color: #666;">
                        Bu e-posta AI Helper sistemi tarafından otomatik olarak gönderilmiştir.<br>
                        Eğer bu e-postayı siz talep etmediyseniz, lütfen dikkate almayın.
                    </p>
                </div>
            </body>
            </html>
            """
            
            # Plain text content
            text_content = f"""
            AI Helper - Giriş Bağlantısı
            
            Merhaba,
            
            AI Helper sistemine giriş yapmak için aşağıdaki seçeneklerden birini kullanabilirsiniz:
            
            Seçenek 1: Magic Link
            {magic_link}
            Bu bağlantı {ttl_note} geçerlidir ve tek kullanımlıktır.
            
            Seçenek 2: Tek Kullanımlık Kod
            Kod: {otp}
            Bu kod {ttl_note} geçerlidir.
            
            Not: Her iki seçenek de {ttl_note} geçerlidir.
            
            ---
            Bu e-posta AI Helper sistemi tarafından otomatik olarak gönderilmiştir.
            Eğer bu e-postayı siz talep etmediyseniz, lütfen dikkate almayın.
            """
            
            msg.attach(MIMEText(html_content, 'html'))
            msg.attach(MIMEText(text_content, 'plain'))
            
            logger.debug("Email content prepared, attempting SMTP connection...")
            
            # SMTP connection
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            logger.debug(f"SMTP connection established to {SMTP_HOST}:{SMTP_PORT}")
            
            server.starttls()
            logger.debug("TLS started")
            
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            logger.debug("SMTP authentication successful")
            
            text = msg.as_string()
            server.sendmail(SENDER_EMAIL, email, text)
            logger.debug(f"Email sent successfully to {email}")
            
            server.quit()
            logger.debug("SMTP connection closed")
            
            logger.info(f"Magic link email sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {email}: {str(e)}")
            logger.debug(f"Full error details: {type(e).__name__}: {str(e)}")
            return False
    
    async def send_login_credentials_email(self, email: str, token: str, code: str, expires_at: datetime) -> bool:
        """Send login credentials email with token and code"""
        try:
            logger.info(f"Attempting to send login credentials email to: {email}")
            logger.info(f"SMTP settings - Host: {SMTP_HOST}, Port: {SMTP_PORT}, Username: {SMTP_USERNAME}")
            logger.info(f"SENDER_EMAIL configured: {bool(SENDER_EMAIL)}")
            
            if not all([SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, SENDER_EMAIL]):
                logger.error("SMTP configuration incomplete")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = SENDER_EMAIL
            msg['To'] = email
            msg['Subject'] = "Giriş bilgilerin hazır"
            
            # Calculate remaining minutes
            remaining_minutes = int((expires_at - datetime.utcnow()).total_seconds() / 60)
            
            # Create login URL - frontend'e token parametresi ile yönlendir
            login_url = f"{PRODUCTION_URL}/api/v1/magic-link?token={token}"
            
            # HTML version
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>AI Helper - Giriş Bilgileri</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #2c5aa0; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background: white; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 8px 8px; }}
                    .login-section {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2c5aa0; }}
                    .code {{ font-size: 24px; font-weight: bold; color: #2c5aa0; text-align: center; padding: 15px; background: white; border-radius: 6px; margin: 10px 0; }}
                    .button {{ background: #2c5aa0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; }}
                    .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
                    .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 15px; border-radius: 6px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🔐 AI Helper - Giriş Bilgileri</h1>
                    <p>Bursa Nilüfer Belediyesi AI Yardımcı Sistemi</p>
                </div>
                
                <div class="content">
                    <h2>Merhaba,</h2>
                    <p>Uygulamaya giriş yapmak için aşağıdaki seçeneklerden birini kullanabilirsiniz:</p>
                    
                    <div class="login-section">
                        <h3>🌐 Giriş Linki</h3>
                        <p>Aşağıdaki bağlantıya tıklayarak doğrudan giriş yapın:</p>
                        <a href="{login_url}" class="button">Giriş Yap</a>
                        <p style="font-size: 12px; color: #666; margin-top: 10px;">Bu bağlantı {remaining_minutes} dakika geçerlidir.</p>
                    </div>
                    
                    <div class="login-section">
                        <h3>🔢 Giriş Kodu</h3>
                        <p>Alternatif olarak aşağıdaki 6 haneli kodu kullanabilirsiniz:</p>
                        <div class="code">{code}</div>
                        <p style="font-size: 12px; color: #666; text-align: center;">Bu kod {remaining_minutes} dakika geçerlidir</p>
                    </div>
                    
                    <div class="warning">
                        <strong>⚠️ Güvenlik Uyarısı:</strong>
                        <ul style="margin: 10px 0; padding-left: 20px;">
                            <li>Bu bilgileri kimseyle paylaşmayın</li>
                            <li>{remaining_minutes} dakika sonra geçersiz olur</li>
                        </ul>
                    </div>
                    
                    <p>Herhangi bir sorun yaşarsanız, lütfen sistem yöneticisi ile iletişime geçin.</p>
                    
                    <p>Saygılarımızla,<br>
                    <strong>AI Helper Sistemi</strong></p>
                </div>
                
                <div class="footer">
                    <p>Bu e-posta otomatik olarak gönderilmiştir. Lütfen yanıtlamayın.</p>
                    <p>© 2024 Bursa Nilüfer Belediyesi. Tüm hakları saklıdır.</p>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            text_content = f"""
            AI Helper - Giriş Bilgileri
            =============================
            
            Merhaba,
            
            Uygulamaya giriş yapmak için aşağıdaki seçeneklerden birini kullanabilirsiniz:
            
            Seçenek 1: Giriş Linki
            {login_url}
            Bu bağlantı {remaining_minutes} dakika geçerlidir.
            
            Seçenek 2: Giriş Kodu
            Kod: {code}
            Bu kod {remaining_minutes} dakika geçerlidir.
            
            Güvenlik Uyarısı:
            - Bu bilgileri kimseyle paylaşmayın
            - {remaining_minutes} dakika sonra geçersiz olur
            
            Herhangi bir sorun yaşarsanız, lütfen sistem yöneticisi ile iletişime geçin.
            
            Saygılarımızla,
            AI Helper Sistemi
            
            ---
            Bu e-posta otomatik olarak gönderilmiştir. Lütfen yanıtlamayın.
            © 2024 Bursa Nilüfer Belediyesi. Tüm hakları saklıdır.
            """
            
            # Attach both versions
            msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # Send email
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
                logger.debug("SMTP connection closed")
            
            logger.info(f"Login credentials email sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending login credentials email: {str(e)}")
            return False
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token (short-lived; logout relies on TTL + is_active)."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=int(ACCESS_TOKEN_EXPIRE_HOURS))
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        # PyJWT returns str; jose sometimes returned bytes
        if isinstance(encoded_jwt, bytes):
            encoded_jwt = encoded_jwt.decode("utf-8")
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None
    
    def log_login_attempt(self, db: Session, email: str, ip_address: str, success: bool, method: str):
        """Log login attempt"""
        try:
            login_attempt = LoginAttempt(
                email=email,
                ip_address=ip_address,
                success=success,
                method=method,
                timestamp=datetime.utcnow()
            )
            db.add(login_attempt)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log login attempt: {str(e)}")
            db.rollback()

# Global auth service instance
auth_service = AuthService()

# Dependency functions
def get_current_user(token = Depends(security), db: Session = Depends(get_db)):
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        logger.debug(f"Token received: {token.credentials[:20]}...")
        
        # JWT token'ı doğrula
        payload = auth_service.verify_token(token.credentials)
        if payload is None:
            raise credentials_exception
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        logger.debug(f"User ID from token: {user_id}")
        
        # User ID'ye göre user bul
        try:
            user = db.query(User).filter(User.id == int(user_id)).first()
        except ValueError:
            logger.error(f"Invalid user ID format: {user_id}")
            raise credentials_exception
            
        logger.debug(f"User found by ID: {user.email if user else 'None'}")
        
        if user is None:
            logger.error(f"User with ID {user_id} not found in database")
            raise credentials_exception

        if not user.is_active:
            logger.warning("Inactive user attempted auth: %s", user.email)
            raise credentials_exception
        
        logger.debug(f"Authentication successful for user: {user.email}")
        return user
        
    except Exception as e:
        logger.error(f"Error in get_current_user: {str(e)}")
        raise credentials_exception

def get_client_ip(request: Request) -> str:
    """Get client IP address"""
    # Check for forwarded headers (Cloudflare)
    forwarded_for = request.headers.get("CF-Connecting-IP")
    if forwarded_for:
        return forwarded_for
    
    # Fallback to direct connection
    return request.client.host if request.client else "unknown"

def save_user_session_to_file(user_email, access_token, request_info, user_id=None):
    """Deprecated: disk session storage removed for security. No-op."""
    logger.warning("save_user_session_to_file called but disabled")
    return None 