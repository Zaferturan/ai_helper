# 🧩 ŞABLONLAR ÖZELLİĞİ GELİŞTİRME PLANI

## 🎯 Amaç

AI Helper sistemine "şablonlar" özelliği eklenerek, kullanıcıların sık kullanılan yanıt metinlerini **kaydedip yeniden kullanabilmeleri** sağlanacaktır.

- Kullanıcılar ürettikleri yanıtlardan istediklerini **şablon olarak saklayabilecekler**.  
- Aynı müdürlükteki herkes, o müdürlüğe ait şablonları görebilecek.  
- Her şablon bir **kategori**ye ait olacak; kategoriler kullanıcılar tarafından yönetilecek.  
- Şablonlar sayfasında kategoriye göre filtreleme, arama, kopyalama ve “kullan” (yanıt alanına ekleme) işlemleri yapılabilecek.

---

## ⚙️ Genel Kurallar ve Mimari Kararlar

- **Erişim:** Şablonları yalnızca **aynı müdürlükteki kullanıcılar** görebilir.  
- **Sahiplik:** Sadece şablonu oluşturan kullanıcı (ve admin) silebilir.  
- **Kategoriler:** Kullanıcı tarafından oluşturulabilir ve silinebilir.  
- **Veri saklama:** Yalnızca “şablon olarak kaydet” işaretli yanıtlar veritabanında saklanır.  
- **Arama:** Başlangıçta istemci tarafında, ileride FTS5 desteği eklenebilir.  
- **Departman izolasyonu:** Backend tüm filtreleri kullanıcının department bilgisine göre uygular.

---

## 🧱 ADIM 1 — Mimari Tanımlama

**Amaç:**  
Şablonların hangi kurallarla paylaşılacağı ve saklanacağı belirlenir.

**Yapılacaklar:**
- Departman bazlı görünürlük ve sahiplik kuralları oluşturulacak.  
- Magic link & JWT sisteminde mevcut kullanıcı department bilgisi kullanılacak.  
- Admin kullanıcılar tüm şablonları görebilecek.

**Kabul Kriterleri:**
- Kullanıcı yalnızca kendi departmanına ait şablonları görebilir.  
- Admin her departmanı görüntüleyebilir.

**Test:**
- A departmanı kullanıcısı → B departmanı şablonlarını göremez.  
- Admin → Tüm departman şablonlarını görebilir.

---

## 🗄️ ADIM 2 — Veritabanı Genişletme

**Amaç:**  
Şablon ve kategori tablolarının oluşturulması.

**Yapılacaklar:**
- Yeni tablolar:
  - `template_categories (id, name, department, owner_user_id, created_at)`
  - `templates (id, title, content, department, owner_user_id, category_id, created_at, updated_at, is_active)`
- Unique constraint: `(name, department)`  
- Soft delete: `is_active = false` olarak işaretleme.

**Kabul Kriterleri:**
- Tablolar başarıyla oluşturulur.
- Veri kaybı yaşanmaz.

**Test:**
- Migration sonrası tablo yapıları doğrulanır.
- Insert/update/delete işlemleri hatasızdır.

---

## 🧩 ADIM 3 — Backend API (Şablonlar)

**Amaç:**  
Kullanıcıların şablon oluşturma, listeleme ve silme işlemlerini yapabilmesi.

**Yapılacaklar:**
- Yeni uçlar eklenecek:
  - `GET /api/v1/templates?q=&category_id=&only_mine=&limit=&offset=`
  - `POST /api/v1/templates`
  - `DELETE /api/v1/templates/{id}`
- `title` boşsa ilk 80 karakterden otomatik üretilecek.
- Tüm isteklerde JWT zorunlu.

**Kabul Kriterleri:**
- Arama hem başlıkta hem içerikte yapılır.
- Departman dışı erişimler 403 döner.

