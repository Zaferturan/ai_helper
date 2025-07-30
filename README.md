# 🤖 AI Helper

Vatandaş taleplerine cevaplarınızı hazırlayın. İstek ve önerilere uygun, resmi ve anlaşılır cevaplar oluşturun.

## ✨ Özellikler

- **AI Destekli Metin Düzenleme**: Ollama ve Gemini LLM modelleri ile metinleri daha kibar ve anlaşılır hale getirin
- **Dinamik Model Seçimi**: Ollama ve Gemini'dan mevcut modelleri otomatik olarak alır
- **İki Farklı Mod**: 
  - İstek/öneri metninden cevap üretme
  - Kendi yazdığınız cevabı iyileştirme
- **Gerçek Zamanlı İstatistikler**: Üretim süresi, model adı, karakter sayısı
- **Veritabanı Entegrasyonu**: Tüm istekler ve yanıtlar MySQL'de saklanır

## 🛠️ Teknolojiler

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM ile veritabanı yönetimi
- **MySQL**: Ana veritabanı
- **Ollama**: Yerel LLM entegrasyonu
- **Gemini API**: Google Gemini LLM entegrasyonu
- **Pydantic**: Veri doğrulama ve serileştirme

### Frontend
- **Streamlit**: Python tabanlı web uygulaması
- **Responsive Design**: Mobil ve masaüstü uyumlu
- **Modern UI**: Temiz ve kullanıcı dostu arayüz

## 📋 Gereksinimler

- Python 3.10+
- MySQL Server
- Ollama (yerel LLM platformu)

## 🚀 Kurulum

### 1. Projeyi Klonlayın
```bash
git clone <repository-url>
cd ai_helper
```

### 2. Sanal Ortam Oluşturun
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows
```

### 3. Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

### 4. Ortam Değişkenlerini Ayarlayın
`.env` dosyası oluşturun:
```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=ai_helper
MYSQL_USER=root
MYSQL_PASSWORD=your_password

REDIS_HOST=localhost
REDIS_PORT=6379

OLLAMA_HOST=http://localhost:11434

# Gemini API (İsteğe bağlı)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_API_URL=https://generativelanguage.googleapis.com/v1beta/models
```

### 5. Veritabanını Oluşturun
```sql
CREATE DATABASE ai_helper;
```

### 6. Backend'i Başlatın
```bash
python main.py
```
Backend `http://localhost:8000` adresinde çalışacak.

### 7. Frontend'i Başlatın
```bash
streamlit run app.py
```
Frontend `http://localhost:8501` adresinde çalışacak.

## 📖 Kullanım

### Ana Özellikler

1. **İstek/Öneri Metninden Cevap Üretme**:
   - Sol sütunda metin girişi yapın
   - Geri dönüş tipini seçin (Pozitif/Negatif/Bilgilendirici/Diğer)
   - Model seçin
   - "Yanıt Üret" butonuna tıklayın

2. **Kendi Cevabınızı İyileştirme**:
   - Sağ sütunda kendi yazdığınız cevabı girin
   - "Metnimi İyileştir" butonuna tıklayın
   - AI metni daha kibar ve resmi hale getirecek

### API Endpoints

- `GET /api/v1/models`: Mevcut modelleri listele
- `POST /api/v1/requests`: Yeni istek oluştur
- `POST /api/v1/generate`: AI yanıtı üret
- `POST /api/v1/responses/feedback`: Yanıt geri bildirimi

## 📁 Proje Yapısı

```
ai_helper/
├── app.py                 # Streamlit frontend
├── main.py               # FastAPI backend
├── config.py             # Konfigürasyon
├── connection.py         # Veritabanı bağlantısı
├── models.py             # SQLAlchemy modelleri
├── api_models.py         # Pydantic modelleri
├── endpoints.py          # API endpoint'leri
├── ollama_client.py      # Ollama entegrasyonu
├── gemini_client.py      # Gemini API entegrasyonu
├── requirements.txt      # Python bağımlılıkları
├── .env                  # Ortam değişkenleri
├── .gitignore           # Git ignore kuralları
├── README.md            # Bu dosya
└── ROADMAP.md           # Geliştirme yol haritası
```

## 🎯 Özellikler

### Backend Özellikleri
- ✅ FastAPI ile modern REST API
- ✅ SQLAlchemy ORM ile veritabanı yönetimi
- ✅ Ollama entegrasyonu
- ✅ Gemini API entegrasyonu
- ✅ Pydantic ile veri doğrulama
- ✅ Asenkron HTTP istekleri
- ✅ Hata yönetimi ve logging

### Frontend Özellikleri
- ✅ Streamlit ile modern web arayüzü
- ✅ İki sütunlu responsive layout
- ✅ Dinamik model seçimi
- ✅ Gerçek zamanlı yanıt üretimi
- ✅ İstatistik gösterimi
- ✅ Kopyalama ve seçim butonları

## 🔧 Geliştirme

### Backend Geliştirme
```bash
# Backend'i geliştirme modunda başlat
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Geliştirme
```bash
# Streamlit'i geliştirme modunda başlat
streamlit run app.py --server.port 8501
```

### Veritabanı İşlemleri
```bash
# Tabloları oluştur
python -c "from connection import engine; from models import Base; Base.metadata.create_all(engine)"
```

## 📊 Veritabanı Şeması

### Requests Tablosu
- `id`: Birincil anahtar
- `original_text`: Orijinal metin
- `response_type`: Yanıt tipi (positive/negative/informative/other)
- `created_at`: Oluşturulma tarihi

### Responses Tablosu
- `id`: Birincil anahtar
- `request_id`: İstek referansı
- `model_name`: Kullanılan model
- `response_text`: AI yanıtı
- `latency_ms`: Üretim süresi
- `is_selected`: Seçilme durumu
- `copied`: Kopyalanma durumu
- `created_at`: Oluşturulma tarihi

### Models Tablosu
- `id`: Birincil anahtar
- `name`: Model adı
- `display_name`: Görünen ad
- `supports_embedding`: Embedding desteği
- `supports_chat`: Chat desteği

## 🚀 Deployment

### Production Ortamı
1. **Backend**: Gunicorn ile FastAPI'yi çalıştırın
2. **Frontend**: Streamlit Cloud veya kendi sunucunuzda
3. **Veritabanı**: MySQL production sunucusu
4. **Ollama**: Production sunucusunda Ollama kurulumu

### Docker (Gelecek)
```bash
# Docker Compose ile tüm servisleri başlat
docker-compose up -d
```

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## 📝 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 📞 İletişim

* **Proje Sahibi**: Zafer TURAN
* **E-posta**: zaferturan@gmail.com
* **GitHub**: @Zaferturan
* **Issues**: GitHub Issues

## 🔄 Güncellemeler

### v1.1.0
- ✅ Gemini API entegrasyonu
- ✅ Çoklu model desteği (Ollama + Gemini)
- ✅ Gelişmiş model seçimi
- ✅ API key yönetimi

### v1.0.0
- ✅ Temel FastAPI backend
- ✅ Streamlit frontend
- ✅ Ollama entegrasyonu
- ✅ MySQL veritabanı
- ✅ İki farklı kullanım modu

### Gelecek Sürümler
- 🔄 Authentication sistemi
- 🔄 Gelişmiş metrikler
- 🔄 Docker containerization
- 🔄 CI/CD pipeline
- 🔄 API rate limiting

---

**AI Helper** - Vatandaş taleplerine profesyonel cevaplar hazırlayın! 🤖 