from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import logging
from sqlalchemy import func
import hashlib
import secrets
import os

from connection import get_db
from models import User, LoginToken, LoginAttempt, Request as DBRequest, Response as DBResponse
from auth_system import auth_service, get_current_user, get_client_ip, security
from api_models import (
    LoginRequest, 
    LoginResponse, 
    CodeVerifyRequest, 
    CodeVerifyResponse,
    TokenConsumeRequest,
    TokenConsumeResponse,
    UserProfile,
    ProfileCompletionRequest,
    AdminStats,
    AdminUsersResponse,
    UserStats,
    DevLoginRequest  # GELİŞTİRME MODU
)
from config import PRODUCTION_URL, FRONTEND_URL

# Router for authentication endpoints
auth_router = APIRouter(tags=["Authentication"])

# Logging
logger = logging.getLogger(__name__)

@auth_router.post("/send", response_model=LoginResponse)
async def send_login_credentials(
    request: LoginRequest,
    db: Session = Depends(get_db),
    client_request: Request = None
):
    """
    Giriş için gerekli link ve kodu gönder
    Sadece @nilufer.bel.tr e-posta adresleri kullanılabilir
    """
    
    # Get client IP
    ip_address = get_client_ip(client_request)
    user_agent = client_request.headers.get("user-agent", "")
    
    # Validate email domain
    if not request.email.endswith("@nilufer.bel.tr"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sadece @nilufer.bel.tr alan adına sahip e-posta adresleri kullanılabilir"
        )
    
    # Check rate limits (IP + email based)
    if not auth_service.check_rate_limit_login(ip_address, request.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Şu an gönderemiyoruz, biraz sonra tekrar dene"
        )
    
    try:
        # Get or create user
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            # Yeni kullanıcı oluştur - profil bilgileri daha sonra tamamlanacak
            user = User(
                email=request.email,
                full_name="",  # Geçici olarak boş, profil tamamlama sayfasında doldurulacak
                department="",  # Geçici olarak boş, profil tamamlama sayfasında doldurulacak
                is_active=True,
                profile_completed=False
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Generate 6-digit code and token
        code = secrets.token_hex(3)[:6].upper()  # 6 haneli kod
        token = secrets.token_urlsafe(32)  # Yüksek entropili token
        
        # Hash the code and token
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Debug logging
        logger.info(f"=== CODE GENERATION DEBUG ===")
        logger.info(f"Generated code: {code}")
        logger.info(f"Generated code hash: {code_hash}")
        
        # Calculate expiration time (5 hours)
        expires_at = datetime.utcnow() + timedelta(hours=5)
        
        # Save login token to database
        login_token = LoginToken(
            email=request.email,
            token_hash=token_hash,
            code_hash=code_hash,
            expires_at=expires_at,
            ip_created=ip_address,
            user_agent_created=user_agent,
            attempt_count=0
        )
        db.add(login_token)
        db.commit()
        
        # Send email with login link and code
        email_sent = await auth_service.send_login_credentials_email(
            request.email, 
            token, 
            code, 
            expires_at
        )
        
        if email_sent:
            # Log successful attempt
            login_attempt = LoginAttempt(
                user_id=user.id,
                email=request.email,
                ip_address=ip_address,
                success=True,
                method="token"
            )
            db.add(login_attempt)
            db.commit()
            
            logger.info(f"Login credentials sent successfully to {request.email} from IP {ip_address}")
            
            return LoginResponse(
                message="Eğer bu e-posta adresi kayıtlıysa, giriş için gerekli link ve kod gönderildi",
                email=request.email,
                expires_in_minutes=300
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="E-posta gönderilemedi"
            )
            
    except Exception as e:
        logger.error(f"Error sending login credentials: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="İşlem tamamlanamadı. Lütfen tekrar dene"
        )

@auth_router.post("/consume-token")
async def consume_login_token(
    request: TokenConsumeRequest,
    db: Session = Depends(get_db),
    client_request: Request = None
):
    """
    6 haneli kod ile giriş yap (1 kere kullanılır)
    """
    
    try:
        # Frontend'den gelen ham token'ı hash'le
        token_hash = hashlib.sha256(request.code.encode()).hexdigest()
        
        # Find the login token
        login_token = db.query(LoginToken).filter(
            LoginToken.token_hash == token_hash,
            LoginToken.expires_at > datetime.utcnow(),
            LoginToken.used_at.is_(None)
        ).first()
        
        if not login_token:
            # Token bulunamadı, süresi dolmuş veya kullanılmış
            raise HTTPException(
                status_code=400, 
                detail="Bağlantının süresi dolmuş veya kullanılmış"
            )
        
        # Mark token as used
        login_token.used_at = datetime.utcnow()
        db.commit()
        
        # Get user
        user = db.query(User).filter(User.email == login_token.email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Create access token
        access_token = auth_service.create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        # Log successful login
        login_attempt = LoginAttempt(
            user_id=user.id,
            email=user.email,
            ip_address=get_client_ip(client_request),
            success=True,
            method="token"
        )
        db.add(login_attempt)
        db.commit()
        
        logger.info(f"User {user.email} logged in successfully via token from IP {get_client_ip(client_request)}")
        
        # Return JSON response with token
        return {
            "access_token": access_token,
            "email": user.email,
            "full_name": user.full_name,
            "department": user.department,
            "profile_completed": user.profile_completed,
            "is_admin": user.is_admin
        }
        
    except Exception as e:
        logger.error(f"Error consuming login token: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="İşlem tamamlanamadı. Lütfen tekrar dene"
        )

@auth_router.get("/profile", response_model=UserProfile)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """
    Kullanıcı profil bilgilerini getir
    """
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        department=current_user.department,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        profile_completed=current_user.profile_completed
    )

@auth_router.post("/verify-code", response_model=CodeVerifyResponse)
async def verify_login_code(
    request: CodeVerifyRequest,
    db: Session = Depends(get_db),
    client_request: Request = None
):
    """
    6 haneli kod ile giriş yap
    """
    
    try:
        # Hash the code
        code_hash = hashlib.sha256(request.code.encode()).hexdigest()
        
        # Debug logging
        logger.info(f"=== CODE VERIFICATION DEBUG ===")
        logger.info(f"Email: {request.email}")
        logger.info(f"Code: {request.code}")
        logger.info(f"Code hash: {code_hash}")
        
        # Find the login token
        login_token = db.query(LoginToken).filter(
            LoginToken.code_hash == code_hash,
            LoginToken.email == request.email,
            LoginToken.expires_at > datetime.utcnow(),
            LoginToken.used_at.is_(None)
        ).first()
        
        if not login_token:
            # Code bulunamadı, süresi dolmuş veya kullanılmış
            logger.info(f"❌ Code verification failed: Token not found")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Kod yanlış, süresi dolmuş veya kullanılmış"
            )
        
        logger.info(f"✅ Token found: ID {login_token.id}")
        
        # Check attempt count and rate limiting
        if login_token.attempt_count >= 5:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Çok fazla deneme yapıldı. Lütfen yeni kod isteyin"
            )
        
        # Update attempt count
        login_token.attempt_count += 1
        login_token.last_attempt_at = datetime.utcnow()
        db.commit()
        
        # Get user
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Create access token
        access_token = auth_service.create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        # Mark token as used ONLY after successful verification
        login_token.used_at = datetime.utcnow()
        db.commit()
        
        # Log successful login
        login_attempt = LoginAttempt(
            user_id=user.id,
            email=user.email,
            ip_address=get_client_ip(client_request),
            success=True,
            method="code"
        )
        db.add(login_attempt)
        db.commit()
        
        logger.info(f"User {user.email} logged in successfully via code from IP {get_client_ip(client_request)}")
        
        return CodeVerifyResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            profile_completed=user.profile_completed,
            is_admin=user.is_admin
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying login code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="İşlem tamamlanamadı. Lütfen tekrar dene"
        )


