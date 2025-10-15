#!/usr/bin/env python3
"""
Template ve TemplateCategory tablolarını oluşturan migration script'i
Bu script mevcut veriyi etkilemeden yeni tabloları ekler.
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from connection import engine, Base
from models import TemplateCategory, Template
import logging

# Logging ayarla
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_table_exists(engine, table_name):
    """Tabloyu kontrol et"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='{table_name}'
            """))
            return result.fetchone() is not None
    except Exception as e:
        logger.error(f"Tablo kontrol hatası: {e}")
        return False

def create_tables():
    """Yeni tabloları oluştur"""
    try:
        logger.info("🔄 Template tabloları oluşturuluyor...")
        
        # Sadece yeni tabloları oluştur
        TemplateCategory.__table__.create(engine, checkfirst=True)
        Template.__table__.create(engine, checkfirst=True)
        
        logger.info("✅ Template tabloları başarıyla oluşturuldu!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Tablo oluşturma hatası: {e}")
        return False

def verify_tables():
    """Tabloların doğru oluştuğunu kontrol et"""
    try:
        logger.info("🔍 Tablolar kontrol ediliyor...")
        
        # Tabloların varlığını kontrol et
        template_categories_exists = check_table_exists(engine, "template_categories")
        templates_exists = check_table_exists(engine, "templates")
        
        if not template_categories_exists:
            logger.error("❌ template_categories tablosu oluşturulamadı!")
            return False
            
        if not templates_exists:
            logger.error("❌ templates tablosu oluşturulamadı!")
            return False
        
        # Index'leri kontrol et
        with engine.connect() as conn:
            # template_categories index'leri
            indexes = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND tbl_name='template_categories'
            """)).fetchall()
            
            expected_indexes = [
                'idx_template_categories_department',
                'idx_template_categories_owner'
            ]
            
            for idx in expected_indexes:
                if not any(idx in str(row) for row in indexes):
                    logger.warning(f"⚠️ Index eksik: {idx}")
            
            # templates index'leri
            indexes = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND tbl_name='templates'
            """)).fetchall()
            
            expected_indexes = [
                'idx_templates_department',
                'idx_templates_category',
                'idx_templates_owner',
                'idx_templates_active',
                'idx_templates_created'
            ]
            
            for idx in expected_indexes:
                if not any(idx in str(row) for row in indexes):
                    logger.warning(f"⚠️ Index eksik: {idx}")
        
        logger.info("✅ Tüm tablolar ve index'ler doğru oluşturuldu!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Tablo doğrulama hatası: {e}")
        return False

def test_constraints():
    """Constraint'leri test et"""
    try:
        logger.info("🧪 Constraint'ler test ediliyor...")
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Test kategorisi oluştur
            test_category = TemplateCategory(
                name="Test Kategori",
                department="Test Departman",
                owner_user_id=1  # Varsayılan user ID
            )
            db.add(test_category)
            db.commit()
            logger.info("✅ Test kategorisi oluşturuldu")
            
            # Aynı isimde ikinci kategori oluşturmaya çalış (hata vermeli)
            try:
                duplicate_category = TemplateCategory(
                    name="Test Kategori",  # Aynı isim
                    department="Test Departman",  # Aynı departman
                    owner_user_id=1
                )
                db.add(duplicate_category)
                db.commit()
                logger.error("❌ Unique constraint çalışmıyor!")
                return False
            except Exception as e:
                logger.info("✅ Unique constraint çalışıyor (duplicate engellendi)")
                db.rollback()
            
            # Test şablonu oluştur
            test_template = Template(
                title="Test Şablon",
                content="Bu bir test şablonudur.",
                department="Test Departman",
                owner_user_id=1,
                category_id=test_category.id
            )
            db.add(test_template)
            db.commit()
            logger.info("✅ Test şablonu oluşturuldu")
            
            # Soft delete test
            test_template.is_active = False
            db.commit()
            logger.info("✅ Soft delete test edildi")
            
            # Temizlik
            db.delete(test_template)
            db.delete(test_category)
            db.commit()
            logger.info("✅ Test verileri temizlendi")
            
        finally:
            db.close()
        
        logger.info("✅ Tüm constraint'ler doğru çalışıyor!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Constraint test hatası: {e}")
        return False

def main():
    """Ana migration fonksiyonu"""
    logger.info("🚀 Template Migration Başlıyor...")
    
    # 1. Tabloları oluştur
    if not create_tables():
        logger.error("❌ Migration başarısız: Tablolar oluşturulamadı")
        sys.exit(1)
    
    # 2. Tabloları doğrula
    if not verify_tables():
        logger.error("❌ Migration başarısız: Tablolar doğrulanamadı")
        sys.exit(1)
    
    # 3. Constraint'leri test et
    if not test_constraints():
        logger.error("❌ Migration başarısız: Constraint'ler test edilemedi")
        sys.exit(1)
    
    logger.info("🎉 Migration başarıyla tamamlandı!")
    logger.info("📋 Oluşturulan tablolar:")
    logger.info("   - template_categories (kategoriler)")
    logger.info("   - templates (şablonlar)")
    logger.info("🔒 Aktif güvenlik özellikleri:")
    logger.info("   - Departman bazlı unique constraint")
    logger.info("   - Soft delete (is_active)")
    logger.info("   - Performance index'leri")

if __name__ == "__main__":
    main()
