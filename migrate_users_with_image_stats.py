#!/usr/bin/env python3
"""Migrate users from old container and add image stats to existing PostgreSQL users"""
import sqlite3
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Resimdeki değerler (Toplam Ürettiği Yanıt, Cevapladığı İstek Sayısı)
IMAGE_VALUES = {
    'zaferturan@nilufer.bel.tr': (516, 157),
    'enginakyildiz@nilufer.bel.tr': (4, 3),
    'hakanulucan@nilufer.bel.tr': (21, 7),
    'senceroncul@nilufer.bel.tr': (1, 1),
    'erhanaptioglu@nilufer.bel.tr': (2, 1),
    'gulsahakpinar@nilufer.bel.tr': (50, 27),
    'burakelove@nilufer.bel.tr': (2, 0),
    'seymaaktas@nilufer.bel.tr': (0, 0),
    'nalanmazlum@nilufer.bel.tr': (0, 0),
    'busracicek@nilufer.bel.tr': (2, 1),
    'mesutsolaklar@nilufer.bel.tr': (4, 1),
    'oznuravdal@nilufer.bel.tr': (1, 0),
    'yasarkizilirmak@nilufer.bel.tr': (4, 0)
}

# Old container SQLite DB
OLD_DB_PATH = '/app/data/ai_helper.db'

# PostgreSQL connection (from new container)
POSTGRES_DB = os.getenv('DATABASE_URL', 'postgresql://engin:BimOrtak12*@postgr_server:5432/postgres')
if '?options=' not in POSTGRES_DB:
    POSTGRES_DB = f"{POSTGRES_DB}?options=-csearch_path%3Dai_helper"

print("="*80)
print("KULLANICI VERI MIGRASYONU - Resim değerleri + PostgreSQL mevcut değerleri")
print("="*80)
print()

# Connect to old SQLite
sqlite_conn = sqlite3.connect(OLD_DB_PATH)
sqlite_cursor = sqlite_conn.cursor()

# Connect to PostgreSQL
pg_engine = create_engine(POSTGRES_DB)
pg_session = sessionmaker(bind=pg_engine)()

try:
    print("1. Eski container'dan kullanıcı bilgileri alınıyor...\n")
    
    users_to_update = []
    
    for email, (image_total, image_answered) in IMAGE_VALUES.items():
        # Get user from old SQLite
        sqlite_cursor.execute("""
            SELECT id, email, full_name, department, is_admin, is_active, created_at, last_login, profile_completed
            FROM users 
            WHERE LOWER(email) = LOWER(?)
        """, (email,))
        
        old_user = sqlite_cursor.fetchone()
        if not old_user:
            print(f"{email}: Eski container'da bulunamadı, atlanıyor")
            continue
        
        user_id, email_db, full_name, department, is_admin, is_active, created_at, last_login, profile_completed = old_user
        
        # Check if user exists in PostgreSQL
        pg_user = pg_session.execute(
            text("SELECT id, email, full_name, department, total_requests, answered_requests, is_admin, is_active FROM ai_helper.users WHERE LOWER(email) = LOWER(:email)"),
            {'email': email_db}
        ).fetchone()
        
        if pg_user:
            pg_id, pg_email, pg_full_name, pg_dept, pg_total, pg_answered, pg_is_admin, pg_is_active = pg_user
            # User exists - ADD image values to existing values
            new_total = pg_total + image_total
            new_answered = pg_answered + image_answered
            
            print(f"{email_db}:")
            print(f"  Mevcut (PostgreSQL): Total={pg_total}, Answered={pg_answered}")
            print(f"  Resim değerleri: Total={image_total}, Answered={image_answered}")
            print(f"  YENI TOPLAM: Total={new_total}, Answered={new_answered}")
            
            # Update user
            pg_session.execute(
                text("""
                    UPDATE ai_helper.users 
                    SET 
                        total_requests = :new_total,
                        answered_requests = :new_answered,
                        full_name = COALESCE(NULLIF(:full_name, ''), full_name),
                        department = COALESCE(NULLIF(:department, ''), department),
                        is_admin = :is_admin,
                        is_active = :is_active
                    WHERE id = :user_id
                """),
                {
                    'user_id': pg_id,
                    'new_total': new_total,
                    'new_answered': new_answered,
                    'full_name': full_name,
                    'department': department,
                    'is_admin': bool(is_admin),
                    'is_active': bool(is_active)
                }
            )
            
            users_to_update.append({
                'email': email_db,
                'action': 'UPDATED',
                'old_total': pg_total,
                'old_answered': pg_answered,
                'new_total': new_total,
                'new_answered': new_answered
            })
        else:
            # User doesn't exist - create with image values
            print(f"{email_db}: YENI KULLANICI (resim değerleri ile)")
            print(f"  Total={image_total}, Answered={image_answered}")
            
            pg_session.execute(
                text("""
                    INSERT INTO ai_helper.users 
                    (email, full_name, department, total_requests, answered_requests, is_admin, is_active, profile_completed)
                    VALUES 
                    (:email, :full_name, :department, :total_requests, :answered_requests, :is_admin, :is_active, :profile_completed)
                """),
                {
                    'email': email_db,
                    'full_name': full_name,
                    'department': department,
                    'total_requests': image_total,
                    'answered_requests': image_answered,
                    'is_admin': bool(is_admin),
                    'is_active': bool(is_active),
                    'profile_completed': bool(profile_completed) if profile_completed is not None else True
                }
            )
            
            users_to_update.append({
                'email': email_db,
                'action': 'CREATED',
                'total': image_total,
                'answered': image_answered
            })
        
        print()
    
    print("\n2. Değişiklikler kaydediliyor...")
    pg_session.commit()
    print("✓ Commit başarılı!")
    
    print("\n" + "="*80)
    print("ÖZET:")
    print("="*80)
    for user in users_to_update:
        if user['action'] == 'UPDATED':
            print(f"{user['email']}: {user['old_total']}+{user['new_total']-user['old_total']}={user['new_total']} (Total), {user['old_answered']}+{user['new_answered']-user['old_answered']}={user['new_answered']} (Answered)")
        else:
            print(f"{user['email']}: YENI - Total={user['total']}, Answered={user['answered']}")
    
except Exception as e:
    print(f"\n❌ HATA: {e}")
    pg_session.rollback()
    import traceback
    traceback.print_exc()
finally:
    sqlite_conn.close()
    pg_session.close()