@auth_router.post("/complete-profile")
async def complete_user_profile(
    profile_data: ProfileCompletionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Complete user profile with full name and department
    """
    try:
        # Update user profile
        current_user.full_name = profile_data.full_name
        current_user.department = profile_data.department
        current_user.profile_completed = True
        
        db.commit()
        
        return {"message": "Profil başarıyla tamamlandı"}
        
    except Exception as e:
        logger.error(f"Error in complete_user_profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profil güncellenirken hata oluştu"
        )

@auth_router.post("/logout")
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """
    Logout user (clear cookie and session)
    """
    # Clear the cookie
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=True,
        samesite="lax"
    )
    
    # Clear session from user_sessions.json
    try:
        import json
        import os
        
        sessions_file = "user_sessions.json"
        
        if os.path.exists(sessions_file):
            with open(sessions_file, "r") as f:
                sessions = json.load(f)
            
            # Remove sessions for this user
            sessions_to_remove = []
            for session_id, session_data in sessions.items():
                if session_data.get("user_email") == current_user.email:
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del sessions[session_id]
            
            with open(sessions_file, "w") as f:
                json.dump(sessions, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Cleared {len(sessions_to_remove)} sessions for user {current_user.email}")
    
    except Exception as e:
        logger.error(f"Error clearing sessions: {str(e)}")
    
    return {"message": "Başarıyla çıkış yapıldı"}

@auth_router.get("/health")
async def auth_health():
    """
    Authentication service health check
    """
    return {"status": "healthy", "service": "authentication"}

@auth_router.post("/debug/clear-cache")
async def clear_rate_limit_cache():
    """
    Clear rate limiting cache (for debugging only)
    """
    auth_service.clear_rate_limit_cache()
    return {"message": "Rate limiting cache cleared", "debug": True}

@auth_router.get("/debug/rate-limit-status/{email}")
async def get_rate_limit_status(email: str):
    """
    Get rate limiting status for an email (for debugging only)
    """
    status = auth_service.get_rate_limit_status(email)
    return {"email": email, "status": status, "debug": True}

# Admin endpoint'leri
@auth_router.get("/admin/stats", response_model=AdminStats)
async def get_admin_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get admin statistics (only for admin users)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gerekli"
        )
    
    try:
        # Genel istatistikler
        total_users = db.query(User).count()
        total_requests = db.query(DBRequest).count()
        total_responses = db.query(DBResponse).count()
        
        # Yeni istek öneri sayısı (cevaplanan istek öneri sayısı)
        new_requests = db.query(DBRequest).filter(DBRequest.is_new_request == True).count()
        
        return AdminStats(
            total_users=total_users,
            total_requests=total_requests,
            total_responses=new_requests,  # Yeni istek öneri sayısı
            total_tokens=0,  # Token kullanımı kaldırıldı
            active_users_today=0,  # Kaldırıldı
            requests_today=0  # Kaldırıldı
        )
        
    except Exception as e:
        logger.error(f"Error in get_admin_stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="İstatistikler alınırken hata oluştu"
        )

@auth_router.get("/admin/users", response_model=AdminUsersResponse)
async def get_admin_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all users with statistics (only for admin users)
    """
    logger.info(f"Admin users request from user: {current_user.email}, is_admin: {current_user.is_admin}")
    
    if not current_user.is_admin:
        logger.warning(f"Non-admin user {current_user.email} tried to access admin endpoint")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için admin yetkisi gerekli"
        )
    
    try:
        # Kullanıcıları ve istatistiklerini al
        users = db.query(User).offset(skip).limit(limit).all()
        
        user_stats = []
        for user in users:
            # Kullanıcının ürettiği yanıt sayısı (Yanıt Üret ile oluşan Response satırları)
            total_responses = (
                db.query(DBResponse)
                .join(DBRequest, DBRequest.id == DBResponse.request_id)
                .filter(DBRequest.user_id == user.id)
                .count()
            )

            # Backward-compat: total_requests alanını "Toplam Ürettiği Yanıt" olarak gönder
            total_requests = total_responses

            # Kullanıcının cevapladığı benzersiz istek sayısı (ilk kopyalama sonrası)
            answered_requests = (
                db.query(DBRequest.id)
                .join(DBResponse, DBResponse.request_id == DBRequest.id)
                .filter(
                    DBRequest.user_id == user.id,
                    DBResponse.copied == True
                )
                .distinct()
                .count()
            )
            
            logger.info(f"User {user.email}: total_requests={total_requests}, answered_requests={answered_requests}")
            
            # Son aktivite (en son istek veya yanıt)
            last_request = db.query(DBRequest).filter(DBRequest.user_id == user.id).order_by(
                DBRequest.created_at.desc()
            ).first()
            
            last_response = db.query(DBResponse).join(DBRequest).filter(
                DBRequest.user_id == user.id
            ).order_by(DBResponse.created_at.desc()).first()
            
            last_activity = max(
                user.last_login or datetime.min,
                last_request.created_at if last_request else datetime.min,
                last_response.created_at if last_response else datetime.min
            )
            
            user_stats.append(UserStats(
                user_id=user.id,
                email=user.email,
                full_name=user.full_name,
                department=user.department,
                total_requests=total_requests,
                total_responses=total_responses,
                answered_requests=answered_requests,  # Cevapladığı istek sayısı
                total_tokens=0,  # Token kullanımı kaldırıldı
                last_activity=last_activity,
                is_active=user.is_active
            ))
        
        return AdminUsersResponse(
            users=user_stats,
            total_count=len(user_stats)
        )
        
    except Exception as e:
        logger.error(f"Error in get_admin_users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kullanıcı bilgileri alınırken hata oluştu"
        )

