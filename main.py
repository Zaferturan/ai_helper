from fastapi import FastAPI, Request, Query
from fastapi.responses import RedirectResponse
from connection import engine
import models
from endpoints import router
from auth_endpoints import auth_router
from config import PRODUCTION_URL

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="AI Helper API",
    description="AI Helper Backend API with Authentication",
    version="1.0.0"
)

# Include API endpoints
app.include_router(router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")

@app.get("/")
async def root():
    """
    Ana sayfa
    """
    return {"message": "AI Helper API çalışıyor"}

@app.get("/gradio_api/{path:path}")
async def gradio_proxy(path: str):
    """
    Gradio API isteklerini frontend'e proxy et
    """
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:8500/gradio_api/{path}")
            return response.json()
    except Exception as e:
        return {"error": str(e)}

@app.post("/gradio_api/{path:path}")
async def gradio_proxy_post(path: str, request: Request):
    """
    Gradio API POST isteklerini frontend'e proxy et
    """
    import httpx
    try:
        body = await request.body()
        async with httpx.AsyncClient() as client:
            response = await client.post(f"http://localhost:8500/gradio_api/{path}", content=body)
            return response.json()
    except Exception as e:
        return {"error": str(e)}

@app.post("/auth/send-and-wait")
async def send_email_and_wait_for_verification(request: dict):
    """
    Email gönder ve kullanıcının giriş yapmasını bekle
    Gradio'da UI geçişi yerine backend'de tüm işlemi yap
    """
    try:
        email = request.get("email")
        
        # Email validasyonu
        if not email or not email.endswith("@nilufer.bel.tr"):
            return {"success": False, "message": "Geçersiz email adresi"}
        
        # Mevcut /api/v1/auth/send endpoint'ini kullan
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://localhost:8000/api/v1/auth/send",
                json={"email": email}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return {
                        "success": True, 
                        "message": f"Email gönderildi: {email}",
                        "next_step": "code_verification",
                        "email": email
                    }
                else:
                    return {"success": False, "message": data.get("message", "Email gönderilemedi")}
            else:
                return {"success": False, "message": f"Backend hatası: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "message": f"Hata: {str(e)}"}

@app.get("/auth")
async def auth_redirect_legacy(token: str = Query(None)):
    """Legacy /auth endpoint - redirect to /api/v1/auth"""
    if token:
        return RedirectResponse(url=f"/api/v1/auth?token={token}", status_code=302)
    else:
        return RedirectResponse(url=f"{PRODUCTION_URL}/?error=no_token", status_code=302)

@app.get("/api/v1/auth")
async def auth_redirect(token: str = Query(None)):
    """
    Magic link kontrolü - URL parameter yaklaşımı ile frontend'e yönlendir
    """
    try:
        if not token:
            return RedirectResponse(url=f"{PRODUCTION_URL}/?error=no_token", status_code=302)
        
        # Token'ı doğrula
        import hashlib
        from sqlalchemy.orm import sessionmaker
        from models import LoginToken, User
        from datetime import datetime, timedelta
        import jwt
        from config import JWT_SECRET_KEY
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Token'ı hash'le
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Token'ı veritabanında ara
        login_token = db.query(LoginToken).filter(
            LoginToken.token_hash == token_hash,
            LoginToken.expires_at > datetime.utcnow()
        ).first()
        
        if login_token:
            # Kullanıcıyı email ile bul (user_id NULL olabilir)
            user = None
            if login_token.user_id:
                user = db.query(User).filter(User.id == login_token.user_id).first()
            else:
                user = db.query(User).filter(User.email == login_token.email).first()
            
            print(f"Token bulundu: {login_token.token_hash}")
            print(f"Kullanıcı bulundu: {user.email if user else 'None'}")
            print(f"Kullanıcı aktif: {user.is_active if user else 'None'}")
            
            if user and user.is_active:
                # JWT token oluştur
                jwt_token = jwt.encode({
                    "sub": str(user.id),
                    "email": user.email,
                    "exp": datetime.utcnow().timestamp() + 18000  # 5 saat
                }, JWT_SECRET_KEY, algorithm="HS256")
                
                # Gradio'da otomatik giriş için session oluştur
                # Session'ı database'e kaydet
                session_data = {
                    "user_id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "department": user.department,
                    "jwt_token": jwt_token,
                    "created_at": datetime.utcnow(),
                    "expires_at": datetime.utcnow() + timedelta(hours=5)
                }
                
                # Basit session storage (gerçek uygulamada Redis kullanılmalı)
                import json
                try:
                    with open("active_sessions.json", "r") as f:
                        sessions = json.load(f)
                except:
                    sessions = {}
                
                sessions[str(user.id)] = session_data
                
                with open("active_sessions.json", "w") as f:
                    json.dump(sessions, f, default=str)
                
                # Gradio'ya yönlendir
                redirect_url = f"{PRODUCTION_URL}/?auto_login=true"
                
                db.close()
                return RedirectResponse(url=redirect_url, status_code=302)
            else:
                db.close()
                return RedirectResponse(url=f"{PRODUCTION_URL}/?error=invalid_token", status_code=302)
        else:
            db.close()
            return RedirectResponse(url=f"{PRODUCTION_URL}/?error=invalid_token", status_code=302)
            
    except Exception as e:
        print(f"Token doğrulama hatası: {e}")
        return RedirectResponse(url=f"{PRODUCTION_URL}/?error=auth_failed", status_code=302)

@app.post("/api/v1/auth/verify-token")
async def verify_token_endpoint(request: dict):
    """
    Frontend'den gelen token'ı doğrula
    """
    try:
        token = request.get("token")
        if not token:
            return {"success": False, "message": "Token bulunamadı"}
        
        # JWT token'ı doğrula
        import jwt
        from config import JWT_SECRET_KEY
        
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("sub")
            email = payload.get("email")
            
            if user_id and email:
                return {
                    "success": True,
                    "message": "Token geçerli",
                    "user_id": user_id,
                    "email": email
                }
            else:
                return {"success": False, "message": "Geçersiz token içeriği"}
                
        except jwt.ExpiredSignatureError:
            return {"success": False, "message": "Token süresi dolmuş"}
        except jwt.InvalidTokenError:
            return {"success": False, "message": "Geçersiz token"}
            
    except Exception as e:
        return {"success": False, "message": f"Hata: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 