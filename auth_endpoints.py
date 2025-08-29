from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import re

from connection import get_db
from auth_system import AuthService
from api_models import (
    LoginRequest, LoginResponse, CodeVerifyRequest, CodeVerifyResponse,
    TokenConsumeRequest, TokenConsumeResponse, UserProfile
)

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

# Email domain validation
ALLOWED_DOMAINS = ["nilufer.bel.tr", "niluferyzeka.tr"]

def validate_email_domain(email: str) -> bool:
    """Validate email domain"""
    domain = email.split('@')[-1].lower()
    return domain in ALLOWED_DOMAINS

def get_client_ip(request: Request) -> str:
    """Get client IP address"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host

def get_user_agent(request: Request) -> str:
    """Get user agent"""
    return request.headers.get("User-Agent", "")

@router.post("/send", response_model=LoginResponse)
async def send_login_credentials(
    request: LoginRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """Send login credentials (token + code) via email"""
    
    # Validate email domain
    if not validate_email_domain(request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu e-posta adresi desteklenmiyor"
        )
    
    auth_service = AuthService(db)
    
    # Check rate limiting
    client_ip = get_client_ip(http_request)
    if not auth_service.check_rate_limit_login(request.email, client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Çok fazla giriş denemesi. Lütfen bekleyin."
        )
    
    # Get or create user
    user = auth_service.get_user_by_email(request.email)
    if not user:
        user = auth_service.create_user(request.email)
    
    # Create login credentials
    token, code = auth_service.create_login_token(
        user, request.email, client_ip, get_user_agent(http_request)
    )
    
    # Send email
    email_sent = auth_service.send_login_credentials_email(
        request.email, token, code, user.name
    )
    
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="E-posta gönderilemedi"
        )
    
    # Log successful attempt
    auth_service.log_login_attempt(
        request.email, client_ip, get_user_agent(http_request),
        True, "send", user.id
    )
    
    return LoginResponse(
        message="Giriş bilgileri e-posta adresinize gönderildi",
        success=True
    )

@router.post("/verify-code", response_model=CodeVerifyResponse)
async def verify_login_code(
    request: CodeVerifyRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """Verify 6-digit login code"""
    
    auth_service = AuthService(db)
    
    # Check rate limiting
    if not auth_service.check_rate_limit_code(request.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Çok fazla kod denemesi. Lütfen yeni bir kod isteyin."
        )
    
    # Verify code
    user = auth_service.verify_login_code(
        request.email, request.code,
        get_client_ip(http_request), get_user_agent(http_request)
    )
    
    if not user:
        # Log failed attempt
        auth_service.log_login_attempt(
            request.email, get_client_ip(http_request), get_user_agent(http_request),
            False, "verify_code"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz kod veya kod süresi dolmuş"
        )
    
    # Create access token
    access_token = auth_service.create_access_token(user)
    
    # Log successful attempt
    auth_service.log_login_attempt(
        request.email, get_client_ip(http_request), get_user_agent(http_request),
        True, "verify_code", user.id
    )
    
    return CodeVerifyResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role
        }
    )

@router.post("/consume-token", response_model=TokenConsumeResponse)
async def consume_login_token(
    request: TokenConsumeRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """Consume login token from URL"""
    
    auth_service = AuthService(db)
    
    # Verify token
    user = auth_service.verify_login_token(
        request.token,
        get_client_ip(http_request), get_user_agent(http_request)
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz token veya token süresi dolmuş"
        )
    
    # Create access token
    access_token = auth_service.create_access_token(user)
    
    # Log successful attempt
    auth_service.log_login_attempt(
        user.email, get_client_ip(http_request), get_user_agent(http_request),
        True, "consume_token", user.id
    )
    
    return TokenConsumeResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role
        }
    )

@router.get("/profile", response_model=UserProfile)
async def get_user_profile(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current user profile"""
    
    auth_service = AuthService(db)
    user = auth_service.get_current_user(credentials.credentials)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz token"
        )
    
    return UserProfile(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login
    )

@router.post("/logout")
async def logout():
    """Logout endpoint (client-side token removal)"""
    return {"message": "Başarıyla çıkış yapıldı"}

# Cleanup expired tokens periodically
@router.post("/cleanup")
async def cleanup_expired_tokens(db: Session = Depends(get_db)):
    """Clean up expired login tokens (admin endpoint)"""
    auth_service = AuthService(db)
    auth_service.cleanup_expired_tokens()
    return {"message": "Süresi dolmuş tokenlar temizlendi"}
