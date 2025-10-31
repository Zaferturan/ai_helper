# 🤖✨ AI Yardımcı - Nilüfer Belediyesi 🏛️💫

<div align="center">

🎉🎊 **Vatandaş taleplerine profesyonel cevaplar hazırlayın!** 🎊🎉

![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&pause=1000&color=4B9AC7&center=true&vCenter=true&width=600&lines=🤖+AI+Destekli+Metin+D%C3%BCzenleme;⚡+Dinamik+Model+Se%C3%A7imi;🌐+Modern+Web+Aray%C3%BCz%C3%BC;🔐+G%C3%BCvenli+Authentication;📊+Ger%C3%A7ek+Zamanl%C4%B1+%C4%B0statistikler)

</div>

## 📸✨ Ekran Görüntüleri 🖼️🎨

### 🖥️💻 Ana Uygulama 🚀
![Ana Uygulama](./ekran%201.png)

### 📊📈 İstatistikler Paneli 📋
![İstatistikler](./istatistikler.png)

## ✨🎯 Özellikler 🚀💫

- 🤖✨ **AI Destekli Metin Düzenleme**: Gemini ve Ollama LLM modelleri ile metinleri daha kibar ve anlaşılır hale getirin
- ⚡🔥 **Dinamik Model Seçimi**: Mevcut modelleri otomatik olarak alır
- 🔄🎨 **İki Farklı Mod**: 
  - 📝✨ İstek/öneri metninden cevap üretme
  - ✏️🎯 Kendi yazdığınız cevabı iyileştirme
- 📊⚡ **Gerçek Zamanlı İstatistikler**: Üretim süresi, model adı, karakter sayısı
- 🗄️💾 **Veritabanı Entegrasyonu**: Tüm istekler ve yanıtlar SQLite'da saklanır
- 🌐🎨 **Modern Web Arayüzü**: HTML+CSS+JavaScript ile responsive tasarım
- 📋✨ **Yanıt Geçmişi**: Önceki yanıtları görüntüleme ve seçme
- 📋🎯 **Panoya Kopyalama**: JavaScript ile tek tıkla yanıt kopyalama
- ✅📊 **Yanıt Seçimi Takibi**: Hangi yanıtların seçildiğini veritabanında saklama
- ⚙️🎛️ **LLM Parametre Kontrolü**: Temperature, Top-p, Repetition Penalty ayarları
- 💡✨ **Tooltip Desteği**: Parametreler hakkında açıklayıcı bilgiler
- 🔐🛡️ **Güvenli Authentication**: Magic Link + OTP ile giriş sistemi
- 🏢🏛️ **Domain Kısıtlaması**: Sadece @nilufer.bel.tr e-posta adresleri
- 👤🎯 **Profil Yönetimi**: Ad soyad ve müdürlük bilgileri
- 🛡️⚡ **Rate Limiting**: Brute force koruması ve günlük limitler
- 🎨✨ **Modern UI/UX**: Gelişmiş gölge efektleri ve responsive tasarım
- 🐳🚀 **Docker Deployment**: Kolay kurulum ve deployment
- 👥📊 **Admin Paneli**: Kullanıcı istatistikleri ve yönetim

## 🛠️⚡ Teknolojiler 🚀💻

### 🐍🔥 Backend 🚀
- 🚀✨ **FastAPI**: Modern Python web framework
- 🗄️💾 **SQLAlchemy**: ORM ile veritabanı yönetimi
- 📊🗃️ **SQLite**: Ana veritabanı (production-ready)
- 🤖🧠 **Ollama**: Yerel LLM entegrasyonu
- 🧠✨ **Gemini API**: Google Gemini modelleri entegrasyonu
- ✅🎯 **Pydantic**: Veri doğrulama ve serileştirme
- 🔑🔐 **JWT**: JSON Web Token authentication
- 📧✉️ **SMTP**: E-posta gönderimi (Google Workspace)
- 🛡️⚡ **Rate Limiting**: Brute force koruması

