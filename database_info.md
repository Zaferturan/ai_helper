# AI Helper Veritabanı Bilgileri

## 📊 Genel İstatistikler
- **Toplam Kullanıcı**: 6 kişi (boş kullanıcılar silindi)
- **Toplam İstek**: 186 adet
- **Toplam Yanıt**: 224 adet
- **Aktif Kullanıcılar**: 6 kişi

## 🗄️ Veritabanı Tabloları

### 1. `users` Tablosu - Kullanıcı Bilgileri
| Alan | Tip | Açıklama |
|------|-----|----------|
| id | Integer | Benzersiz kullanıcı kimliği (Primary Key) |
| email | String(255) | E-posta adresi (Unique, Index) |
| full_name | String(255) | Ad soyad |
| department | String(255) | Müdürlük bilgisi |
| is_active | Boolean | Aktif kullanıcı mı? (Default: True) |
| created_at | DateTime | Kayıt tarihi (Timezone aware) |
| last_login | DateTime | Son giriş tarihi (Nullable) |
| profile_completed | Boolean | Profil tamamlandı mı? (Default: False) |
| is_admin | Boolean | Admin yetkisi var mı? (Default: False) |

### 2. `requests` Tablosu - Kullanıcı İstekleri
| Alan | Tip | Açıklama |
|------|-----|----------|
| id | Integer | İstek kimliği (Primary Key) |
| user_id | Integer | Hangi kullanıcının isteği (Foreign Key) |
| original_text | Text | Orijinal metin |
| response_type | String(50) | Yanıt türü |
| created_at | DateTime | Oluşturulma tarihi |
| is_active | Boolean | Aktif istek mi? |
| remaining_responses | Integer | Kalan yanıt hakkı |
| is_new_request | Boolean | Yeni istek öneri mi? (Default: False) |

### 3. `responses` Tablosu - AI Yanıtları
| Alan | Tip | Açıklama |
|------|-----|----------|
| id | Integer | Yanıt kimliği (Primary Key) |
| request_id | Integer | Hangi isteğe ait (Foreign Key) |
| model_name | String(100) | Hangi AI modeli (Foreign Key) |
| response_text | Text | Yanıt metni |
| temperature | Float | AI parametresi |
| top_p | Float | AI parametresi |
| repetition_penalty | Float | AI parametresi |
| latency_ms | Integer | Yanıt süresi (ms) |
| is_selected | Boolean | Seçildi mi? (Default: False) |
| copied | Boolean | Kopyalandı mı? (Default: False) |
| created_at | DateTime | Oluşturulma tarihi |
| tokens_used | Integer | Kullanılan token sayısı |

### 4. `login_attempts` Tablosu - Giriş Denemeleri
| Alan | Tip | Açıklama |
|------|-----|----------|
| id | Integer | Deneme kimliği (Primary Key) |
| user_id | Integer | Kullanıcı kimliği (Foreign Key, Nullable) |
| email | String(255) | E-posta (Index) |
| ip_address | String(45) | IP adresi (IPv6 desteği) |
| success | Boolean | Başarılı mı? |
| method | String(50) | Giriş yöntemi (token/code) |
| timestamp | DateTime | Deneme zamanı |

### 5. `login_tokens` Tablosu - Giriş Tokenları
| Alan | Tip | Açıklama |
|------|-----|----------|
| id | Integer | Token kimliği (Primary Key) |
| user_id | Integer | Kullanıcı kimliği (Foreign Key, Nullable) |
| email | String(255) | E-posta (Index) |
| token_hash | String(255) | Token hash'i (Index) |
| code_hash | String(255) | 6 haneli kod hash'i (Index) |
| expires_at | DateTime | Son kullanma tarihi (Index) |
| used_at | DateTime | Kullanıldığı zaman (Nullable) |
| ip_created | String(45) | Oluşturulduğu IP |
| user_agent_created | String(500) | Oluşturulduğu user agent |
| attempt_count | Integer | Deneme sayısı (Default: 0) |
| last_attempt_at | DateTime | Son deneme zamanı (Nullable) |

### 6. `models` Tablosu - AI Modelleri
| Alan | Tip | Açıklama |
|------|-----|----------|
| id | Integer | Model kimliği (Primary Key) |
| name | String(100) | Model adı (Unique) |
| display_name | String(200) | Görünen ad |
| supports_embedding | Boolean | Embedding desteği (Default: False) |
| supports_chat | Boolean | Chat desteği (Default: False) |

## 👥 Aktif Kullanıcılar

| ID | Ad Soyad | E-posta | Müdürlük | Admin | Toplam Yanıt | Cevaplanan İstek |
|----|----------|---------|----------|-------|--------------|------------------|
| 1 | zafer turan | zaferturan@nilufer.bel.tr | Bilgi İşlem Müdürlüğü | ✅ | 144 | 36 |
| 3 | Mesut SOLAKLAR | mesut.solaklar@niluferyapayzeka.tr | Bilgi İşlem Müdürlüğü | ❌ | 13 | 7 |
| 5 | Hakan ULUCAN | hakan.ulucan@niluferyapayzeka.tr | İnsan Kaynakları Müdürlüğü | ❌ | 14 | 9 |
| 6 | öznur avdal | oznur.avdal@niluferyapayzeka.tr | Mali Hizmetler Müdürlüğü | ❌ | 11 | 6 |
| 7 | DENİZ ŞANLI | deniz.sanli@niluferyapayzeka.tr | Plan ve Proje Müdürlüğü | ❌ | 20 | 10 |
| 8 | engin akyıldız | engin.akyildiz@niluferyapayzeka.tr | Kültür ve Sosyal İşler Müdürlüğü | ❌ | 14 | 8 |

## 🔗 Tablo İlişkileri

- **users** → **requests** (1:N) - Bir kullanıcının birden fazla isteği olabilir
- **users** → **login_attempts** (1:N) - Bir kullanıcının birden fazla giriş denemesi olabilir
- **users** → **login_tokens** (1:N) - Bir kullanıcının birden fazla token'ı olabilir
- **requests** → **responses** (1:N) - Bir isteğin birden fazla yanıtı olabilir
- **models** → **responses** (1:N) - Bir modelin birden fazla yanıtı olabilir

## 📈 Performans İndeksleri

### login_attempts Tablosu
- `idx_login_attempts_email_timestamp` - E-posta ve zaman bazlı arama
- `idx_login_attempts_ip_timestamp` - IP ve zaman bazlı arama

### login_tokens Tablosu
- `idx_login_tokens_token_hash` - Token hash arama
- `idx_login_tokens_code_hash` - Kod hash arama
- `idx_login_tokens_expires` - Son kullanma tarihi arama
- `idx_login_tokens_email` - E-posta arama

## 🗑️ Silinen Kullanıcılar (2025-09-08)

Aşağıdaki boş kullanıcılar veritabanından silinmiştir:

| ID | E-posta | Ad Soyad | Müdürlük |
|----|---------|----------|----------|
| 9 | test@nilufer.bel.tr | (boş) | (boş) |
| 10 | enginakyildiz@nilufer.bel.tr | (boş) | (boş) |
| 11 | zaefrturan@nilufer.bel.tr | (boş) | (boş) |
| 12 | zafertuan@nilufer.bel.tr | (boş) | (boş) |

## 📝 Notlar

- Veritabanı SQLite kullanıyor
- Tüm tarih alanları timezone-aware
- Foreign key ilişkileri aktif
- Performans için gerekli indeksler mevcut
- Admin paneli gerçek zamanlı veri çekiyor