# GELİŞTİRME MODU: Direkt email ile giriş endpoint'i
@auth_router.post("/dev-login", response_model=LoginResponse)
async def dev_login(
    request: DevLoginRequest,
    db: Session = Depends(get_db)
):
    """
    GELİŞTİRME MODU: Direkt email ile giriş (JWT validation bypass)
    """
    try:
        # Email'e göre user bul
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            # Yeni kullanıcı oluştur
            user = User(
                email=request.email,
                full_name="",
                department="",
                is_active=True,
                profile_completed=False
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # GELİŞTİRME MODU: Token yerine email döndür
        return LoginResponse(
            access_token=user.email,  # Token yerine email
            token_type="dev",
            user_id=user.id,
            email=user.email,
            full_name=user.full_name
        )
        
    except Exception as e:
        logger.error(f"Error in dev_login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Giriş yapılırken hata oluştu"
        )

@auth_router.post("/dev-token", response_model=CodeVerifyResponse)
async def get_dev_token(
    db: Session = Depends(get_db)
):
    """
    Geliştirme için süresi dolmayan token al
    """
    # Kullanıcıyı bul - enginakyildiz için
    user = db.query(User).filter(User.email == "enginakyildiz@nilufer.bel.tr").first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bulunamadı"
        )
    
    # Süresi dolmayan token oluştur (1 yıl)
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "exp": datetime.utcnow() + timedelta(days=365)
    }
    
    token = auth_service.create_access_token(token_data)
    
    return CodeVerifyResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        profile_completed=user.profile_completed
    ) 