### 🌐🎨 Frontend ✨
- 🌐💻 **HTML5 + CSS3 + JavaScript**: Modern web teknolojileri
- 📱🎯 **Responsive Design**: Mobil ve masaüstü uyumlu
- 🎨✨ **Modern UI**: Temiz ve kullanıcı dostu arayüz
- 🌐⚡ **Nginx**: Web server ve reverse proxy
- ✨🎨 **CSS Styling**: Özel tasarım ve gölge efektleri

### 🚀🐳 Deployment 🏭
- 🐳🚀 **Docker**: Containerization
- 🌐⚡ **Nginx**: Web server ve reverse proxy
- ☁️🌍 **Cloudflare**: CDN ve SSL sertifikası
- 💾🗃️ **Volume Mounting**: Veri ve log persistence

## 📋⚡ Gereksinimler 🛠️

- 🐳🚀 **Docker**
- 🐍✨ **Python 3.11+** (development için)
- 📊🗃️ **PostgreSQL** (zorunlu)

## 🚀✨ Kurulum 🎯

### 🐳🔥 Docker ile Hızlı Kurulum (Önerilen) ⚡

1. 📥✨ **Projeyi Klonlayın**
```bash
git clone <repository-url>
cd ai_helper
```

2. ⚙️🎯 **Ortam Değişkenlerini Ayarlayın**
`.env` dosyası oluşturun:
```env
# Database (PostgreSQL)
# 1) Doğrudan DSN
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME
# veya 2) POSTGRES_* değişkenleri (otomatik DSN)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ai_helper
POSTGRES_USER=ai_helper
POSTGRES_PASSWORD=your-password

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434

# Authentication Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=900

# SMTP Configuration (Google Workspace)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@niluferyapayzeka.tr
SMTP_PASSWORD=your-app-password
SENDER_EMAIL=admin@niluferyapayzeka.tr

# Gemini API Configuration
GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE

# Production URLs
PRODUCTION_URL=https://your-domain.com
FRONTEND_URL=http://localhost:8500
BACKEND_URL=http://localhost:8000
```

3. 🚀🎯 **Docker ile Başlatın**
```bash
# Image oluştur
docker build -t ai_helper_v3 .

# Container başlat
docker run -d --name ai_yardimci --restart always \
  -p 8000:8000 -p 8500:80 \
  -v ai_helper_data:/app/data \
  -v ai_helper_logs:/app/logs \
  ai_helper_v3
```

✅🎉 **Kurulum tamamlandı!** Uygulama production URL'de çalışıyor.

### 🔧⚡ Geliştirme Ortamı Kurulumu 🛠️

1. 🐍✨ **Sanal Ortam Oluşturun**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows
```

2. 📦🎯 **Bağımlılıkları Yükleyin**
```bash
pip install -r requirements.txt
```

3. 🚀⚡ **Backend'i Başlatın**
```bash
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 12000 --reload
```
Backend `http://localhost:12000` adresinde çalışacak.

4. 🌐🎨 **Frontend'i Başlatın**
```bash
cd frontend
python -m http.server 13000
```
Frontend `http://localhost:13000` adresinde çalışacak.

> Geliştirme sırasında cache'i yenilemek için `index.html` içindeki `app.js?v=...` sürümünü artırın ve sayfayı F5 ile yenileyin.

## 📖✨ Kullanım 🎯🚀

### 🎯⚡ Ana Özellikler 🚀

1. 📧✨ **E-posta ile Giriş**:
   - @nilufer.bel.tr e-posta adresinizi girin
   - E-posta adresinize gönderilen kodu girin
   - Profil bilgilerinizi tamamlayın

2. 🤖🎯 **İstek/Öneri Metninden Cevap Üretme**:
   - Sol sütunda metin girişi yapın
   - Yanıt ayarlarını düzenleyin (Temperature, Top-p, Repetition Penalty)
   - Model seçin (Gemini veya Ollama)
   - "🚀 Yanıt Üret" butonuna tıklayın

