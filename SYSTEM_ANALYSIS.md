# AI Helper Sistemi - Detaylı Kod Analizi

## Sistem Mimarisi

### 1. Backend (FastAPI)
**Dosyalar:**
- `main.py` - Ana FastAPI uygulaması
- `auth_endpoints.py` - Authentication API endpoints
- `auth_system.py` - Authentication servisleri
- `connection.py` - Database bağlantısı
- `models.py` - SQLAlchemy modelleri
- `api_models.py` - Pydantic modelleri

### 2. Frontend (Streamlit)
**Dosyalar:**
- `app.py` - Ana Streamlit uygulaması (1289 satır)
- `admin_panel.py` - Admin panel component

### 3. Database (SQLite)
**Tablo:**
- `users` - Kullanıcı bilgileri
- `login_tokens` - Giriş token'ları
- `login_attempts` - Giriş denemeleri
- `requests` - Vatandaş talepleri
- `responses` - AI yanıtları

## Authentication Sistemi

### 1. Giriş Akışı

#### A. E-posta Gönderimi (`/auth/send`)
```python
# Frontend'den e-posta adresi alınır
email = "zaferturan@nilufer.bel.tr"

# Backend'de:
1. E-posta domain kontrolü (@nilufer.bel.tr)
2. Rate limit kontrolü (IP + e-posta bazlı)
3. Kullanıcı oluştur/güncelle
4. 6 haneli kod + token üret
5. Hash'leme (SHA256)
6. Database'e kaydet (10 dakika geçerli)
7. E-posta gönder (magic link + kod)
```

#### B. Magic Link ile Giriş
```python
# E-posta linki: https://yardimci.niluferyapayzeka.tr/?token=ABC123
# Frontend'de URL'den token alınır
token = st.query_params['token']

# Backend'e gönderilir
POST /auth/consume-token
{
    "code": "ABC123"
}

# Backend'de:
1. Token hash'lenir
2. Database'de aranır
3. Süre kontrolü
4. Kullanılmış mı kontrolü
5. JWT access_token üretilir
6. Kullanıcı bilgileri döndürülür
```

#### C. Kod ile Giriş
```python
# Frontend'de 6 haneli kod girilir
code = "123456"

# Backend'e gönderilir
POST /auth/verify-code
{
    "email": "zaferturan@nilufer.bel.tr",
    "code": "123456"
}

# Backend'de:
1. Kod hash'lenir
2. Database'de aranır
3. Süre kontrolü
4. JWT access_token üretilir
```

### 2. Session Yönetimi

#### A. Streamlit Session State
```python
# 20+ session state değişkeni
st.session_state = {
    "authenticated": True,
    "access_token": "jwt_token_here",
    "user_email": "zaferturan@nilufer.bel.tr",
    "user_full_name": "zafer turan",
    "user_department": "Bilgi İşlem Müdürlüğü",
    "profile_completed": True,
    "history": [],  # Yanıt geçmişi
    "responses": [],  # Üretilen yanıtlar
    "state": "draft",  # Durum makinesi
    "has_copied": False,  # Kopyalandı mı?
    "yanit_sayisi": 0,  # Yanıt sayısı
    # ... diğerleri
}
```

#### B. Token Kontrolü
```python
def check_authentication():
    # 1. URL'den token kontrolü
    if 'token' in st.query_params:
        # Magic link ile giriş
        return verify_token()
    
    # 2. Session state kontrolü
    if st.session_state.authenticated:
        # Backend'e profil isteği gönder
        # Token süresi kontrolü
        return verify_session()
    
    # 3. localStorage kontrolü (karmaşık)
    # JavaScript ile localStorage okuma
    return False
```

## Ana Uygulama Akışı