@auth_router.post("/verify-token")
async def verify_token(request: dict, db: Session = Depends(get_db)):
    """
    Magic link token'ını doğrula (1 kere kullanılır, 5 saat geçerli)
    """
    try:
        token = request.get("token")
        if not token:
            return {"success": False, "message": "Token bulunamadı"}
        
        # Token'ı hash'le ve veritabanında ara
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        login_token = db.query(LoginToken).filter(
            LoginToken.token_hash == token_hash,
            LoginToken.expires_at > datetime.utcnow(),
            LoginToken.used_at.is_(None)  # Kullanılmamış olmalı
        ).first()
        
        if not login_token:
            return {"success": False, "message": "Geçersiz veya süresi dolmuş token"}
        
        # Kullanıcıyı bul
        user = db.query(User).filter(User.id == login_token.user_id).first()
        if not user or not user.is_active:
            return {"success": False, "message": "Kullanıcı bulunamadı veya aktif değil"}
        
        # Access token üret
        access_token = auth_service.create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        # Token'ı kullanılmış olarak işaretle
        login_token.used_at = datetime.utcnow()
        db.commit()
        
        return {
            "success": True,
            "access_token": access_token,
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "department": user.department,
            "is_admin": user.is_admin
        }
        
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return {"success": False, "message": f"Token doğrulama hatası: {str(e)}"}