3. ✏️✨ **Kendi Cevabınızı İyileştirme**:
   - Sol sütunda kendi yazdığınız cevabı girin
   - "🚀 Yanıt Üret" butonuna tıklayın
   - AI metni daha kibar ve resmi hale getirecek

4. 📋🎯 **Yanıt Geçmişi ve Seçimi**:
   - Sağ sütunda en son yanıtı görüntüleyin
   - "📋 Seç ve Kopyala" ile yanıtı panoya kopyalayın
   - Önceki yanıtları expander'larda görüntüleyin
   - Her yanıt için ayrı "📋 Seç ve Kopyala" butonu

5. 👥📊 **Admin Paneli** (Admin kullanıcılar için):
   - Kullanıcı istatistikleri
   - Toplam istek ve yanıt sayıları
   - En çok kullanılan modeller

### 🔌⚡ API Endpoints 🚀

#### 🔐🛡️ Authentication 🔑
- 📧✨ `POST /api/v1/send`: Magic link ve OTP gönderimi
- ✅🎯 `POST /api/v1/verify-code`: OTP doğrulama
- 🔗⚡ `GET /api/v1/auth`: Magic link doğrulama
- 👤🎯 `GET /api/v1/profile`: Kullanıcı profili
- ✏️✨ `POST /api/v1/complete-profile`: Profil tamamlama
- 🚪🎯 `POST /api/v1/logout`: Çıkış yapma

#### 🤖🚀 Core API ⚡
- 📋🎯 `GET /api/v1/models`: Mevcut modelleri listele
- 📝✨ `POST /api/v1/requests`: Yeni istek oluştur
- 🚀⚡ `POST /api/v1/generate`: AI yanıtı üret
- 💬🎯 `POST /api/v1/responses/feedback`: Yanıt geri bildirimi

#### 👥📊 Admin API 🏛️
- 📊🎯 `GET /api/v1/admin/users`: Kullanıcı listesi
- 📈✨ `GET /api/v1/admin/stats`: İstatistikler

## 📁✨ Proje Yapısı 🗂️🚀

```
ai_helper/
├── 🐍 main.py               # FastAPI backend
├── ⚙️ config.py             # Konfigürasyon
├── 🔌 connection.py         # Veritabanı bağlantısı
├── 🗄️ models.py             # SQLAlchemy modelleri
├── 📋 api_models.py         # Pydantic modelleri
├── 🔌 endpoints.py          # API endpoint'leri
├── 🔐 auth_endpoints.py     # Authentication endpoints
├── 🔑 auth_system.py        # Authentication logic
├── 🤖 ollama_client.py      # Ollama entegrasyonu
├── 🧠 gemini_client.py      # Gemini API entegrasyonu
├── 📦 requirements.txt      # Python bağımlılıkları
├── 🐳 Dockerfile            # Docker container build
├── 🚀 start.sh              # Container startup script
├── 🌐 nginx.conf            # Nginx configuration
├── 📁 frontend/             # Frontend dosyaları
│   ├── 🌐 index.html        # Ana HTML dosyası
│   ├── 🎨 style.css         # CSS stilleri
│   └── ⚡ app.js            # JavaScript kodu
├── 💾 data/                 # Database storage directory
├── 📝 logs/                 # Log dosyaları
├── 🔧 .env                  # Ortam değişkenleri
├── 📖 README.md            # Bu dosya
└── 🗺️ ROADMAP.md           # Geliştirme yol haritası
```

## 🎯✨ Özellikler 🚀💫