### 1. Sayfa Yükleme Sırası
```python
def main():
    # 1. Session state initialize
    initialize_session_state()
    
    # 2. URL token kontrolü
    if 'token' in st.query_params:
        verify_page()
        return
    
    # 3. Authentication kontrolü
    if not check_authentication():
        if st.session_state.login_sent:
            login_sent_page()
        else:
            login_page()
        return
    
    # 4. Profil tamamlama kontrolü
    if not st.session_state.profile_completed:
        profile_completion_page()
        return
    
    # 5. Ana uygulama
    show_main_interface()
```

### 2. Yanıt Üretme Süreci
```python
# 1. Kullanıcı "Yanıt Üret" butonuna tıklar
if st.button("🚀 Yanıt Üret"):
    st.session_state.is_generating = True
    st.rerun()

# 2. Loading ekranı gösterilir
if st.session_state.is_generating:
    show_loading_screen()
    
    # 3. Arka planda yanıt üretilir
    request_id = create_request(original_text)
    response_data = generate_response(request_id, custom_input, ...)
    
    # 4. Session state güncellenir
    st.session_state.generated_response = response_data
    st.session_state.history.insert(0, response_data)
    st.session_state.yanit_sayisi += 1
```

### 3. Clipboard Sistemi
```python
def copy_to_clipboard(text):
    """Systemd servisi için clipboard kopyalama - sadece xclip"""
    try:
        result = subprocess.run(['xclip', '-selection', 'clipboard'], 
                              input=text.encode('utf-8'), 
                              capture_output=True, 
                              text=True, 
                              check=True)
        return True
    except:
        return False

# Kullanım:
if st.button("📋 Seç ve Kopyala"):
    if copy_to_clipboard(response_text):
        st.success("✅ Yanıt panoya kopyalandı!")
        # Backend'e kopyalandı olarak işaretle
        mark_response_as_copied(response_id)
        # Durum makinesini güncelle
        st.session_state.has_copied = True
        st.session_state.state = "finalized"
```

## Durum Makinesi

### 1. State Değişkenleri
```python
"state": "draft" | "finalized"  # Ana durum
"has_copied": False | True      # Kopyalandı mı?
"yanit_sayisi": 0-5            # Yanıt sayısı (max 5)
```

### 2. Durum Geçişleri
```python
# Başlangıç
state = "draft"
yanit_sayisi = 0

# Yanıt üretildiğinde
yanit_sayisi += 1

# Kopyalandığında
has_copied = True
state = "finalized"

# Yeni istek için
state = "draft"
has_copied = False
yanit_sayisi = 0
```

## Backend API Endpoints

### 1. Authentication
```python
POST /auth/send              # E-posta gönder
POST /auth/consume-token     # Magic link ile giriş
POST /auth/verify-code       # Kod ile giriş
GET  /auth/profile          # Kullanıcı profili
POST /auth/complete-profile  # Profil tamamlama
```

### 2. Request/Response
```python
POST /requests              # Yeni istek oluştur
POST /generate              # AI yanıtı üret
PUT  /responses/{id}/mark-copied  # Kopyalandı işaretle
POST /responses/feedback    # Feedback güncelle
```

### 3. Admin
```python
GET /admin/stats            # İstatistikler
GET /admin/users            # Kullanıcı listesi
GET /admin/users/{id}/stats # Kullanıcı istatistikleri
```

## Database Modelleri

### 1. User
```python
class User(Base):
    id: int
    email: str
    full_name: str
    department: str
    is_active: bool
    profile_completed: bool
    created_at: datetime
    last_login: datetime
```

### 2. LoginToken
```python
class LoginToken(Base):
    id: int
    email: str
    token_hash: str      # SHA256 hash
    code_hash: str       # SHA256 hash
    expires_at: datetime # 10 dakika
    used_at: datetime    # Kullanıldığı zaman
    ip_created: str
    user_agent_created: str
```