@auth_router.get("/verify-magic-link")
async def verify_magic_link(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Magic link token'ını doğrula (1 kere kullanılır, 5 saat geçerli)
    """
    try:
        # Token hash'ini oluştur
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Token'ı bul
        login_token = db.query(LoginToken).filter(
            LoginToken.token_hash == token_hash,
            LoginToken.used_at.is_(None),  # Kullanılmamış
            LoginToken.expires_at > datetime.utcnow()
        ).first()
        
        if not login_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Geçersiz veya süresi dolmuş token"
            )
        
        # Kullanıcıyı bul
        user = db.query(User).filter(User.email == login_token.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kullanıcı bulunamadı"
            )
        
        # Token'ı kullanılmış olarak işaretle
        login_token.used_at = datetime.utcnow()
        
        # JWT token oluştur
        jwt_token = auth_service.create_access_token({"sub": user.email})
        
        # Session bilgilerini döndür
        return {
            "email": user.email,
            "jwt_token": jwt_token,
            "full_name": user.full_name or "",
            "department": user.department or "",
            "created_at": datetime.utcnow().isoformat(),
            "is_admin": user.is_admin
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Magic link verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Magic link doğrulama hatası: {str(e)}"
        )

@auth_router.post("/save-session")
async def save_session(
    session_data: dict,
    db: Session = Depends(get_db)
):
    """
    Session bilgilerini active_sessions.json'a kaydet
    """
    try:
        import json
        import os
        
        email = session_data.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email gerekli"
            )
        
        # user_sessions.json dosyasını oku veya oluştur
        sessions_file = "user_sessions.json"
        if os.path.exists(sessions_file):
            with open(sessions_file, "r") as f:
                sessions = json.load(f)
        else:
            sessions = {}
        
        # Session'ı kaydet
        import time
        import hashlib
        
        # Unique session ID oluştur
        session_data_str = f"127.0.0.1_MagicLink"
        session_id = hashlib.md5(session_data_str.encode()).hexdigest()[:12]
        
        sessions[session_id] = {
            "user_email": email,
            "access_token": session_data.get("jwt_token"),
            "login_time": time.time(),
            "user_agent": "MagicLink",
            "ip_address": "127.0.0.1",
            "last_activity": time.time(),
            "is_admin": session_data.get("is_admin", False),
            "full_name": session_data.get("full_name", ""),
            "department": session_data.get("department", ""),
            "profile_completed": True
        }
        
        # Dosyaya yaz
        with open(sessions_file, "w") as f:
            json.dump(sessions, f, indent=2)
        
        return {"success": True, "message": "Session kaydedildi"}
        
    except Exception as e:
        logger.error(f"Session kaydetme hatası: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Session kaydetme hatası: {str(e)}"
        )

@auth_router.get("/session-status")
async def get_session_status():
    """
    Aktif session'ları listele
    """
    try:
        import json
        import os
        
        sessions_file = "user_sessions.json"
        
        if not os.path.exists(sessions_file):
            return {"sessions": []}
        
        with open(sessions_file, "r") as f:
            sessions = json.load(f)
        
        # Session'ları listeye çevir
        session_list = []
        for session_id, session_data in sessions.items():
            session_list.append({
                "session_id": session_id,
                "user_email": session_data.get("user_email"),
                "login_time": session_data.get("login_time"),
                "last_activity": session_data.get("last_activity")
            })
        
        # En son aktiviteye göre sırala
        session_list.sort(key=lambda x: x.get("last_activity", 0), reverse=True)
        
        return {"sessions": session_list}
        
    except Exception as e:
        logger.error(f"Session status hatası: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Session status hatası: {str(e)}"
        )

@auth_router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Belirli session'ı döndür - admin durumu dahil"""
    try:
        import json
        import os
        
        sessions_file = "user_sessions.json"
        
        if not os.path.exists(sessions_file):
            return {"error": "Session bulunamadı"}
        
        with open(sessions_file, "r") as f:
            sessions = json.load(f)
        
        if session_id not in sessions:
            return {"error": "Session bulunamadı"}
        
        session_data = sessions[session_id]
        
        # Aktiviteyi güncelle
        import time
        session_data['last_activity'] = time.time()
        
        # Dosyaya geri yaz
        with open(sessions_file, "w") as f:
            json.dump(sessions, f, indent=2)
        
        # Admin durumunu kontrol et
        user_email = session_data.get('user_email')
        
        # Veritabanından kullanıcı bilgilerini al
        db = next(get_db())
        user = db.query(User).filter(User.email == user_email).first()
        
        if user:
            # Session'a admin bilgisini ekle
            session_data['is_admin'] = user.is_admin
            session_data['full_name'] = user.full_name
            session_data['department'] = user.department
            session_data['profile_completed'] = user.profile_completed
            
            print(f"DEBUG: Session returned - email: {user_email}, admin: {user.is_admin}")
        
        db.close()
        return session_data
        
    except Exception as e:
        logger.error(f"Session retrieval hatası: {str(e)}")
        return {"error": "Session okuma hatası"} 