### 🐍🔥 Backend Özellikleri 🚀
- 🚀✨ **FastAPI ile modern REST API**
- 🗄️💾 **SQLAlchemy ORM ile veritabanı yönetimi**
- 🤖🧠 **Ollama entegrasyonu**
- 🧠✨ **Gemini API entegrasyonu**
- ✅🎯 **Pydantic ile veri doğrulama**
- ⚡🔥 **Asenkron HTTP istekleri**
- 🛠️⚡ **Hata yönetimi ve logging**
- ⚙️🎛️ **LLM parametre kontrolü** (Temperature, Top-p, Repetition Penalty)
- 🔑🔐 **JWT tabanlı authentication sistemi**
- 🔗✨ **Magic Link + OTP giriş yöntemi**
- 🏢🏛️ **Domain kısıtlaması** (@nilufer.bel.tr)
- 🛡️⚡ **Rate limiting ve brute force koruması**
- 📧✉️ **SMTP entegrasyonu** (Google Workspace)
- 📝📊 **Login attempt logging**
- 🔐🎯 **Session yönetimi**
- 👥📊 **Admin paneli ve istatistikler**

### 🌐🎨 Frontend Özellikleri ✨
- 🌐💻 **HTML5 + CSS3 + JavaScript ile modern web arayüzü**
- 📱🎯 **Responsive tasarım** (mobil ve masaüstü uyumlu)
- ⚡🔥 **Dinamik model seçimi** (Gemini + Ollama)
- ⏱️⚡ **Gerçek zamanlı yanıt üretimi**
- 📊📈 **İstatistik gösterimi**
- 📋✨ **Yanıt geçmişi ve expander'lar**
- 📋🎯 **JavaScript ile panoya kopyalama**
- ✅📊 **Yanıt seçimi ve veritabanı takibi**
- 💡✨ **Tooltip desteği** (parametre açıklamaları)
- 🎨💫 **Modern CSS tasarım ve gölge efektleri**
- 🔐🛡️ **Authentication sistemi** (Magic Link + OTP)
- 👤🎯 **Profil tamamlama sayfası**
- 🏢🏛️ **Domain kontrolü** (@nilufer.bel.tr)
- 👥📊 **Admin paneli** (admin kullanıcılar için)
- ⏳⚡ **Loading states ve error handling**
- 🔄✨ **Cache-busting ile güncel dosya yükleme**

### 🚀🐳 Deployment Özellikleri 🏭
- 🐳🚀 **Docker containerization**
- 🌐⚡ **Nginx web server ve reverse proxy**
- 💾🗃️ **Database persistence with volumes**
- ❤️⚡ **Health checks**
- 🏭🎯 **Production-ready configuration**
- ☁️🌍 **Cloudflare CDN ve SSL sertifikası**
- 🔄⚡ **Automatic restart policy**
- ⚙️🎛️ **Environment variable management**
- 📝📊 **Log management**

## 🔧⚡ Geliştirme 🛠️🚀

### 🐳🔥 Docker ile Geliştirme ⚡
```bash
# Container'ı başlat
docker run -d --name ai_yardimci --restart always \
  -p 8000:8000 -p 8500:80 \
  -v ai_helper_data:/app/data \
  -v ai_helper_logs:/app/logs \
  ai_helper_v3

# Logları izle
docker logs -f ai_yardimci

# Container'a bağlan
docker exec -it ai_yardimci bash

# Container'ı durdur
docker stop ai_yardimci && docker rm ai_yardimci
```

### 💻✨ Yerel Geliştirme 🚀
```bash
# Backend'i geliştirme modunda başlat
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend'i geliştirme modunda başlat
cd frontend && python -m http.server 8500
```

### 🗄️📊 Veritabanı İşlemleri (PostgreSQL) 💾
PostgreSQL'e geçiş için `.env`:
```env
# 1) Doğrudan DSN (öncelikli)
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME

# veya 2) POSTGRES_* değişkenleri ile otomatik DSN
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ai_helper
POSTGRES_USER=ai_helper
POSTGRES_PASSWORD=your-password
```

`config.py` önceliği (yalnızca PostgreSQL):
1) `DATABASE_URL` (postgresql şeması)
2) `POSTGRES_*` → otomatik DSN
3) Aksi halde uygulama başlatılmaz (RuntimeError)
Sık karşılaşılan PostgreSQL sorunları ve çözümleri:

1) `422 Unprocessable Entity` (generate): Eksik alanlar. Frontend `request_id`, `model_name`, `custom_input` gönderdiğinden emin olun.

2) `NOT NULL violation: responses.temperature` (generate): `endpoints.py` DB kaydı artık `temperature/top_p/repetition_penalty` alanlarını da yazar. Kodu güncellediyseniz sorun çözülür.

3) `duplicate key value violates unique constraint responses_pkey`: Sequence geride kaldı. Aşağıdaki tek seferlik düzeltmeyi uygulayın:
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

4) İstatistik sayaçları sıfır görünüyor: Mevcut veriden geri doldurun:
```bash
python recompute_user_counters.py
```

## 📊💾 Veritabanı Şeması 🗃️✨

### 👤🎯 Users Tablosu 👥
- 🔑✨ `id`: Birincil anahtar
- 📧✉️ `email`: E-posta adresi (unique, @nilufer.bel.tr)
- 👤🎯 `full_name`: Ad soyad
- 🏢🏛️ `department`: Müdürlük bilgisi
- ✅⚡ `is_active`: Aktif kullanıcı durumu
- 📅📊 `created_at`: Oluşturulma tarihi
- 🔐🎯 `last_login`: Son giriş tarihi
- ✅✨ `profile_completed`: Profil tamamlanma durumu
- 👑🏛️ `is_admin`: Admin yetkisi

### 🔑🛡️ LoginTokens Tablosu 🔐
- 🔑✨ `id`: Birincil anahtar
- 👤🎯 `user_id`: Kullanıcı referansı
- 📧✉️ `email`: E-posta adresi
- 🔐⚡ `token_hash`: Token hash'i
- 🔢🎯 `code_hash`: OTP kodu hash'i
- ⏰📊 `expires_at`: Son kullanım tarihi
- ✅✨ `used_at`: Kullanım tarihi
- 🌐🎯 `ip_created`: Oluşturulma IP'si
- 🖥️💻 `user_agent_created`: User agent
- 🔢📊 `attempt_count`: Deneme sayısı
- ⏰⚡ `last_attempt_at`: Son deneme tarihi

### 📝📊 LoginAttempts Tablosu 🔐
- 🔑✨ `id`: Birincil anahtar
- 👤🎯 `user_id`: Kullanıcı referansı
- 📧✉️ `email`: E-posta adresi
- 🌐🎯 `ip_address`: IP adresi
- ✅⚡ `success`: Başarı durumu
- 🔐🛡️ `method`: Giriş yöntemi (magic_link, otp)
- ⏰📊 `timestamp`: Zaman damgası

### 📋🎯 Requests Tablosu 📝
- 🔑✨ `id`: Birincil anahtar
- 👤🎯 `user_id`: Kullanıcı referansı
- 📝📊 `original_text`: Orijinal metin
- 🎯⚡ `response_type`: Yanıt tipi (positive/negative/informative/other)
- 📅📊 `created_at`: Oluşturulma tarihi
- ✅⚡ `is_active`: Aktif durum
- 🔢📊 `remaining_responses`: Kalan yanıt sayısı
- 🆕✨ `is_new_request`: Yeni istek durumu

### 💬🤖 Responses Tablosu 🚀
- 🔑✨ `id`: Birincil anahtar
- 📋🎯 `request_id`: İstek referansı
- 🤖🧠 `model_name`: Kullanılan model
- 💬📊 `response_text`: AI yanıtı
- 🌡️🎛️ `temperature`: Temperature parametresi
- 📊⚡ `top_p`: Top-p parametresi
- 🔄🎯 `repetition_penalty`: Repetition penalty parametresi
- ⏱️📊 `latency_ms`: Üretim süresi
- ✅🎯 `is_selected`: Seçilme durumu
- 📋✨ `copied`: Kopyalanma durumu
- 📅📊 `created_at`: Oluşturulma tarihi
- 🔢📊 `tokens_used`: Kullanılan token sayısı

