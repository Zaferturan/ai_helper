# AI Helper - Teknik Dokümantasyon

## 📋 İçindekiler
1. [Sistem Genel Bakış](#sistem-genel-bakış)
2. [Mimari ve Port Yapısı](#mimari-ve-port-yapısı)
3. [Dosya Yapısı](#dosya-yapısı)
4. [Authentication Flow](#authentication-flow)
5. [Database Yapısı](#database-yapısı)
6. [API Endpoints](#api-endpoints)
7. [Template Sistemi](#template-sistemi) ⭐ **YENİ**
8. [Frontend İşleyişi](#frontend-işleyişi)
9. [Docker Deployment](#docker-deployment)
10. [Önemli Fonksiyonlar](#önemli-fonksiyonlar)
11. [Troubleshooting](#troubleshooting)

---

## Sistem Genel Bakış

AI Helper, Bursa Nilüfer Belediyesi için geliştirilmiş bir yapay zeka destekli yanıt üretim sistemidir. Kullanıcılar, gelen istek/önerilere cevap taslakları hazırlayabilir, AI destekli yanıtlar üretebilir ve **şablon sistemi** ile sık kullanılan yanıtları kaydedip tekrar kullanabilir.

### Teknoloji Stack
- **Backend:** FastAPI (Python 3.11)
- **Frontend:** Vanilla JavaScript + HTML/CSS
- **Database:** PostgreSQL (zorunlu)
- **AI Models:** Ollama (lokal) + Google Gemini (cloud)
- **Web Server:** Nginx (reverse proxy)
- **Containerization:** Docker
- **Authentication:** JWT + Magic Link + 6-digit Code

---

## Mimari ve Port Yapısı

### Port Kullanımı

| Port | Servis | Açıklama |
|------|--------|----------|
| **8000** | FastAPI Backend | API endpoints, auth, business logic |
| **80** | Nginx (Docker içi) | Frontend static files + API proxy |
| **8500** | Host Port Mapping | Cloudflare → Docker:80 yönlendirmesi |
| **11434** | Ollama | Lokal AI model sunucusu |

### Mimari Şema

```
Cloudflare (Port 8500)
         ↓
Docker Container:80 (Nginx)
         ├─→ Static Files (/, /index.html, /app.js)
         └─→ API Proxy (/api/*) → localhost:8000 (FastAPI)
                                      ↓
                            ┌─────────┴─────────┐
                            ↓                   ↓
                     Ollama:11434        Gemini API
                     (Lokal AI)        (Cloud AI)
```

### Docker Container Yapısı

```dockerfile
FROM python:3.11-slim
├── FastAPI (Port 8000) - Backend API
├── Nginx (Port 80) - Frontend + Reverse Proxy
├── Volume: /app/data - SQLite database
└── Volume: /app/logs - Application logs
```

**Docker Run Komutu:**
```bash
docker run -d \
  --name ai_helper_container \
  --restart always \
  -p 8500:80 \
  -p 8000:8000 \
  -v ai_helper_data:/app/data \
  -v ai_helper_logs:/app/logs \
  ai_helper:latest
```

---

## Dosya Yapısı

### Core Backend Files

```
├── main.py                  # FastAPI ana uygulama
├── auth_endpoints.py        # Authentication endpoints
├── auth_system.py           # Auth logic, JWT, email
├── endpoints.py             # Business logic endpoints + Template API
├── models.py                # SQLAlchemy database models + Template models
├── api_models.py            # Pydantic request/response models + Template models
├── connection.py            # Database connection
├── config.py                # Configuration management
├── ollama_client.py         # Ollama AI client
├── gemini_client.py         # Gemini AI client
├── migrate_templates.py     # Template tabloları migration script'i
├── test_templates_api.py    # Template API test script'i
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container build file
├── nginx.conf               # Nginx configuration
├── start.sh                 # Container startup script
└── .env                     # Environment variables
```

### Frontend Files

```
frontend/
├── index.html              # Main HTML structure
├── app.js                  # Application logic (1849 lines)
├── style.css               # Styling
├── logo.png                # Belediye logosu
└── favicon.ico             # Site icon
```

### Data Files (Persistent)

```
data/
├── ai_helper.db            # SQLite database
└── .env                    # Production environment variables

logs/
└── app.log                 # Application logs
```

---

## Dosya Görevleri (Her Dosya Ne Yapar?)

### Backend Core Files

#### `main.py` (263 satır)
**Görev:** FastAPI uygulamasının ana entry point'i
- **Satır 1-19:** Import'lar ve FastAPI app oluşturma
- **Satır 20-28:** CORS middleware (cross-origin requests için)
- **Satır 30-32:** Router'ları ekleme (`/api/v1` prefix ile)
- **Satır 34-35:** Static file serving
- **Satır 37-42:** Root endpoint (`/`)
- **Satır 51-76:** Gradio proxy endpoints (legacy, kullanılmıyor)
- **Satır 78-114:** Email gönderme endpoint (legacy)
- **Satır 117-222:** **Magic link authentication handler** (GET `/api/v1/auth`)
  - Token'ı hash'leyip veritabanında arar
  - Kullanıcıyı bulur, JWT token oluşturur
  - Session'ı `user_sessions.json`'a kaydeder
  - Frontend'e `?auto_login=true&token=XXX` ile yönlendirir
- **Satır 224-259:** Token verification endpoint (POST `/api/v1/auth/verify-token`)

**Önemli Fonksiyonlar:**
- `auth_redirect()`: Magic link ile giriş yapan kullanıcıyı işler

---

#### `auth_endpoints.py` (948 satır)
**Görev:** Tüm authentication işlemlerini yönetir

**Ana Endpoint'ler:**

1. **POST `/api/v1/send`** (Satır 37-149)
   - Email ile giriş isteği yapar
   - 6 haneli kod + magic link token üretir
   - Her ikisini de hash'leyip veritabanına kaydeder
   - Email gönderir (5 saat geçerlilik)
   - Rate limiting uygular (IP + email bazlı)

2. **POST `/api/v1/verify-code`** (Satır 394-502)
   - 6 haneli kodu doğrular
   - Kod hash'ini veritabanında arar
   - Maksimum 5 deneme hakkı
   - JWT token döner
   - Token'ı `used_at` ile işaretler

3. **GET `/api/v1/magic-link`** (Satır 227-298)
   - Magic link ile giriş
   - Token'ı hash'leyip veritabanında arar
   - **Tekrar kullanılabilir** (5 saat boyunca)
   - Frontend'e redirect ile yönlendirir

4. **POST `/api/v1/verify-magic-link`** (Satır 300-376)
   - Magic link token'ını JSON response olarak döner
   - Frontend AJAX istekleri için

5. **POST `/api/v1/complete-profile`** (Satır 505-542)
   - İlk giriş sonrası profil tamamlama
   - `full_name` ve `department` günceller
   - `profile_completed = True` yapar

6. **POST `/api/v1/logout`** (Satır 544-588)
   - Kullanıcıyı çıkış yapar
   - `user_sessions.json`'dan session'ı siler
   - Cookie'yi temizler

7. **GET `/api/v1/admin/stats`** (Satır 614-651)
   - Admin istatistikleri
   - Toplam kullanıcı, istek, yanıt sayıları

8. **GET `/api/v1/admin/users`** (Satır 653-741)
   - Tüm kullanıcıların detaylı istatistikleri
   - Her kullanıcı için:
     - `total_requests`: Toplam üretilen yanıt sayısı
     - `answered_requests`: Cevapladığı istek sayısı (kopyalama bazlı)
     - `last_activity`: Son aktivite tarihi

**Önemli Fonksiyonlar:**
- `send_login_credentials()`: Email + kod gönderme
- `verify_login_code()`: 6 haneli kod doğrulama
- `magic_link_auth()`: Magic link ile giriş
- `complete_user_profile()`: Profil tamamlama
- `get_admin_stats()`: Admin istatistikleri
- `get_admin_users()`: Kullanıcı listesi ve detayları

---

#### `auth_system.py` (580 satır)
**Görev:** Authentication servis katmanı (business logic)

**AuthService Class:**

1. **Rate Limiting** (Satır 78-156)
   - `check_rate_limit_login()`: IP + email bazlı rate limiting
     - 5 saniye aralık zorunluluğu
     - Günlük 50 deneme limiti
   - `check_rate_limit_otp()`: OTP deneme limiti
   - `increment_otp_attempts()`: Deneme sayacı
   - Cache tabanlı, memory'de tutulan kontroller

2. **Email Sending** (Satır 274-413)
   - `send_login_credentials_email()`: Giriş emaili gönderir
     - Magic link oluşturur: `{PRODUCTION_URL}/api/v1/magic-link?token={token}` (PRODUCTION_URL .env'den okunur)
     - 6 haneli kod ekler
     - HTML + Plain text versiyonları
     - SMTP ile Gmail üzerinden gönderir
   - SMTP Settings:
     - Host: `SMTP_HOST` (.env)
     - Port: `SMTP_PORT` (587 - TLS)
     - Username: `SMTP_USERNAME`
     - Password: `SMTP_PASSWORD`

3. **JWT Token Management** (Satır 415-442)
   - `create_access_token()`: JWT token üretir
     - Geçerlilik: 5 saat (18000 saniye)
     - Payload: `{"sub": user_id, "email": email, "exp": timestamp}`
     - Algorithm: HS256
     - Secret: `JWT_SECRET_KEY` (.env)
   - `verify_token()`: JWT token doğrular

4. **User Authentication** (Satır 464-504)
   - `get_current_user()`: JWT token'dan kullanıcı bulur
     - Bearer token'ı parse eder
     - JWT verify eder
     - `user_id` ile veritabanından kullanıcıyı çeker
     - FastAPI Depends ile kullanılır

5. **Session Management** (Satır 516-580)
   - `save_user_session_to_file()`: Session'ı JSON dosyasına kaydeder
     - `user_sessions.json` dosyasına yazar
     - Session ID oluşturur (MD5 hash)
     - Kullanıcı bilgilerini ekler (email, is_admin, full_name, department)

**Önemli Sabitler:**
- `SECRET_KEY`: JWT şifreleme anahtarı
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token geçerlilik süresi (720 dakika = 12 saat)
- `RATE_LIMIT_EMAIL_SECONDS`: Email gönderme aralığı (60 saniye)
- `RATE_LIMIT_DAILY_EMAILS`: Günlük email limiti (10)
- `RATE_LIMIT_OTP_ATTEMPTS`: OTP deneme limiti (5)

---

#### `models.py` (116 satır)
**Görev:** SQLAlchemy database model tanımları

**Database Tables:**

1. **User** (Satır 6-22)
   ```python
   - id (Integer, Primary Key)
   - email (String 255, Unique, Not Null)
   - full_name (String 255, Not Null)
   - department (String 255, Not Null)
   - is_active (Boolean, Default: True)
   - created_at (DateTime, Auto)
   - last_login (DateTime, Nullable)
   - profile_completed (Boolean, Default: False)
   - is_admin (Boolean, Default: False)
   ```
   - İlişkiler: `login_attempts`, `login_tokens`, `requests`

2. **LoginAttempt** (Satır 24-42)
   ```python
   - id (Integer, Primary Key)
   - user_id (Integer, Foreign Key)
   - email (String 255)
   - ip_address (String 45, IPv6 support)
   - success (Boolean)
   - method (String 50: "token", "code", "magic_link")
   - timestamp (DateTime, Auto)
   ```
   - Index: `email + timestamp`, `ip + timestamp`

3. **LoginToken** (Satır 44-68)
   ```python
   - id (Integer, Primary Key)
   - user_id (Integer, Foreign Key, Nullable)
   - email (String 255)
   - token_hash (String 255) # Magic link token hash
   - code_hash (String 255)  # 6 haneli kod hash
   - expires_at (DateTime)   # 5 saat geçerlilik
   - used_at (DateTime, Nullable) # Kullanım zamanı
   - ip_created (String 45)
   - user_agent_created (String 500)
   - attempt_count (Integer, Default: 0)
   - last_attempt_at (DateTime, Nullable)
   ```
   - Index: `token_hash`, `code_hash`, `expires_at`, `email`

4. **Request** (Satır 70-84)
   ```python
   - id (Integer, Primary Key)
   - user_id (Integer, Foreign Key)
   - original_text (Text) # Gelen istek/öneri metni
   - response_type (String 50)
   - created_at (DateTime, Auto)
   - is_active (Boolean, Nullable)
   - remaining_responses (Integer, Nullable)
   - is_new_request (Boolean, Default: False)
   ```
   - İlişkiler: `user`, `responses`

5. **Response** (Satır 86-104)
   ```python
   - id (Integer, Primary Key)
   - request_id (Integer, Foreign Key)
   - model_name (String 100, Foreign Key)
   - response_text (Text) # AI tarafından üretilen yanıt
   - temperature (Float)
   - top_p (Float)
   - repetition_penalty (Float)
   - latency_ms (Integer, Nullable)
   - is_selected (Boolean, Default: False)
   - copied (Boolean, Default: False) # Kopyalandı mı?
   - created_at (DateTime, Auto)
   - tokens_used (Integer, Nullable)
   ```
   - İlişkiler: `request`, `model`

6. **Model** (Satır 106-116)
   ```python
   - id (Integer, Primary Key)
   - name (String 100, Unique)
   - display_name (String 200)
   - supports_embedding (Boolean, Default: False)
   - supports_chat (Boolean, Default: False)
   ```
   - İlişkiler: `responses`

---

#### `api_models.py` (125 satır)
**Görev:** Pydantic request/response model tanımları (API validation)

**Request Models:**
1. `LoginRequest` (Satır 6-7): Email ile giriş
2. `CodeVerifyRequest` (Satır 9-11): 6 haneli kod doğrulama
3. `TokenConsumeRequest` (Satır 13-14): Magic link token
4. `ProfileCompletionRequest` (Satır 51-54): Profil tamamlama
5. `RequestCreate` (Satır 58-61): Yeni istek oluşturma
6. `GenerateRequest` (Satır 63-70): AI yanıt üretme
7. `FeedbackRequest` (Satır 72-75): Yanıt seçme/kopyalama

**Response Models:**
1. `LoginResponse` (Satır 17-20): Email gönderildi mesajı
2. `CodeVerifyResponse` (Satır 22-30): JWT token + kullanıcı bilgileri
3. `TokenConsumeResponse` (Satır 32-39): Magic link sonucu
4. `UserProfile` (Satır 41-49): Kullanıcı profil bilgileri
5. `GenerateResponse` (Satır 90-96): Üretilen yanıt
6. `AdminStats` (Satır 103-109): Admin istatistikleri
7. `UserStats` (Satır 111-121): Kullanıcı detaylı istatistikleri

---

#### `connection.py` (26 satır)
**Görev:** SQLAlchemy database bağlantısı

```python
# Engine oluşturma
engine = create_engine(
    DATABASE_URL,  # .env'den okunur
    connect_args={"check_same_thread": False}  # SQLite için
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class
Base = declarative_base()

# Dependency function (FastAPI Depends için)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

#### `config.py` (94 satır)
**Görev:** Tüm konfigürasyon yönetimi (.env dosyası okuma)

**Önemli Değişkenler:**

```python
# URL Configuration
PRODUCTION_URL = "https://your-domain.com"
FRONTEND_URL = "http://localhost:8500"
BACKEND_URL = "http://localhost:8000"

# Database (yalnızca PostgreSQL)
# Öncelik sırası:
# 1) DATABASE_URL (postgresql şeması)
# 2) POSTGRES_* değişkenlerinden otomatik DSN
# Aksi halde çalışma durur (RuntimeError)
DATABASE_URL = "postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME"  # .env ile override edilir

# AI Models
OLLAMA_HOST = "http://localhost:11434"
GEMINI_API_KEY = ""  # .env'den okunur
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# JWT
JWT_SECRET_KEY = ""  # .env'den okunur
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 900  # 15 saat

# SMTP
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = ""  # .env
SMTP_PASSWORD = ""  # .env
SENDER_EMAIL = ""   # .env

# Rate Limiting
RATE_LIMIT_LOGIN_SECONDS = 5  # 5 saniye aralık
RATE_LIMIT_DAILY_LOGINS = 50  # Günlük 50 deneme
```

---

#### `ollama_client.py` (114 satır)
**Görev:** Ollama AI model client (lokal AI)

**Ana Fonksiyonlar:**

1. `get_available_models()` (Satır 13-32)
   - Ollama'dan mevcut modelleri çeker
   - `GET http://localhost:11434/api/tags`
   - Model listesi döner

2. `generate()` (Satır 34-97)
   - AI yanıtı üretir
   - Endpoint: `POST /api/generate`
   - Parametreler:
     - `model`: Model adı (ör: "llama2")
     - `prompt`: Sistem promptu + kullanıcı girdisi
     - `temperature`: Yaratıcılık (0.1-2.0)
     - `top_p`: Nucleus sampling (0.1-1.0)
     - `top_k`: Top-k sampling (1-100)
     - `num_predict`: **Max token sayısı (4000)**
   - Stream yanıt alır, birleştirir
   - Latency ölçer (ms)

**Token Limiti Ayarı:**
```python
"num_predict": 4000  # Maksimum 4000 token üretir
```

---

#### `gemini_client.py` (174 satır)
**Görev:** Google Gemini AI client (cloud AI)

**Ana Fonksiyonlar:**

1. `get_available_models()` (Satır 16-39)
   - Gemini API'den model listesi çeker
   - `GET https://generativelanguage.googleapis.com/v1beta/models`
   - Sadece `generateContent` destekleyen modelleri filtreler

2. `generate()` (Satır 41-162)
   - AI yanıtı üretir
   - Endpoint: `POST /v1beta/models/{model}:generateContent`
   - Parametreler:
     - `model`: Model adı (ör: "gemini-2.5-flash")
     - `contents`: Sistem promptu + kullanıcı girdisi
     - `temperature`: Yaratıcılık
     - `topP`, `topK`: Sampling
     - `maxOutputTokens`: **Max token sayısı (4000)**
   - API key header ile gönderilir
   - JSON response parse eder

**Token Limiti Ayarı:**
```python
"maxOutputTokens": 4000  # Maksimum 4000 token üretir
```

---

#### `endpoints.py` (311 satır)
**Görev:** Business logic API endpoints (AI yanıt üretme, istatistikler)

**Ana Endpoint'ler:**

1. **GET `/api/v1/models`** (Satır 16-60)
   - Mevcut AI modellerini listeler
   - Ollama + Gemini modellerini birleştirir
   - Veritabanına senkronize eder

2. **POST `/api/v1/generate`** (Satır 62-158)
   - AI yanıtı üretir
   - İşlem adımları:
     1. Request kaydı oluştur (veritabanı)
     2. Belirtilen sayıda yanıt üret
     3. Model provider'a göre yönlendir (Ollama/Gemini)
     4. Her yanıt için Response kaydı oluştur
     5. Yanıtları frontend'e döner
   - Parametreler:
     - `original_text`: Gelen istek/öneri
     - `custom_input`: Kullanıcının cevap taslağı
     - `model_name`: Seçilen AI model
     - `temperature`: Yaratıcılık
     - `top_p`, `top_k`: Sampling
     - `system_prompt`: Sistem promptu
     - `response_count`: Kaç yanıt üretilecek

3. **POST `/api/v1/copy/{response_id}`** (Satır 160-177)
   - Yanıtı kopyalandı olarak işaretler
   - `has_been_copied = True` yapar

4. **GET `/api/v1/stats`** (Satır 179-227)
   - Kullanıcı istatistiklerini döner
   - **Sadece admin kullanıcılar erişebilir**
   - İstatistikler:
     - `total_users`: Toplam kullanıcı sayısı
     - `total_requests`: Toplam istek sayısı
     - `total_responses`: Toplam yanıt sayısı
     - `copied_responses`: Kopyalanan yanıt sayısı
     - `user_requests`: Kullanıcının istek sayısı
     - `user_responses`: Kullanıcının yanıt sayısı
     - `user_copied`: Kullanıcının kopyaladığı sayı

5. **GET `/api/v1/system-prompt`** (Satır 229-239)
   - Sistem promptunu döner
   - `saved_system_prompt.txt` dosyasından okur

6. **POST `/api/v1/system-prompt`** (Satır 241-257)
   - Sistem promptunu kaydeder
   - **Sadece admin kullanıcılar kaydedebilir**
   - `saved_system_prompt.txt` dosyasına yazar

7. **GET `/api/v1/profile`** (Satır 259-271)
   - Kullanıcı profil bilgilerini döner
   - JWT token ile authentication

8. **POST `/api/v1/profile/complete`** (Satır 273-292)
   - Profil tamamlama
   - `full_name` ve `department` günceller
   - `profile_completed = True` yapar

9. **GET `/api/v1/session`** (Satır 294-306)
   - Session durumunu kontrol eder
   - Kullanıcı bilgilerini döner

---

### Frontend Files

#### `frontend/index.html` (296 satır)
**Görev:** Uygulamanın ana HTML yapısı

**Ekran Yapısı:**

1. **Loading Screen** (Satır 11-15)
   - İşlem yapılırken gösterilen loading ekranı

2. **Login Screen** (Satır 17-44)
   - Email input field
   - "Bağlantı ve Kod Gönder" butonu
   - Hata mesajı alanı

3. **Code Verification Screen** (Satır 46-70)
   - 6 haneli kod input (maxlength="6")
   - "Kodu Doğrula" butonu
   - Email bilgisi gösterimi

4. **Profile Completion Screen** (Satır 72-125)
   - Ad Soyad input
   - Müdürlük select (26 seçenek)
   - "Profili Tamamla" butonu

5. **Main Application Screen** (Satır 127-291)
   - **Banner** (Satır 131-141): Logo + başlık
   - **User Info Bar** (Satır 143-149): Kullanıcı bilgisi + çıkış butonu
   - **Admin Panel** (Satır 151-163): İstatistikler (accordion, admin-only)
   - **Sol Sütun** (Satır 170-218):
     - "Gelen İstek/Öneri" textarea
     - "Hazırladığınız Cevap Taslağı" textarea
     - "Yanıt Ayarları" accordion (Model, Temperature, Max Tokens)
     - "Yanıt Üret" butonu
   - **Sağ Sütun** (Satır 220-288):
     - "Son Üretilen Yanıt" alanı
     - "Seç ve Kopyala" butonu
     - "Yeni İstek Öneri Cevapla" butonu
     - Önceki yanıtlar (4 accordion)

**Cache Busting:**
```html
<script src="app.js?v=20250916-05"></script>
```
Her güncelleme sonrası `v` parametresi değiştirilir.

---

#### `frontend/app.js` (1849 satır)
**Görev:** Tüm frontend logic ve UI management

**Sınıf Yapısı:**

1. **APIClient** (Satır 26-112)
   - Backend API çağrıları
   - Fonksiyonlar:
     - `sendLoginCode(email)`: Email gönder
     - `verifyCode(email, code)`: Kod doğrula
     - `verifyMagicLink(token)`: Magic link doğrula
     - `completeProfile(data)`: Profil tamamla
     - `getProfile()`: Profil bilgileri al
     - `generateResponse(data)`: AI yanıt üret
     - `getStats()`: İstatistikler al

2. **AuthManager** (Satır 176-616)
   - Authentication state yönetimi
   - Fonksiyonlar:
     - `checkBackendSession()`: Session kontrolü
       - URL parametrelerini parse eder (`auto_login`, `token`, `error`)
       - Magic link varsa `handleMagicLinkAuth()` çağrılır
       - Yoksa login ekranı gösterilir
     - `handleMagicLinkAuth(token)`: Magic link işleme
       - Backend'e token gönderir
       - JWT token alır, localStorage'a kaydeder
       - `profile_completed` kontrolü yapar
       - True ise → Main app
       - False ise → Profile completion
     - `sendLoginCode()`: Email gönderme
     - `verifyCode()`: 6 haneli kod doğrulama
       - Backend'e kod gönderir
       - JWT token alır
       - Profil durumuna göre yönlendirir
     - `completeProfile()`: Profil tamamlama
       - Ad Soyad + Müdürlük gönderir
       - Main app'e yönlendirir
     - `logout()`: Çıkış yapma
       - localStorage temizler
       - Login ekranına döner

3. **AppState** (Satır 939-975)
   - Uygulama state yönetimi (localStorage)
   - State Fields:
     ```javascript
     {
       currentState: 'draft' | 'generating' | 'generated',
       originalText: '',
       customInput: '',
       lastResponse: '',
       yanitSayisi: 0,
       previousResponses: [],
       selectedModel: 'gemini-2.5-flash',
       temperature: 0.7,
       maxTokens: 4000
     }
     ```
   - Fonksiyonlar:
     - `loadState()`: State yükle
     - `saveState()`: State kaydet
     - `resetState()`: State sıfırla

4. **UIManager** (Satır 1087-1488)
   - UI yönetimi ve ekran geçişleri
   - Fonksiyonlar:
     - `showScreen(screenId)`: Ekran göster/gizle
     - `showLoading()`: Loading ekranı göster
     - `hideLoading()`: Loading ekranı gizle
     - `showMainApp()`: Ana uygulama ekranı
       - Admin paneli göster/gizle (`isAdmin` kontrolü)
       - "Yanıt Ayarları" accordion göster/gizle (`isAdmin` kontrolü)
       - İstatistikleri yükle
     - `updateButtonVisibility()`: Butón görünürlük kontrolü
     - `updateAdminPanel()`: İstatistik paneli güncelleme
     - `clearTextboxValues()`: Input alanlarını temizle

5. **ResponseGenerator** (Satır 1489-1637)
   - AI yanıt üretme logic
   - Fonksiyonlar:
     - `generateResponse()`: Ana üretim fonksiyonu
       - Input validation (empty check)
       - Backend'e istek gönder
       - Yanıtları UI'da göster
       - State'i güncelle
     - `showResponse()`: Yanıtı ekranda göster
     - `copyResponse()`: Yanıtı kopyala
       - `navigator.clipboard.writeText()` kullanır
       - Backend'e `copied=true` gönderir

6. **Event Handlers** (Satır 1639-1791)
   - Button click event'leri
   - `DOMContentLoaded` event'i
   - Accordion toggle'ları

**Önemli Fonksiyonlar:**

- **checkAuthenticationState()** (Satır 527-551)
  - JWT token'ı localStorage'dan okur
  - Geçerliliğini kontrol eder
  - Boolean döner

- **newRequest()** (Satır 1575-1599)
  - "Yeni İstek Öneri Cevapla" butonu
  - Tüm alanları temizler
  - State'i sıfırlar
  - UI'ı initial state'e döndürür

- **clearTextboxValues()** (Satır 1446-1461)
  - "Gelen İstek/Öneri" ve "Hazırladığınız Cevap Taslağı" alanlarını boşaltır
  - Sayfa yüklendiğinde ve "Yeni İstek" butonuna basıldığında çalışır

**localStorage Kullanımı:**
```javascript
localStorage.setItem('auth_token', jwt_token);
localStorage.setItem('user_email', email);
localStorage.setItem('is_admin', is_admin);
localStorage.setItem('user_profile', JSON.stringify(profile));
localStorage.setItem('app_state', JSON.stringify(state));
```

---

## Authentication Flow

### 1. Email Gönderme (Login)

```mermaid
sequenceDiagram
    User->>Frontend: Email girer, "Gönder" tıklar
    Frontend->>Backend: POST /api/v1/send {email}
    Backend->>Database: User var mı kontrol
    alt User yoksa
        Backend->>Database: Yeni user oluştur (profile_completed=false)
    end
    Backend->>Backend: 6 haneli kod üret (secrets.token_hex)
    Backend->>Backend: Magic link token üret (secrets.token_urlsafe)
    Backend->>Backend: Her ikisini de SHA256 hash'le
    Backend->>Database: LoginToken kaydet (code_hash, token_hash, expires_at=+5h)
    Backend->>SMTP: Email gönder (kod + magic link)
    Backend->>Frontend: {success: true, message: "Email gönderildi"}
    Frontend->>User: Kod doğrulama ekranı göster
```

**Email İçeriği:**
- **Seçenek 1:** Magic Link (5 saat geçerli)
  - URL: `{PRODUCTION_URL}/api/v1/magic-link?token=XXX` (PRODUCTION_URL .env'den okunur)
- **Seçenek 2:** 6 Haneli Kod (5 saat geçerli)
  - Kod: `AB12CD` (hexadecimal, uppercase)

---

### 2A. Magic Link ile Giriş

```mermaid
sequenceDiagram
    User->>Browser: Email'deki magic link'e tıklar
    Browser->>Backend: GET /api/v1/magic-link?token=XXX
    Backend->>Backend: Token'ı SHA256 hash'le
    Backend->>Database: LoginToken ara (token_hash, expires_at > now)
    alt Token geçersiz veya expired
        Backend->>Browser: Redirect → /?error=invalid_token
    end
    Backend->>Database: User bilgilerini çek
    Backend->>Backend: JWT token oluştur (5 saat geçerli)
    Backend->>Backend: Session oluştur (user_sessions.json)
    Backend->>Browser: Redirect → /?auto_login=true&token=XXX
    Browser->>Frontend: index.html yükle
    Frontend->>Frontend: URL parametresini parse et (auto_login=true)
    Frontend->>Backend: POST /api/v1/verify-magic-link {code: token}
    Backend->>Frontend: {access_token, email, full_name, department, profile_completed, is_admin}
    Frontend->>Frontend: localStorage'a kaydet
    alt profile_completed == false
        Frontend->>User: Profil tamamlama ekranı göster
    else profile_completed == true
        Frontend->>User: Ana uygulama ekranı göster
    end
```

**Önemli:** Magic link'ler **tekrar kullanılabilir**. 5 saat boyunca aynı link ile giriş yapılabilir.

---

### 2B. 6 Haneli Kod ile Giriş

```mermaid
sequenceDiagram
    User->>Frontend: 6 haneli kod girer
    Frontend->>Backend: POST /api/v1/verify-code {email, code}
    Backend->>Backend: Code'u SHA256 hash'le
    Backend->>Database: LoginToken ara (code_hash, email, expires_at > now, used_at IS NULL)
    alt Kod geçersiz/expired/used
        Backend->>Frontend: {error: "Kod yanlış veya süresi dolmuş"}
        Frontend->>User: Hata mesajı göster
    end
    Backend->>Backend: attempt_count kontrol (max 5)
    alt attempt_count >= 5
        Backend->>Frontend: {error: "Çok fazla deneme"}
        Frontend->>User: Yeni kod istemesini söyle
    end
    Backend->>Database: attempt_count++ ve last_attempt_at güncelle
    Backend->>Database: User bilgilerini çek
    Backend->>Backend: JWT token oluştur
    Backend->>Database: LoginToken.users_at = now (tek kullanımlık)
    Backend->>Database: LoginAttempt kaydet (success=true, method="code")
    Backend->>Frontend: {access_token, email, full_name, department, profile_completed, is_admin}
    Frontend->>Frontend: localStorage'a kaydet
    alt profile_completed == false
        Frontend->>User: Profil tamamlama ekranı göster
    else profile_completed == true
        Frontend->>User: Ana uygulama ekranı göster
    end
```

**Önemli:** 6 haneli kod **tek kullanımlıktır**. Kod kullanıldıktan sonra `used_at` alanı set edilir.

---

### 3. Profil Tamamlama (İlk Giriş)

```mermaid
sequenceDiagram
    User->>Frontend: Ad Soyad + Müdürlük seç
    Frontend->>Backend: POST /api/v1/complete-profile {full_name, department}
    Backend->>Backend: JWT token'dan user_id al
    Backend->>Database: User güncelle (full_name, department, profile_completed=true)
    Backend->>Frontend: {success: true, message: "Profil tamamlandı"}
    Frontend->>Frontend: localStorage'daki profil bilgilerini güncelle
    Frontend->>User: Ana uygulama ekranı göster
```

---

### 4. Session Kontrolü (Sayfa Yenilendiğinde)

```mermaid
sequenceDiagram
    User->>Browser: Sayfa yenile
    Browser->>Frontend: index.html yükle
    Frontend->>Frontend: localStorage'dan auth_token oku
    alt Token varsa
        Frontend->>Backend: GET /api/v1/session (Header: Bearer token)
        Backend->>Backend: JWT token doğrula
        Backend->>Database: User bilgilerini çek
        Backend->>Frontend: {authenticated: true, email, full_name, ...}
        Frontend->>User: Ana uygulama ekranı göster
    else Token yoksa
        Frontend->>User: Login ekranı göster
    end
```

---

### 5. Logout

```mermaid
sequenceDiagram
    User->>Frontend: "Çıkış Yap" butonuna tıklar
    Frontend->>Frontend: localStorage'ı temizle
    Frontend->>Frontend: URL'i temizle (history.replaceState)
    Frontend->>User: Login ekranı göster
```

---

## AI Yanıt Üretme Flow

```mermaid
sequenceDiagram
    User->>Frontend: "Yanıt Üret" butonuna tıklar
    Frontend->>Frontend: Input validation (boş mu?)
    alt Boş ise
        Frontend->>User: Hata mesajı göster
    end
    Frontend->>Backend: POST /api/v1/generate {original_text, custom_input, model_name, temperature, ...}
    Backend->>Database: Request kaydı oluştur (user_id, original_text, response_type)
    Backend->>Database: Model bilgilerini çek (provider)
    alt provider == "ollama"
        Backend->>Ollama: POST /api/generate {model, prompt, temperature, top_p, top_k, num_predict: 4000}
        Ollama->>Backend: Stream response
    else provider == "gemini"
        Backend->>Gemini: POST /v1beta/models/{model}:generateContent {contents, temperature, topP, topK, maxOutputTokens: 4000}
        Gemini->>Backend: JSON response
    end
    Backend->>Database: Response kaydı oluştur (request_id, model_id, response_text, temperature, ...)
    Backend->>Frontend: {request_id, responses: [{id, text, model_name, has_been_copied}]}
    Frontend->>Frontend: State güncelle (currentState='generated', lastResponse=text, yanitSayisi++)
    Frontend->>Frontend: UI güncelle (response_area'ya yaz, accordion'ları göster)
    Frontend->>User: Üretilen yanıtı göster
```

**Yanıt Kopyalama:**
```mermaid
sequenceDiagram
    User->>Frontend: "Seç ve Kopyala" butonuna tıklar
    Frontend->>Browser: navigator.clipboard.writeText(response_text)
    Frontend->>Backend: POST /api/v1/copy/{response_id}
    Backend->>Database: Response.copied = true
    Backend->>Frontend: {success: true}
    Frontend->>User: "Kopyalandı!" toast mesajı
```

---

## Database Yapısı

### ER Diyagramı

```
┌─────────────────────────┐
│ User                    │
├─────────────────────────┤
│ id (PK)                 │
│ email (UNIQUE)          │
│ full_name               │
│ department              │
│ is_active               │
│ created_at              │
│ last_login              │
│ profile_completed       │
│ is_admin                │
└────────┬────────────────┘
         │
         │ 1:N
         │
┌────────▼────────────────┐      ┌─────────────────────────┐
│ Request                 │      │ LoginToken              │
├─────────────────────────┤      ├─────────────────────────┤
│ id (PK)                 │      │ id (PK)                 │
│ user_id (FK)            │      │ user_id (FK)            │
│ original_text           │      │ email                   │
│ response_type           │      │ token_hash (INDEX)      │
│ created_at              │      │ code_hash (INDEX)       │
│ is_active               │      │ expires_at (INDEX)      │
│ remaining_responses     │      │ used_at                 │
│ is_new_request          │      │ ip_created              │
└────────┬────────────────┘      │ user_agent_created      │
         │                        │ attempt_count           │
         │ 1:N                    │ last_attempt_at         │
         │                        └─────────────────────────┘
┌────────▼────────────────┐
│ Response                │      ┌─────────────────────────┐
├─────────────────────────┤      │ LoginAttempt            │
│ id (PK)                 │      ├─────────────────────────┤
│ request_id (FK)         │      │ id (PK)                 │
│ model_name (FK)         │      │ user_id (FK)            │
│ response_text           │      │ email (INDEX)           │
│ temperature             │      │ ip_address (INDEX)      │
│ top_p                   │      │ success                 │
│ repetition_penalty      │      │ method                  │
│ latency_ms              │      │ timestamp (INDEX)       │
│ is_selected             │      └─────────────────────────┘
│ copied                  │
│ created_at              │      ┌─────────────────────────┐
│ tokens_used             │      │ Model                   │
└─────────────────────────┘      ├─────────────────────────┤
                                  │ id (PK)                 │
                                  │ name (UNIQUE)           │
                                  │ display_name            │
                                  │ supports_embedding      │
                                  │ supports_chat           │
                                  └─────────────────────────┘
```

### İndeksler

**LoginToken:**
- `idx_login_tokens_token_hash` (token_hash)
- `idx_login_tokens_code_hash` (code_hash)
- `idx_login_tokens_expires` (expires_at)
- `idx_login_tokens_email` (email)

**LoginAttempt:**
- `idx_login_attempts_email_timestamp` (email, timestamp)
- `idx_login_attempts_ip_timestamp` (ip_address, timestamp)

**User:**
- `email` (UNIQUE)
- `id` (PRIMARY KEY)

---

## API Endpoints (Özet)

### Authentication Endpoints (auth_router)

| Method | Endpoint | Açıklama | Auth Required |
|--------|----------|----------|---------------|
| POST | `/api/v1/send` | Email gönder (magic link + kod) | ❌ |
| POST | `/api/v1/verify-code` | 6 haneli kod doğrula | ❌ |
| GET | `/api/v1/magic-link` | Magic link ile giriş (redirect) | ❌ |
| POST | `/api/v1/verify-magic-link` | Magic link doğrula (JSON) | ❌ |
| POST | `/api/v1/complete-profile` | Profil tamamla | ✅ |
| POST | `/api/v1/logout` | Çıkış yap | ✅ |
| GET | `/api/v1/profile` | Profil bilgileri | ✅ |
| GET | `/api/v1/admin/stats` | Admin istatistikleri | ✅ (Admin) |
| GET | `/api/v1/admin/users` | Kullanıcı listesi | ✅ (Admin) |
| GET | `/api/v1/session-status` | Session durumu | ❌ |
| GET | `/api/v1/session/{id}` | Session detayı | ❌ |
| POST | `/api/v1/save-session` | Session kaydet | ❌ |

### Business Logic Endpoints (router)

| Method | Endpoint | Açıklama | Auth Required |
|--------|----------|----------|---------------|
| GET | `/api/v1/models` | Mevcut AI modelleri | ✅ |
| POST | `/api/v1/generate` | AI yanıt üret | ✅ |
| POST | `/api/v1/copy/{response_id}` | Yanıtı kopyala işaretle | ✅ |
| GET | `/api/v1/stats` | İstatistikler | ✅ (Admin) |
| GET | `/api/v1/system-prompt` | Sistem promptu | ✅ |
| POST | `/api/v1/system-prompt` | Sistem promptu kaydet | ✅ (Admin) |
| GET | `/api/v1/profile` | Kullanıcı profili | ✅ |
| POST | `/api/v1/profile/complete` | Profil tamamla | ✅ |
| GET | `/api/v1/session` | Session kontrolü | ✅ |

### Template Endpoints (YENİ) ⭐

| Method | Endpoint | Açıklama | Auth Required |
|--------|----------|----------|---------------|
| GET | `/api/v1/templates` | Şablonları listele (filtreleme, arama) | ✅ |
| POST | `/api/v1/templates` | Yeni şablon oluştur | ✅ |
| DELETE | `/api/v1/templates/{id}` | Şablon sil (soft delete) | ✅ (Owner/Admin) |
| GET | `/api/v1/categories` | Kategorileri listele | ✅ |
| POST | `/api/v1/categories` | Yeni kategori oluştur | ✅ |
| DELETE | `/api/v1/categories/{id}` | Kategori sil | ✅ (Owner/Admin) |

---

## Template Sistemi ⭐ **YENİ ÖZELLİK**

### Genel Bakış

Template sistemi, kullanıcıların sık kullanılan yanıt metinlerini **kaydedip yeniden kullanabilmelerini** sağlar. Sistem departman bazlı çalışır ve güvenlik odaklıdır.

### Özellikler

- **Departman Bazlı Paylaşım:** Aynı müdürlükteki herkes şablonları görebilir
- **Kategori Sistemi:** Şablonlar kategorilere ayrılabilir
- **Sahiplik Kontrolü:** Sadece oluşturan (ve admin) silebilir
- **Soft Delete:** Şablonlar silinmez, `is_active=false` yapılır
- **Arama ve Filtreleme:** Başlık ve içerikte arama, kategori filtreleme
- **Otomatik Başlık:** Boş title ilk 80 karakterden üretilir

### Veritabanı Yapısı

#### TemplateCategory Tablosu
```sql
CREATE TABLE template_categories (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    department VARCHAR(255) NOT NULL,
    owner_user_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(name, department),  -- Aynı departmanda aynı isim
    FOREIGN KEY(owner_user_id) REFERENCES users(id)
);
```

#### Template Tablosu
```sql
CREATE TABLE templates (
    id INTEGER PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    department VARCHAR(255) NOT NULL,
    owner_user_id INTEGER NOT NULL,
    category_id INTEGER,  -- Opsiyonel
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,  -- Soft delete
    
    FOREIGN KEY(owner_user_id) REFERENCES users(id),
    FOREIGN KEY(category_id) REFERENCES template_categories(id)
);
```

### Güvenlik Kuralları

#### Departman İzolasyonu
```python
# Kullanıcı sadece kendi departmanını görebilir
if not current_user.is_admin:
    query = query.filter(Template.department == current_user.department)
```

#### Sahiplik Kontrolü
```python
# Sadece owner veya admin silebilir
if not current_user.is_admin and template.owner_user_id != current_user.id:
    raise HTTPException(status_code=403, detail="Sadece şablon sahibi silebilir")
```

#### Kategori Koruması
```python
# İçinde şablon olan kategori silinemez
if active_templates_count > 0:
    raise HTTPException(status_code=400, detail="Bu kategoride şablonlar bulunuyor")
```

### API Kullanımı

#### Şablon Listeleme
```bash
# Tüm şablonlar
GET /api/v1/templates

# Arama
GET /api/v1/templates?q=belediye

# Kategori filtresi
GET /api/v1/templates?category_id=1

# Sadece kendi şablonlarım
GET /api/v1/templates?only_mine=true

# Sayfalama
GET /api/v1/templates?limit=20&offset=40
```

#### Şablon Oluşturma
```bash
POST /api/v1/templates
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
    "title": "Belediye Yanıtı",  # Opsiyonel, boşsa otomatik üretilir
    "content": "Sayın vatandaşımız...",
    "category_id": 1  # Opsiyonel
}
```

#### Kategori Yönetimi
```bash
# Kategorileri listele
GET /api/v1/categories

# Yeni kategori oluştur
POST /api/v1/categories
{
    "name": "Genel Yanıtlar"
}

# Kategori sil (sadece owner/admin)
DELETE /api/v1/categories/1
```

### Frontend Entegrasyonu

#### Şablon Kaydetme
```javascript
// Yanıt üretim ekranında
const saveAsTemplate = async (content, categoryId) => {
    const response = await fetch('/api/v1/templates', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            content: content,
            category_id: categoryId
        })
    });
    return response.json();
};
```

#### Şablon Kullanma
```javascript
// Şablonları listele
const getTemplates = async (filters = {}) => {
    const params = new URLSearchParams(filters);
    const response = await fetch(`/api/v1/templates?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.json();
};
```

### Migration ve Kurulum

#### Tabloları Oluşturma
```bash
# Migration script'ini çalıştır
python migrate_templates.py
```

#### Test Etme
```bash
# API test script'ini çalıştır
python test_templates_api.py
```

### Gelecek Geliştirmeler

- **Favori Şablonlar:** Kullanıcılar şablonları favorilere ekleyebilir
- **Etiketleme:** Şablonlara etiket ekleme sistemi
- **Paylaşımsız Şablonlar:** Sadece sahibinin görebileceği özel şablonlar
- **FTS5 Arama:** Daha gelişmiş arama özellikleri
- **Şablon İstatistikleri:** En çok kullanılan şablonlar

---

## Docker Deployment

### Dockerfile Adımları

```dockerfile
# 1. Base image
FROM python:3.11-slim

# 2. Sistem paketleri
RUN apt-get update && apt-get install -y gcc g++ nginx

# 3. Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Uygulama dosyaları
COPY . .

# 5. Frontend dosyaları Nginx'e
COPY frontend/ /usr/share/nginx/html/

# 6. Production URL replacement (Dockerfile içinde)
RUN sed -i 's|http://localhost:8000/api/v1|${PRODUCTION_URL}/api/v1|g' /usr/share/nginx/html/app.js

# 7. Nginx konfigürasyonu
COPY nginx.conf /etc/nginx/sites-available/default

# 8. Port expose
EXPOSE 8000 80

# 9. Volume mount points
VOLUME ["/app/data", "/app/logs"]

# 10. Startup script
COPY start.sh .
RUN chmod +x start.sh
CMD ["./start.sh"]
```

### start.sh

```bash
#!/bin/bash

# .env dosyasını yükle
set -a
source /app/data/.env
set +a

# Backend'i arka planda başlat (Port 8000)
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &

# Nginx'i ön planda başlat (Port 80)
nginx -g "daemon off;"
```

### nginx.conf

```nginx
server {
    listen 80;
    server_name localhost;

    # Frontend static files
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API proxy
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Docker Komutları

**Build:**
```bash
docker build -t ai_helper:latest .
```

**Run:**
```bash
docker run -d \
  --name ai_helper_container \
  --restart always \
  -p 8500:80 \
  ai_helper:latest \
  -p 8000:8000 \
  -v ai_helper_data:/app/data \
  -v ai_helper_logs:/app/logs \
  ai_helper:latest
```

**Logs:**
```bash
docker logs -f ai_helper_container
```

**Shell Access:**
```bash
docker exec -it ai_helper_container bash
```

**Restart:**
```bash
docker restart ai_helper_container
```

**Stop:**
```bash
docker stop ai_helper_container
docker rm ai_helper_container
```

### Volume Management

**Data Volume (Database):**
```bash
docker volume inspect ai_helper_data
# → /var/lib/docker/volumes/ai_helper_data/_data
#    └── ai_helper.db
```

**Logs Volume:**
```bash
docker volume inspect ai_helper_logs
# → /var/lib/docker/volumes/ai_helper_logs/_data
#    └── app.log
```

---

## Önemli Fonksiyonlar

### Backend

#### 1. `send_login_credentials_email()` (auth_system.py)
```python
async def send_login_credentials_email(
    email: str, 
    token: str,   # Ham token (hash'lenmemiş)
    code: str,    # 6 haneli kod (hash'lenmemiş)
    expires_at: datetime
) -> bool:
    """
    Giriş emaili gönderir:
    - Magic link: `{PRODUCTION_URL}/api/v1/magic-link?token={token}` (PRODUCTION_URL .env'den okunur)
    - 6 haneli kod: {code}
    
    Returns:
        True: Email gönderildi
        False: Email gönderilemedi
    """
```

#### 2. `magic_link_auth()` (auth_endpoints.py)
```python
@auth_router.get("/magic-link")
async def magic_link_auth(
    token: str,                      # URL query parameter
    db: Session = Depends(get_db),
    client_request: Request = None
):
    """
    Magic link ile giriş:
    1. Token'ı SHA256 hash'le
    2. Veritabanında ara (token_hash, expires_at > now)
    3. User bilgilerini çek
    4. JWT token oluştur
    5. Session oluştur (user_sessions.json)
    6. Frontend'e redirect: /?auto_login=true&token={token}
    
    Note: Magic link tekrar kullanılabilir (5 saat)
    """
```

#### 3. `verify_login_code()` (auth_endpoints.py)
```python
@auth_router.post("/verify-code")
async def verify_login_code(
    request: CodeVerifyRequest,     # {email, code}
    db: Session = Depends(get_db),
    client_request: Request = None
) -> CodeVerifyResponse:
    """
    6 haneli kod ile giriş:
    1. Code'u SHA256 hash'le
    2. Veritabanında ara (code_hash, email, expires_at > now, used_at IS NULL)
    3. attempt_count kontrol (max 5)
    4. User bilgilerini çek
    5. JWT token oluştur
    6. Token'ı used_at ile işaretle (tek kullanımlık)
    7. LoginAttempt kaydet
    
    Returns:
        {access_token, email, full_name, department, profile_completed, is_admin}
    """
```

#### 4. `generate()` (ollama_client.py & gemini_client.py)
```python
def generate(
    model_name: str,
    original_text: str,      # Gelen istek/öneri
    custom_input: str,       # Kullanıcının cevap taslağı
    system_prompt: str,      # Sistem promptu
    temperature: float = 0.7,
    top_p: float = 0.9,
    top_k: int = 40
) -> str:
    """
    AI yanıtı üretir:
    
    Ollama:
        - Endpoint: POST /api/generate
        - Parametreler: num_predict=4000 (max token)
        
    Gemini:
        - Endpoint: POST /v1beta/models/{model}:generateContent
        - Parametreler: maxOutputTokens=4000
    
    Returns:
        Üretilen yanıt metni
    """
```

---

### Frontend

#### 1. `checkBackendSession()` (app.js)
```javascript
async checkBackendSession() {
    /**
     * Sayfa yüklendiğinde çağrılır:
     * 
     * 1. URL parametrelerini parse et:
     *    - auto_login=true & token=XXX → Magic link
     *    - error=invalid_token → Hata
     * 
     * 2. Magic link varsa:
     *    - handleMagicLinkAuth(token) çağır
     *    - JWT token al, localStorage'a kaydet
     *    - profile_completed kontrolü
     *    - True → Main app
     *    - False → Profile completion
     * 
     * 3. Magic link yoksa:
     *    - localStorage'dan auth_token kontrol
     *    - Varsa → Session kontrolü (/api/v1/session)
     *    - Yoksa → Login ekranı
     */
}
```

#### 2. `generateResponse()` (app.js)
```javascript
async generateResponse() {
    /**
     * "Yanıt Üret" butonuna tıklandığında:
     * 
     * 1. Input validation:
     *    - original_text boş mu?
     *    - custom_input boş mu?
     *    - Boşsa → Hata mesajı göster, return
     * 
     * 2. Backend'e istek gönder:
     *    POST /api/v1/generate
     *    {
     *      original_text,
     *      custom_input,
     *      model_name,
     *      temperature,
     *      top_p,
     *      top_k,
     *      system_prompt,
     *      response_count: 1
     *    }
     * 
     * 3. Yanıtı işle:
     *    - State güncelle (currentState='generated', yanitSayisi++)
     *    - UI güncelle (response_area, accordion'lar)
     *    - Önceki yanıtları listeye ekle
     * 
     * 4. Button görünürlüğünü güncelle:
     *    - "Seç ve Kopyala" → visible
     *    - "Yeni İstek Öneri Cevapla" → visible
     */
}
```

#### 3. `newRequest()` (app.js)
```javascript
function newRequest() {
    /**
     * "Yeni İstek Öneri Cevapla" butonuna tıklandığında:
     * 
     * 1. Input alanlarını temizle:
     *    - original_text = ''
     *    - custom_input = ''
     * 
     * 2. UI'ı sıfırla:
     *    - main-response = "Henüz yanıt üretilmedi..."
     *    - Accordion'ları gizle
     *    - Önceki yanıtlar listesini temizle
     * 
     * 3. State'i sıfırla:
     *    - currentState = 'draft'
     *    - lastResponse = ''
     *    - yanitSayisi = 0
     *    - previousResponses = []
     * 
     * 4. Button görünürlüğünü güncelle:
     *    - "Yanıt Üret" → visible
     *    - "Seç ve Kopyala" → hidden
     *    - "Yeni İstek Öneri Cevapla" → hidden
     */
}
```

#### 4. `clearTextboxValues()` (app.js)
```javascript
function clearTextboxValues() {
    /**
     * Input alanlarını temizler:
     * 
     * Çağrıldığı yerler:
     * 1. DOMContentLoaded (sayfa yüklendiğinde)
     * 2. newRequest() (yeni istek butonuna basıldığında)
     * 
     * Temizlenen alanlar:
     * - original-text (Gelen İstek/Öneri)
     * - custom-input (Hazırladığınız Cevap Taslağı)
     */
    document.getElementById('original-text').value = '';
    document.getElementById('custom-input').value = '';
}
```

---

## Buton Görevleri

### Login Ekranı

| Buton | ID | Görev |
|-------|-----|-------|
| **📧 Bağlantı ve Kod Gönder** | `send-btn` | Email gönder (magic link + kod) → Kod doğrulama ekranına geç |

### Kod Doğrulama Ekranı

| Buton | ID | Görev |
|-------|-----|-------|
| **✅ Kodu Doğrula** | `verify-btn` | 6 haneli kodu doğrula → Profil tamamlama veya ana uygulamaya geç |

### Profil Tamamlama Ekranı

| Buton | ID | Görev |
|-------|-----|-------|
| **✅ Profili Tamamla** | `complete-profile-btn` | Ad Soyad + Müdürlük kaydet → Ana uygulamaya geç |

### Ana Uygulama Ekranı

| Buton | ID | Görev | Görünürlük |
|-------|-----|-------|------------|
| **🚪 Çıkış Yap** | `logout-btn` | Logout → Login ekranına dön | Her zaman |
| **🔄 Yenile** | `refresh-admin-btn` | İstatistikleri yeniden yükle | Admin only |
| **🚀 Yanıt Üret** | `generate-btn` | AI yanıtı üret | state=draft veya generated |
| **📋 Seç ve Kopyala** | `main-copy-btn` | Ana yanıtı kopyala | state=generated |
| **🆕 Yeni İstek Öneri Cevapla** | `new-request-btn` | Tüm alanları temizle, başa dön | state=generated |
| **📋 Seç ve Kopyala #1** | `prev-copy-btn-1` | 1. önceki yanıtı kopyala | yanitSayisi >= 2 |
| **📋 Seç ve Kopyala #2** | `prev-copy-btn-2` | 2. önceki yanıtı kopyala | yanitSayisi >= 3 |
| **📋 Seç ve Kopyala #3** | `prev-copy-btn-3` | 3. önceki yanıtı kopyala | yanitSayisi >= 4 |
| **📋 Seç ve Kopyala #4** | `prev-copy-btn-4` | 4. önceki yanıtı kopyala | yanitSayisi >= 5 |

---

## Accordion'lar

### Admin Panel (id="admin-panel")
- **Görünürlük:** Sadece `is_admin = true` kullanıcılar
- **İçerik:** 
  - Toplam Kullanıcı Sayısı
  - Toplam İstek Sayısı
  - Toplam Yanıt Sayısı
  - Kullanıcı Listesi (tablo)

### Yanıt Ayarları (id="response-settings")
- **Görünürlük:** Sadece `is_admin = true` kullanıcılar
- **İçerik:**
  - Model seçimi (dropdown)
  - Yaratıcılık (Temperature) slider
  - Maksimum Token Sayısı slider

### Önceki Yanıtlar (id="prev-accordion-1" ... "prev-accordion-4")
- **Görünürlük:** `yanitSayisi >= 2` olduğunda
- **İçerik:**
  - Önceki yanıt metni
  - "Seç ve Kopyala" butonu

---

## Troubleshooting

### 1. Magic Link Çalışmıyor

**Semptom:** Magic link'e tıklandığında `/?error=invalid_token` yönlendirmesi

**Olası Sebepler:**
1. Token süresi dolmuş (5 saat geçti)
2. Token veritabanında yok
3. Email'deki URL yanlış (`/auth` yerine `/magic-link` olmalı)

**Çözüm:**
```python
# auth_system.py içinde login_url kontrolü
login_url = f"{PRODUCTION_URL}/api/v1/magic-link?token={token}"
# PRODUCTION_URL .env'den okunur, /magic-link olmalı, /auth DEĞİL
```

---

### 2. Kod Girişi Sonrası Her Seferinde Profil Tamamlama Ekranı Geliyor

**Semptom:** Profil dolduruldu ama kod ile giriş yapıldığında tekrar profil tamamlama istiyor

**Olası Sebepler:**
1. `profile_completed` boolean olarak dönmüyor
2. Frontend'de `profile_completed` kontrolü yanlış
3. `CodeVerifyResponse` model'inde `department` eksik

**Çözüm:**
```python
# api_models.py
class CodeVerifyResponse(BaseModel):
    ...
    department: Optional[str] = None  # EKLE
    profile_completed: bool = False
```

```python
# auth_endpoints.py - verify_login_code()
return CodeVerifyResponse(
    ...
    department=user.department,  # EKLE
    profile_completed=user.profile_completed
)
```

---

### 3. Docker Container 502 Bad Gateway Hatası

**Semptom:** Cloudflare'den 502 Bad Gateway

**Olası Sebepler:**
1. Nginx yanlış port'ta dinliyor
2. FastAPI başlamadı
3. Port mapping yanlış
4. Nginx konfigürasyonu hatalı (circular proxy)

**Çözüm:**
```bash
# 1. Container loglarını kontrol et
docker logs ai_helper_container

# 2. Container içine gir
docker exec -it ai_helper_container bash

# 3. Port dinleme kontrolü
netstat -tuln | grep LISTEN
# → 0.0.0.0:80 (Nginx)
# → 0.0.0.0:8000 (FastAPI)

# 4. Nginx konfigürasyonu kontrolü
cat /etc/nginx/sites-available/default

# 5. Doğru nginx.conf:
server {
    listen 80;
    
    location / {
        root /usr/share/nginx/html;  # Static files
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://localhost:8000;  # FastAPI proxy
    }
}
```

---

### 4. Input Alanları Boş Gelmiyor

**Semptom:** Sayfa yüklendiğinde input alanlarında varsayılan metin var

**Çözüm:**
```javascript
// app.js - DOMContentLoaded event'inde
document.addEventListener('DOMContentLoaded', () => {
    ...
    clearTextboxValues();  // EKLE
});

function clearTextboxValues() {
    document.getElementById('original-text').value = '';
    document.getElementById('custom-input').value = '';
}
```

```html
<!-- index.html - textarea'larda placeholder kullan, value yok -->
<textarea id="original-text" placeholder="İstek/öneri metnini buraya yapıştırın..."></textarea>
<textarea id="custom-input" placeholder="Cevap taslağınızı buraya yazın..."></textarea>
```

---

### 5. Admin Paneli Görünmüyor

**Semptom:** Admin kullanıcı olmasına rağmen "İstatistikler" paneli görünmüyor

**Çözüm:**
```javascript
// app.js - showMainApp() fonksiyonu
showMainApp() {
    ...
    const isAdmin = localStorage.getItem('is_admin') === 'true';
    
    if (isAdmin) {
        document.getElementById('admin-panel').classList.remove('hidden');
        document.getElementById('response-settings').classList.add('hidden');
        this.updateAdminPanel();
    } else {
        document.getElementById('admin-panel').classList.add('hidden');
        document.getElementById('response-settings').classList.add('hidden');
    }
}
```

**Not:** "Yanıt Ayarları" accordion'u da sadece admin kullanıcılarda görünür.

---

### 6. AI Yanıtlar Çok Kısa Geliyor

**Semptom:** Üretilen yanıtlar beklenenden kısa (100-200 token)

**Çözüm:**
```python
# ollama_client.py
"num_predict": 4000  # Token limiti artır

# gemini_client.py
"maxOutputTokens": 4000  # Token limiti artır
```

---

### 7. Email Gönderilmiyor

**Semptom:** "Email gönderildi" mesajı geliyor ama email gelmiyor

**Olası Sebepler:**
1. SMTP ayarları yanlış
2. Gmail "Less secure app access" kapalı (2-factor auth gerekli)
3. SMTP_PASSWORD yanlış

**Çözüm:**
```bash
# .env dosyasını kontrol et
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@yourdomain.com
SMTP_PASSWORD=your-app-password  # NOT: Gmail app password, not regular password
SENDER_EMAIL=noreply@yourdomain.com
```

**Gmail App Password Oluşturma:**
1. Google Account → Security
2. 2-Step Verification → ON
3. App passwords → Generate
4. Uygulama: "Mail", Cihaz: "Other" → "AI Helper"
5. Üretilen 16 haneli şifreyi .env'ye ekle

---

### 8. Database Migration Gerekiyor

**Semptom:** Yeni bir alan eklendiğinde eski database'de hata

**Çözüm:**
```python
# Terminal'de
docker exec -it ai_helper_container bash

# Container içinde
python -c "
from connection import engine
from models import Base

# Tüm tabloları yeniden oluştur (DİKKAT: Veri kaybı)
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
"
```

**Daha güvenli yol (Alembic ile migration):**
```bash
pip install alembic
alembic init migrations
# migration dosyaları oluştur ve uygula
```

---

### 9. PostgreSQL'e Geçiş Sonrası Hatalar

**Semptom A (422 Missing Field):** `POST /api/v1/generate` çağrısı `request_id / model_name / custom_input` eksik uyarısı veriyor.

**Çözüm:** Frontend `generateResponse()` payload'unun bu alanları içerdiğini doğrulayın.

**Semptom B (500 NOT NULL violation):** `responses.temperature` için NOT NULL ihlali.

**Çözüm:** `endpoints.py` içinde response kaydederken `temperature`, `top_p`, `repetition_penalty` alanlarını da DB'ye yazıyoruz.

**Semptom C (duplicate key violates unique constraint responses_pkey):** Sequence geride kalmış.

**Çözüm (sequence düzeltme):**
```bash
python - << 'PY'
from sqlalchemy import create_engine, text
from config import DATABASE_URL
engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    for t in ['users','requests','responses','templates','template_categories','login_tokens','login_attempts','models']:
        seq = conn.execute(text("SELECT pg_get_serial_sequence(:t,'id')"), {'t': t}).scalar()
        if seq:
            max_id = conn.execute(text(f"SELECT COALESCE(MAX(id),0) FROM {t}")).scalar()
            conn.execute(text("SELECT setval(:s,:v,true)"), {'s': seq, 'v': max_id})
            print(t, '->', seq, '=', max_id)
PY
```

**Sayaçları yeniden oluşturma:**
```bash
python recompute_user_counters.py
```

---

## .env Dosyası Örneği

```env
# Production URLs
PRODUCTION_URL=https://your-production-domain.com
ALLOWED_ORIGINS=https://your-production-domain.com
FRONTEND_URL=http://localhost:8500
BACKEND_URL=http://localhost:8000

# Database (yalnızca PostgreSQL)
# 1) Doğrudan DSN
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME
# veya 2) POSTGRES_* değişkenleri ile otomatik DSN
POSTGRES_HOST=your-database-host
POSTGRES_PORT=5432
POSTGRES_DB=your-database-name
POSTGRES_USER=your-database-user
POSTGRES_PASSWORD=your-secure-password

# Ollama
OLLAMA_HOST=http://your-ollama-host:11434

# Gemini API
GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE
GEMINI_API_URL=http://generativelanguage.googleapis.com/v1beta/models

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-min-32-characters
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=900

# SMTP (Google Workspace)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@yourdomain.com
SMTP_PASSWORD=your-app-password
SENDER_EMAIL=noreply@yourdomain.com

# Rate Limiting
RATE_LIMIT_LOGIN_SECONDS=5
RATE_LIMIT_DAILY_LOGINS=50

# Debug
DEBUG_MODE=false
LOG_LEVEL=INFO
```

---

## Özet

1. **Backend:** FastAPI (Port 8000) - API endpoints, auth, business logic
2. **Frontend:** Nginx (Port 80) - Static files + API proxy
3. **Docker:** Port 8500 (host) → 80 (container)
4. **Authentication:** JWT + Magic Link (5h, reusable) + 6-digit Code (5h, single-use)
5. **AI Models:** Ollama (lokal) + Gemini (cloud), max 4000 tokens
6. **Database:** SQLite (User, LoginToken, LoginAttempt, Request, Response, Model, **Template, TemplateCategory**)
7. **Template Sistemi:** ⭐ Departman bazlı şablon paylaşımı, kategori yönetimi, güvenlik kontrolleri
8. **Admin Features:** İstatistikler, kullanıcı listesi, yanıt ayarları
9. **User Flow:** 
   - Email → Magic link/kod → Profil tamamlama (ilk giriş) → Ana uygulama
   - Gelen istek/öneri + Cevap taslağı → AI yanıt üret → **Şablon olarak kaydet** → Kopyala → Yeni istek
   - **Şablonlarım** → Arama/filtreleme → Şablon kullan → Yanıt alanına ekle

---

**Son Güncelleme:** 30 Ekim 2025
**Versiyon:** 1.1.2
**Değişiklikler:**
- PostgreSQL zorunlu hale getirildi (SQLite fallback kaldırıldı)
- `.env` önceliği ve `POSTGRES_*` ile otomatik DSN
- `generate` kaydı: `temperature/top_p/repetition_penalty` DB'ye yazılıyor
- PostgreSQL sequence düzeltme talimatı eklendi
- Sayaç geri doldurma aracı: `recompute_user_counters.py`

