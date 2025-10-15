# 🏗️ ŞABLONLAR MİMARİ KURALLARI

## 📋 Genel Kurallar

### 1. **Departman Bazlı Erişim**
```python
# Tüm şablon/kategori işlemlerinde zorunlu filtre
def filter_by_department(query, current_user):
    if current_user.is_admin:
        # Admin tüm departmanları görebilir
        return query
    else:
        # Normal kullanıcı sadece kendi departmanını görebilir
        return query.filter(Template.department == current_user.department)
```

### 2. **Sahiplik Kuralları**
```python
# Silme/düzenleme sadece owner veya admin tarafından yapılabilir
def check_ownership(template, current_user):
    if current_user.is_admin:
        return True  # Admin her şeyi yapabilir
    return template.owner_user_id == current_user.id
```

### 3. **Erişim Kontrolü**
```python
# Departman dışı erişim 403 döner
def check_department_access(template, current_user):
    if current_user.is_admin:
        return True  # Admin erişimi kısıtlanmaz
    if template.department != current_user.department:
        raise HTTPException(status_code=403, detail="Access denied: Different department")
    return True
```

## 🔒 Güvenlik Kuralları

### **Backend Filtreleme (Zorunlu)**
- Tüm database sorgularında `department` filtresi uygulanır
- Frontend'den gelen filtreler backend'de tekrar kontrol edilir
- Admin kullanıcılar hariç, hiçbir kullanıcı başka departman verilerini göremez

### **API Endpoint Güvenliği**
```python
@router.get("/templates")
async def get_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Departman filtresi zorunlu
    query = db.query(Template)
    if not current_user.is_admin:
        query = query.filter(Template.department == current_user.department)
    
    return query.all()
```

### **Silme İşlemleri**
```python
@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    template = db.query(Template).filter(Template.id == template_id).first()
    
    # Departman kontrolü
    if not current_user.is_admin and template.department != current_user.department:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Sahiplik kontrolü
    if not current_user.is_admin and template.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owner can delete")
    
    # Silme işlemi
    db.delete(template)
    db.commit()
```

## 🧪 Test Senaryoları

### **1. Departman İzolasyonu**
- **A departmanı kullanıcısı** → B departmanı şablonlarına erişim → **403 Forbidden**
- **B departmanı kullanıcısı** → A departmanı şablonlarına erişim → **403 Forbidden**

### **2. Admin Erişimi**
- **Admin kullanıcı** → Tüm departman şablonlarını görebilir
- **Admin kullanıcı** → Herhangi bir şablonu silebilir
- **Admin kullanıcı** → Departman filtresi olmadan tüm verileri listeleyebilir

### **3. Sahiplik Kontrolü**
- **Normal kullanıcı** → Kendi şablonunu silebilir
- **Normal kullanıcı** → Başkasının şablonunu silemez → **403 Forbidden**
- **Admin kullanıcı** → Herhangi bir şablonu silebilir

## 📊 Veri Modeli

### **Template Tablosu**
```sql
CREATE TABLE templates (
    id INTEGER PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    department VARCHAR(255) NOT NULL,  -- Departman bilgisi
    owner_user_id INTEGER NOT NULL,    -- Sahip kullanıcı
    category_id INTEGER,
    created_at DATETIME,
    updated_at DATETIME,
    is_active BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (owner_user_id) REFERENCES users(id),
    FOREIGN KEY (category_id) REFERENCES template_categories(id)
);
```

### **Template_Categories Tablosu**
```sql
CREATE TABLE template_categories (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    department VARCHAR(255) NOT NULL,  -- Departman bilgisi
    owner_user_id INTEGER NOT NULL,    -- Sahip kullanıcı
    created_at DATETIME,
    
    UNIQUE(name, department),  -- Aynı departmanda aynı isim
    FOREIGN KEY (owner_user_id) REFERENCES users(id)
);
```

## 🚀 Uygulama Stratejisi

### **Adım 2'de Yapılacaklar**
1. Veritabanı tabloları oluşturulacak
2. Tüm API endpoint'lerinde bu kurallar uygulanacak
3. Test senaryoları manuel olarak test edilecek

### **Önemli Notlar**
- **Hiçbir endpoint'te departman filtresi atlanmamalı**
- **Admin kontrolü her işlemde yapılmalı**
- **403 hataları açıklayıcı mesajlarla dönmeli**
- **Frontend'de de departman bilgisi gösterilmeli**

---

**Hazırlayan:** AI Assistant  
**Tarih:** 2025-10-14  
**Versiyon:** 1.0  
**Durum:** ADIM 1 Tamamlandı ✅