### 🤖🧠 Models Tablosu ⚡
- 🔑✨ `id`: Birincil anahtar
- 🤖🎯 `name`: Model adı
- 🏷️✨ `display_name`: Görünen ad
- 🔗🎯 `supports_embedding`: Embedding desteği
- 💬⚡ `supports_chat`: Chat desteği

## 🚀🏭 Deployment 🐳⚡

### 🏭🎯 Production Ortamı 🚀
1. 🐳🚀 **Docker**: Containerization
2. 🗄️💾 **Database**: PostgreSQL
3. 🌐⚡ **Frontend**: Nginx (port 80)
4. 🚀🔥 **Backend**: FastAPI (port 8000)
5. ☁️🌍 **Cloudflare**: CDN ve SSL sertifikası

### 🐳⚡ Docker Commands 🚀
```bash
# Production deployment
docker build -t ai_helper_v3 .
docker run -d --name ai_yardimci --restart always \
  -p 8000:8000 -p 8500:80 \
  -v ai_helper_data:/app/data \
  -v ai_helper_logs:/app/logs \
  ai_helper_v3

# Logları izle
docker logs -f ai_yardimci

# Container durumunu kontrol et
docker ps

# Health check
curl https://yardimci.niluferyapayzeka.tr/api/v1/auth/health

# Container'ı yeniden başlat
docker restart ai_yardimci

# Container'ı durdur
docker stop ai_yardimci && docker rm ai_yardimci
```

### ⚙️🎛️ Environment Variables 🔧
```bash
# Production environment
APP_ENV=production
DEBUG_MODE=false
LOG_LEVEL=INFO
API_PORT=8000
WEB_PORT=80
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME
ALLOWED_ORIGINS=https://yardimci.niluferyapayzeka.tr
```

## 🤝✨ Katkıda Bulunma 🚀💫

1. 🍴🎯 **Fork yapın**
2. 🌿✨ **Feature branch oluşturun** (`git checkout -b feature/amazing-feature`)
3. 💾⚡ **Commit yapın** (`git commit -m 'Add amazing feature'`)
4. 📤🚀 **Push yapın** (`git push origin feature/amazing-feature`)
5. 🔄🎯 **Pull Request oluşturun**

## 📝✨ Lisans 📄🎯

📄🎉 **Bu proje MIT lisansı altında lisanslanmıştır.** 🎉📄

## 📞 İletişim

<div align="center">

