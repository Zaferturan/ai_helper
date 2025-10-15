#!/usr/bin/env python3
"""
Template API endpoint'lerini test eden script
"""

import requests
import json
from sqlalchemy.orm import sessionmaker
from connection import engine
from models import User, Template, TemplateCategory

# Test kullanıcısı oluştur
def create_test_user():
    """Test kullanıcısı oluştur"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Test kullanıcısı var mı kontrol et
        test_user = db.query(User).filter(User.email == "test@nilufer.bel.tr").first()
        if not test_user:
            test_user = User(
                email="test@nilufer.bel.tr",
                full_name="Test Kullanıcı",
                department="Test Departman",
                is_active=True,
                profile_completed=True,
                is_admin=False
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            print(f"✅ Test kullanıcısı oluşturuldu: {test_user.id}")
        else:
            print(f"✅ Test kullanıcısı mevcut: {test_user.id}")
        
        return test_user
        
    except Exception as e:
        print(f"❌ Test kullanıcısı oluşturma hatası: {e}")
        return None
    finally:
        db.close()

def get_auth_token():
    """Test için basit token oluştur (gerçek JWT değil)"""
    # Bu gerçek bir test değil, sadece endpoint'lerin çalıştığını görmek için
    return "test_token"

def test_endpoints():
    """API endpoint'lerini test et"""
    base_url = "http://localhost:12000/api/v1"
    
    print("🧪 Template API Test Başlıyor...")
    
    # Test kullanıcısı oluştur
    test_user = create_test_user()
    if not test_user:
        print("❌ Test kullanıcısı oluşturulamadı")
        return
    
    # Endpoint'leri test et (authentication olmadan)
    endpoints = [
        "/templates",
        "/categories"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            if response.status_code == 401:
                print(f"✅ {endpoint} - Authentication korumalı (401)")
            else:
                print(f"⚠️ {endpoint} - Beklenmeyen durum: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} - Hata: {e}")
    
    print("🎉 API endpoint testleri tamamlandı!")

if __name__ == "__main__":
    test_endpoints()