### 3. Request/Response
```python
class Request(Base):
    id: int
    user_id: int
    original_text: str
    response_type: str
    is_new_request: bool
    created_at: datetime

class Response(Base):
    id: int
    request_id: int
    response_text: str
    model_name: str
    temperature: float
    top_p: float
    repetition_penalty: float
    latency_ms: int
    is_selected: bool
    copied: bool
    has_been_copied: bool
    created_at: datetime
```

## Güvenlik Önlemleri

### 1. Rate Limiting
```python
# IP + e-posta bazlı rate limiting
# 10 dakikada maksimum 3 deneme
# 1 saatte maksimum 10 deneme
```

### 2. Token Güvenliği
```python
# SHA256 hash'leme
# 10 dakika geçerlilik süresi
# Tek kullanımlık token'lar
# IP ve User-Agent kaydı
```

### 3. Domain Kontrolü
```python
# Sadece @nilufer.bel.tr e-postaları
# E-posta doğrulama
```

## Clipboard Sorunu

### 1. Mevcut Durum
```python
# Streamlit'te JavaScript clipboard API çalışmıyor
# pyperclip systemd servisinde çalışmıyor
# xclip kullanılıyor ama başarısız
```

### 2. Çözüm Denemeleri
```python
# 1. pyperclip (başarısız)
# 2. xclip (başarısız)
# 3. xsel (başarısız)
# 4. JavaScript clipboard API (başarısız)
# 5. Systemd environment variables (başarısız)
```

### 3. Gradio Alternatifi
```python
# JavaScript clipboard API Gradio'da çalışıyor
# Daha iyi browser entegrasyonu
# Modern web API'leri desteği
```

## Sistem Entegrasyonu

### 1. E-posta Sistemi
```python
# SMTP ile e-posta gönderimi
# HTML template'ler
# Magic link + kod içerik
# Production URL: https://yardimci.niluferyapayzeka.tr
```

### 2. AI Model Entegrasyonu
```python
# Gemini 2.5 Flash (varsayılan)
# Gemini 1.5 Flash
# GPT-OSS
# Temperature, Top-p, Repetition Penalty ayarları
```

### 3. Admin Panel
```python
# Sadece zaferturan@nilufer.bel.tr erişimi
# Kullanıcı istatistikleri
# Yanıt sayıları
# Kopyalama oranları
# Grafik ve tablolar
```

## Production Deployment

### 1. Docker Compose
```python
# Backend: localhost:8000
# Frontend: localhost:8500
# Database: SQLite (volume)
# Logs: volume
```

### 2. Systemd Service
```python
# ai-helper.service
# start_service.sh
# manage_service.sh
# X11 environment variables
```

### 3. Cloudflare Tunnel
```python
# Production URL: yardimci.niluferyapayzeka.tr
# SSL sertifikası
# Domain yönlendirme
```

## Önemli Notlar

### 1. Authentication Karmaşıklığı
- Magic link + kod sistemi
- Session state yönetimi
- Token süresi kontrolü
- Profil tamamlama zorunluluğu

### 2. State Management
- 20+ session state değişkeni
- Durum makinesi
- Yanıt sayısı kontrolü
- Kopyalama durumu

### 3. Clipboard Sorunu
- Streamlit'te JavaScript çalışmıyor
- Systemd servisinde pyperclip çalışmıyor
- Gradio'ya geçiş gerekli

### 4. Backend Bağımlılığı
- Tüm işlemler backend API'ye bağımlı
- Authentication zorunlu
- Database persistence
- Rate limiting

## Sonuç

Bu sistem oldukça karmaşık bir authentication ve state management yapısına sahip. Gradio'ya geçiş yapmak için:

1. **Authentication wrapper** gerekli
2. **State management** Gradio'ya uyarlanmalı
3. **URL parameter handling** çözülmeli
4. **Session persistence** sağlanmalı
5. **Clipboard functionality** JavaScript ile çözülmeli

Sistem tamamen çalışır durumda, sadece clipboard sorunu var. Gradio'ya geçiş mümkün ama karmaşık.