| 👨‍💻 **Geliştirici** |
|:---:|
| ![Zafer Turan](https://avatars.githubusercontent.com/u/10232886?v=4) |
| **Zafer Turan** |
| 🐙 [GitHub](https://github.com/Zaferturan) |
| 💼 [LinkedIn](https://www.linkedin.com/in/zafer-turan-224854183/) |
| 🏆 [HackerRank](https://www.hackerrank.com/profile/zaferturan) |
| 📧 [zaferturan@gmail.com](mailto:zaferturan@gmail.com) |

</div>

## 🔄✨ Güncellemeler 🚀💫

### 🎨🔥 v2.0.0 - Modern Web Arayüzü ✨
- 🌐💻 **HTML5 + CSS3 + JavaScript ile modern web arayüzü**
- 🌐⚡ **Nginx web server ve reverse proxy**
- 📱🎯 **Responsive tasarım** (mobil ve masaüstü uyumlu)
- 👥📊 **Admin paneli ve istatistikler**
- ⏳⚡ **Loading states ve error handling**
- 🔄✨ **Cache-busting ile güncel dosya yükleme**
- 💾🗃️ **Docker volume mounting ile veri persistence**
- 🏭🎯 **Production-ready deployment**

### 🐳🚀 v1.7.0 - Docker Compose Deployment ⚡
- 🐳🔥 **Docker Compose multi-service orchestration**
- 🗄️💾 **Database persistence with SQLite**
- 🏭🎯 **Production-ready containerization**
- ❤️⚡ **Health checks and monitoring**
- ☁️🌍 **Cloudflare Tunnel integration**
- 🔄⚡ **Automatic restart policy**
- ⚙️🎛️ **Environment variable management**
- 🚀✨ **Multi-service startup script**

### 🔐🛡️ v1.6.0 - Authentication System 🔑
- 🔑🔐 **JWT tabanlı authentication sistemi**
- 🔗✨ **Magic Link + OTP giriş yöntemi**
- 🏢🏛️ **Domain kısıtlaması** (@nilufer.bel.tr)
- 👤🎯 **Profil yönetimi** (ad soyad, müdürlük)
- 🛡️⚡ **Rate limiting ve brute force koruması**
- 📧✉️ **SMTP entegrasyonu** (Google Workspace)
- 📝📊 **Login attempt logging**
- 🔐🎯 **Session yönetimi**
- ☁️🌍 **Production URL desteği** (Cloudflare Tunnel)
- 🎨💫 **Modern UI/UX ve gelişmiş gölge efektleri**

### 🔐🛡️ v1.5.0 - Security & Profile 🔑
- 🔐✨ **Authentication sistemi entegrasyonu**
- 👤🎯 **Kullanıcı profil yönetimi**
- 🛡️⚡ **Güvenlik önlemleri ve rate limiting**
- 📧✉️ **E-posta gönderim sistemi**

### 🎨✨ v1.4.0 - UI/UX Improvements 💫
- 📐🎯 **İki sütunlu modern layout**
- 📋✨ **Yanıt geçmişi ve expander'lar**
- 📋🎯 **JavaScript ile panoya kopyalama**
- ✅📊 **Yanıt seçimi veritabanı takibi**
- ⚙️🎛️ **LLM parametre kontrolü** (Temperature, Top-p, Repetition Penalty)
- 💡✨ **Tooltip desteği**
- 🎨💫 **Modern CSS tasarım**

### 🧠🤖 v1.3.0 - AI Model Integration ⚡
- 🧠✨ **Gemini API entegrasyonu**
- 🤖🔥 **Çoklu model desteği** (Gemini + Ollama)
- 🔍🎯 **Model filtreleme ve varsayılan seçim**
- ⚙️🎛️ **Sistem prompt yönetimi**
- 🔢📊 **Token limit optimizasyonu**

### 🐳🚀 v1.2.0 - Docker Deployment ⚡
- 🐳🔥 **Docker containerization**
- 🔄⚡ **Always restart policy**
- ⚙️🎯 **Varsayılan ayarlar güncellendi**
- 🔧✨ **Environment variables düzeltildi**

### 🤖🧠 v1.1.0 - Ollama Integration ⚡
- 🤖✨ **Ollama entegrasyonu**
- 🔄🔥 **Çoklu model desteği**
- 🎯⚡ **Gelişmiş model seçimi**

### 🚀✨ v1.0.0 - Initial Release 🎉
- 🚀🔥 **Temel FastAPI backend**
- 🌐💻 **Streamlit frontend**
- 🤖🧠 **Ollama entegrasyonu**
- 🗄️💾 **SQLite veritabanı**
- 🔄🎯 **İki farklı kullanım modu**

### 🔮✨ Gelecek Sürümler 🚀
- 🔄⚡ **CI/CD pipeline**
- 📊📈 **Advanced monitoring**
- 🌍🎯 **Multi-language support**
- 🛡️⚡ **API rate limiting**
- 📱💻 **Mobile app**
- 📈📊 **Advanced analytics**

---

<div align="center">

**🤖✨ AI Yardımcı** - Nilüfer Belediyesi için profesyonel cevaplar hazırlayın! 🎉🎊

🚀💫 **Hayal Et, Tasarla, Kodla!** 💫🚀

</div>