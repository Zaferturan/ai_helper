import hashlib
import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import jwt

from models import User, LoginAttempt, LoginToken
from config import (
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,
    LOGIN_TOKEN_TTL_MINUTES, LOGIN_CODE_TTL_MINUTES,
    RATE_LIMIT_LOGIN_SECONDS, RATE_LIMIT_DAILY_LOGINS, RATE_LIMIT_CODE_ATTEMPTS,
    SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_USE_TLS,
    FRONTEND_URL
)

class AuthService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, email: str, name: Optional[str] = None, role: str = "user") -> User:
        """Create a new user"""
        user = User(email=email, name=name, role=role)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def create_access_token(self, user: User) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "sub": str(user.id),
            "email": user.email,
            "exp": expire
        }
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    def verify_access_token(self, token: str) -> Optional[dict]:
        """Verify JWT access token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.PyJWTError:
            return None
    
    def get_current_user(self, token: str) -> Optional[User]:
        """Get current user from JWT token"""
        payload = self.verify_access_token(token)
        if payload is None:
            return None
        
        user_id = int(payload.get("sub"))
        return self.get_user_by_id(user_id)
    
    def generate_login_credentials(self) -> Tuple[str, str]:
        """Generate token and 6-digit code"""
        token = secrets.token_urlsafe(32)
        code = str(secrets.randbelow(1000000)).zfill(6)
        return token, code
    
    def hash_credentials(self, token: str, code: str) -> Tuple[str, str]:
        """Hash token and code for storage"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        return token_hash, code_hash
    
    def create_login_token(self, user: User, email: str, ip_address: str, user_agent: str) -> Tuple[str, str]:
        """Create login token and code, return plain versions for email"""
        token, code = self.generate_login_credentials()
        token_hash, code_hash = self.hash_credentials(token, code)
        
        expires_at = datetime.utcnow() + timedelta(minutes=LOGIN_TOKEN_TTL_MINUTES)
        
        login_token = LoginToken(
            user_id=user.id,
            email=email,
            token_hash=token_hash,
            code_hash=code_hash,
            expires_at=expires_at,
            ip_created=ip_address,
            user_agent_created=user_agent
        )
        
        self.db.add(login_token)
        self.db.commit()
        
        return token, code
    
    def verify_login_token(self, token: str, ip_address: str, user_agent: str) -> Optional[User]:
        """Verify login token and mark as used"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        login_token = self.db.query(LoginToken).filter(
            and_(
                LoginToken.token_hash == token_hash,
                LoginToken.used_at.is_(None),
                LoginToken.expires_at > datetime.utcnow()
            )
        ).first()
        
        if not login_token:
            return None
        
        # Mark as used
        login_token.used_at = datetime.utcnow()
        self.db.commit()
        
        # Update user's last login
        user = self.get_user_by_id(login_token.user_id)
        if user:
            user.last_login = datetime.utcnow()
            self.db.commit()
        
        return user
    
    def verify_login_code(self, email: str, code: str, ip_address: str, user_agent: str) -> Optional[User]:
        """Verify login code and mark token as used"""
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        
        login_token = self.db.query(LoginToken).filter(
            and_(
                LoginToken.email == email,
                LoginToken.code_hash == code_hash,
                LoginToken.used_at.is_(None),
                LoginToken.expires_at > datetime.utcnow()
            )
        ).first()
        
        if not login_token:
            return None
        
        # Mark as used
        login_token.used_at = datetime.utcnow()
        self.db.commit()
        
        # Update user's last login
        user = self.get_user_by_id(login_token.user_id)
        if user:
            user.last_login = datetime.utcnow()
            self.db.commit()
        
        return user
    
    def check_rate_limit_login(self, email: str, ip_address: str) -> bool:
        """Check rate limit for login attempts"""
        # Check recent attempts from same IP
        recent_ip_attempts = self.db.query(LoginAttempt).filter(
            and_(
                LoginAttempt.ip_address == ip_address,
                LoginAttempt.created_at > datetime.utcnow() - timedelta(seconds=RATE_LIMIT_LOGIN_SECONDS)
            )
        ).count()
        
        if recent_ip_attempts > 0:
            return False
        
        # Check daily attempts for same email
        daily_email_attempts = self.db.query(LoginAttempt).filter(
            and_(
                LoginAttempt.email == email,
                LoginAttempt.created_at > datetime.utcnow() - timedelta(days=1)
            )
        ).count()
        
        if daily_email_attempts >= RATE_LIMIT_DAILY_LOGINS:
            return False
        
        return True
    
    def check_rate_limit_code(self, email: str) -> bool:
        """Check rate limit for code verification attempts"""
        recent_attempts = self.db.query(LoginAttempt).filter(
            and_(
                LoginAttempt.email == email,
                LoginAttempt.attempt_type == "verify_code",
                LoginAttempt.created_at > datetime.utcnow() - timedelta(minutes=LOGIN_TOKEN_TTL_MINUTES)
            )
        ).count()
        
        return recent_attempts < RATE_LIMIT_CODE_ATTEMPTS
    
    def log_login_attempt(self, email: str, ip_address: str, user_agent: str, 
                         success: bool, attempt_type: str, user_id: Optional[int] = None):
        """Log login attempt"""
        attempt = LoginAttempt(
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            attempt_type=attempt_type
        )
        self.db.add(attempt)
        self.db.commit()
    
    def send_login_credentials_email(self, email: str, token: str, code: str, user_name: str = None) -> bool:
        """Send email with login link and code"""
        try:
            msg = MIMEMultipart()
            msg['From'] = SMTP_USERNAME
            msg['To'] = email
            msg['Subject'] = "Giriş Bilgileriniz - AI Helper"
            
            # Create login link
            login_link = f"{FRONTEND_URL}/?token={token}"
            
            # Email body
            body = f"""
            Merhaba {user_name or 'Kullanıcı'},
            
            AI Helper sistemine giriş yapmak için aşağıdaki bilgileri kullanabilirsiniz:
            
            🔗 Giriş Linki: {login_link}
            🔢 Giriş Kodu: {code}
            
            Bu bilgiler 10 dakika geçerlidir ve sadece bir kez kullanılabilir.
            
            Eğer bu e-postayı siz talep etmediyseniz, lütfen dikkate almayın.
            
            Saygılarımızla,
            AI Helper Ekibi
            """
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Send email
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                if SMTP_USE_TLS:
                    server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"Email sending failed: {e}")
            return False
    
    def cleanup_expired_tokens(self):
        """Clean up expired login tokens"""
        expired_tokens = self.db.query(LoginToken).filter(
            LoginToken.expires_at < datetime.utcnow()
        ).all()
        
        for token in expired_tokens:
            self.db.delete(token)
        
        self.db.commit()