**Test:**
- Listeleme + filtreleme + silme test edilir.
- Yetkisiz silme denemesi 403 döner.

---

## 🗂️ ADIM 4 — Backend API (Kategoriler)

**Amaç:**  
Kategorilerin kullanıcı tarafından yönetilebilmesi.

**Yapılacaklar:**
- Yeni uçlar:
  - `GET /api/v1/categories`
  - `POST /api/v1/categories`
  - `DELETE /api/v1/categories/{id}`
- Silme davranışı: içinde şablon varsa engellenecek (ileride “boşalt” seçeneği eklenebilir).

**Kabul Kriterleri:**
- Aynı isim aynı departmanda tekrar edemez.
- Kullanıcı yalnızca kendi kategorisini silebilir.

**Test:**
- Aynı departmanda aynı isimde kategori eklenemiyor.
- Başka kullanıcının kategorisi silinemiyor.

---

## 🧭 ADIM 5 — Navigasyon (Yeni Ekranlar)

**Amaç:**  
Kullanıcı “Şablonlarım” sayfasına geçiş yapabilmeli.

**Yapılacaklar:**
- Navbar’a iki yeni buton eklenecek:
  - **🏠 Ana Sayfa**
  - **📂 Şablonlarım**
- “Şablonlarım” butonu yeni bir `section id="templates-screen"` ekranını açacak.
- “Ana Sayfa” butonu üretim ekranına geri dönecek.

**Kabul Kriterleri:**
- Ekran geçişleri SPA içinde yapılır.
- State kaybı olmaz.

**Test:**
- Şablonlarım sayfasına gidip geri dönüldüğünde oturum korunur.

---

## 💾 ADIM 6 — “Şablonlarım” Ekranı Tasarımı

**Amaç:**  
Kullanıcı arayüzünde şablonların görüntülenmesi ve filtrelenmesi.

**Yapılacaklar:**
- Sol panel:
  - Kategori dropdown
  - “Sadece Benimkiler” toggle
  - Arama kutusu (yazdıkça filtre)
- Sağ panel:
  - Şablon kartları (başlık, kategori etiketi, içerik özeti, tarih, sahibi)
  - Aksiyonlar: **Kullan**, **Kopyala**, **Sil**
  - “Kullan” → modal: “Gelen İstek” / “Cevap Taslağı” / “Panoya kopyala”

**Kabul Kriterleri:**
- Filtreler etkileşimli çalışır.
- Modal seçimleri doğru alana içerik taşır.

**Test:**
- Arama + kategori + toggle birlikte çalışıyor.
- “Kullan” seçimi doğru textarea’ya aktarılıyor.

---

## 📋 ADIM 7 — “Seç ve Kopyala” Akışına Şablon Kaydet Ekleme

**Amaç:**  
Üretilen yanıtın kolayca şablon olarak kaydedilebilmesi.

**Yapılacaklar:**
- “Son Yanıt” paneline `☑ Şablon olarak sakla` checkbox eklenecek.
- Seçiliyse kategori dropdown ve “➕ Yeni Kategori” butonu açılacak.
- “Seç ve Kopyala” tıklanınca:
  - Kategori seçili değilse uyarı.
  - Seçiliyse `POST /templates` → başarı mesajı.

**Kabul Kriterleri:**
- Kategori seçimi zorunludur.
- Başarılı kayıtta toast bildirimi çıkar.

**Test:**
- Şablon kaydı sonrasında listeye eklenir.
- Kategori seçilmeden kayda izin verilmez.

---

## 🔍 ADIM 8 — Arama ve Performans

**Amaç:**  
Şablon arama ve filtreleme işlemlerini optimize etmek.

**Yapılacaklar:**
- Başlangıçta istemci tarafı filtreleme (max 100 kayıt).
- Gecikmeli sunucu sorgusu (300ms debounce) sonraki sürümde.

**Kabul Kriterleri:**
- 100 kayıt içinde arama anında çalışır.

