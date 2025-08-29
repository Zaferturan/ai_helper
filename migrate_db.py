#!/usr/bin/env python3
"""
Database migration script to add new fields and relationships
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text, inspect
from connection import Base, engine
from models import User, Request, Response

def column_exists(conn, table_name, column_name):
    """Check if a column exists in a table"""
    try:
        result = conn.execute(text(f"PRAGMA table_info({table_name})"))
        columns = [row[1] for row in result.fetchall()]
        return column_name in columns
    except:
        return False

def migrate_database():
    """Migrate database to add new fields and relationships"""
    
    print("🔄 Veritabanı migration başlatılıyor...")
    
    try:
        # Yeni tabloları oluştur (eğer yoksa)
        Base.metadata.create_all(bind=engine)
        print("✅ Tablolar oluşturuldu/güncellendi")
        
        # Mevcut kullanıcıları admin yap (zaferturan@nilufer.bel.tr için)
        with engine.connect() as conn:
            # is_admin kolonu ekle (eğer yoksa)
            if not column_exists(conn, "users", "is_admin"):
                conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE"))
                print("✅ is_admin kolonu eklendi")
            else:
                print("ℹ️ is_admin kolonu zaten mevcut")
            
            # zaferturan@nilufer.bel.tr kullanıcısını admin yap
            result = conn.execute(
                text("UPDATE users SET is_admin = TRUE WHERE email = 'zaferturan@nilufer.bel.tr'")
            )
            if result.rowcount > 0:
                print("✅ zaferturan@nilufer.bel.tr admin yapıldı")
            else:
                print("ℹ️ zaferturan@nilufer.bel.tr kullanıcısı bulunamadı")
            
            # Request tablosuna yeni kolonlar ekle
            if not column_exists(conn, "requests", "user_id"):
                conn.execute(text("ALTER TABLE requests ADD COLUMN user_id INTEGER REFERENCES users(id)"))
                print("✅ requests.user_id kolonu eklendi")
            else:
                print("ℹ️ requests.user_id kolonu zaten mevcut")
            
            if not column_exists(conn, "requests", "is_active"):
                conn.execute(text("ALTER TABLE requests ADD COLUMN is_active BOOLEAN"))
                print("✅ requests.is_active kolonu eklendi")
            else:
                print("ℹ️ requests.is_active kolonu zaten mevcut")
            
            if not column_exists(conn, "requests", "remaining_responses"):
                conn.execute(text("ALTER TABLE requests ADD COLUMN remaining_responses INTEGER"))
                print("✅ requests.remaining_responses kolonu eklendi")
            else:
                print("ℹ️ requests.remaining_responses kolonu zaten mevcut")
            
            # Response tablosuna yeni kolonlar ekle
            if not column_exists(conn, "responses", "temperature"):
                conn.execute(text("ALTER TABLE responses ADD COLUMN temperature FLOAT"))
                print("✅ responses.temperature kolonu eklendi")
            else:
                print("ℹ️ responses.temperature kolonu zaten mevcut")
            
            if not column_exists(conn, "responses", "top_p"):
                conn.execute(text("ALTER TABLE responses ADD COLUMN top_p FLOAT"))
                print("✅ responses.top_p kolonu eklendi")
            else:
                print("ℹ️ responses.top_p kolonu zaten mevcut")
            
            if not column_exists(conn, "responses", "repetition_penalty"):
                conn.execute(text("ALTER TABLE responses ADD COLUMN repetition_penalty FLOAT"))
                print("✅ responses.repetition_penalty kolonu eklendi")
            else:
                print("ℹ️ responses.repetition_penalty kolonu zaten mevcut")
            
            if not column_exists(conn, "responses", "tokens_used"):
                conn.execute(text("ALTER TABLE responses ADD COLUMN tokens_used INTEGER"))
                print("✅ responses.tokens_used kolonu eklendi")
            else:
                print("ℹ️ responses.tokens_used kolonu zaten mevcut")
            
            # Mevcut kayıtları güncelle
            conn.execute(text("UPDATE responses SET temperature = 0.7, top_p = 0.9, repetition_penalty = 1.0 WHERE temperature IS NULL"))
            print("✅ Mevcut response kayıtları güncellendi")
            
            conn.commit()
            print("✅ Migration tamamlandı!")
            
    except Exception as e:
        print(f"❌ Migration hatası: {e}")
        return False
    
    return True

if __name__ == "__main__":
    migrate_database()