**Test:**
- Büyük listelerde arama gecikmeden sonuç verir.

---

## 🧑‍💼 ADIM 9 — Yetki ve Güvenlik

**Amaç:**  
Veri gizliliği ve güvenliği sağlanır.

**Yapılacaklar:**
- Tüm uçlarda `get_current_user` kontrolü.
- Departman filtreleri zorunlu.
- XSS önlemleri (`textContent` render).
- Uygun hata mesajları.

**Kabul Kriterleri:**
- Departman dışı erişimler engellenir.
- HTML injection engellenir.

**Test:**
- Farklı departmandan 403 döner.
- HTML içeren şablonlar güvenli şekilde görüntülenir.

---

## 🧑‍💻 ADIM 10 — Admin Görünümü

**Amaç:**  
Admin’in tüm departman şablonlarını görebilmesi.

**Yapılacaklar:**
- Admin kullanıcılar için “Departman” filtresi eklenecek.
- Admin tüm kategorileri silebilir.

**Kabul Kriterleri:**
- Admin departman seçimiyle filtreleme yapabilir.

**Test:**
- Admin hesabı farklı departman şablonlarını görüntüleyebilir.

---

## ✨ ADIM 11 — Bildirimler ve UX Cilası

**Amaç:**  
Kullanıcı deneyimini güçlendirmek.

**Yapılacaklar:**
- Toast mesajları (kaydet, sil, hata).
- Silme onayı (modal confirm).
- “Daha Fazla” butonu (offset/limit).

**Kabul Kriterleri:**
- Her işlem sonrası uygun geri bildirim gösterilir.

**Test:**
- Silmeden önce onay ekranı çıkar.
- Başarılı kayıtta kısa başarı mesajı görülür.

---

## 🧪 ADIM 12 — Test Senaryoları (Manuel QA)

1. Şablon kaydetme ve listeleme.  
2. Yeni kategori oluşturma.  
3. Arama + filtre + “Sadece Benimkiler”.  
4. “Kullan” akışı: içerik doğru alana geçer.  
5. Başkasının şablonunu silememe.  
6. Departman izolasyonu.  
7. Boş kategori uyarısı.  
8. Otomatik başlık üretimi.  
9. Performans kontrolü (100+ kayıt).

---

## 🧾 ADIM 13 — Dokümantasyon

**Amaç:**  
Yeni özelliğin proje dokümantasyonuna eklenmesi.

**Yapılacaklar:**
- `/docs/feature_templates.md` bu dosya olarak projeye eklenir.  
- API endpoint örnekleri, akış diyagramı ve kullanım rehberi eklenir.

---

## 🚀 ADIM 14 — Yayın ve Geri Bildirim

**Amaç:**  
Özelliğin kontrollü biçimde yayına alınması.

**Yapılacaklar:**
- `.env` içine `TEMPLATES_ENABLED=true` feature flag eklenecek.  
- İlk hafta loglar yakından izlenecek.  
- Kullanıcı geri bildirimleri toplanacak.  
- Faz-2 planı: “Favori”, “Etiket”, “Paylaşımsız şablon”.

---

## 📘 Özet

| Bileşen | Açıklama |
|----------|-----------|
| **Yeni Tablolar** | templates, template_categories |
| **Yeni Uçlar** | /templates, /categories |
| **Yeni Ekran** | Şablonlarım (listeleme, filtre, arama, kopyala, kullan) |
| **Yeni UI Elemanları** | “Şablon olarak sakla” checkbox, kategori seçici |
| **Erişim Kuralları** | Departman bazlı görünürlük, sahiplik kontrolü |
| **Gelecek Geliştirmeler** | Favori, özel şablonlar, etiketleme, FTS5 arama |

---

**Hazırlayan:**  
Zafer Turan – Bilgi İşlem Müdürlüğü  
**Tarih:** 2025-10  
**Versiyon:** 1.0   
