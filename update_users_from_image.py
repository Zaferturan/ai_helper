#!/usr/bin/env python3
"""Update PostgreSQL users with image stats added to existing values"""
import json
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# PostgreSQL connection
POSTGRES_DB = os.getenv('DATABASE_URL', 'postgresql://engin:BimOrtak12*@postgr_server:5432/postgres')
if '?options=' not in POSTGRES_DB:
    POSTGRES_DB = f"{POSTGRES_DB}?options=-csearch_path%3Dai_helper"

# Read JSON from stdin or file
if len(sys.argv) > 1:
    with open(sys.argv[1], 'r') as f:
        users_data = json.load(f)
else:
    users_data = json.load(sys.stdin)

pg_engine = create_engine(POSTGRES_DB)
pg_session = sessionmaker(bind=pg_engine)()

print("="*80)
print("KULLANICI GUNCELLEMESI - Resim değerleri + PostgreSQL mevcut değerleri")
print("="*80)
print()

updated_count = 0
created_count = 0

try:
    for user_data in users_data:
        email = user_data['email']
        image_total = user_data['total_requests']
        image_answered = user_data['answered_requests']
        
        # Check if user exists in PostgreSQL
        pg_user = pg_session.execute(
            text("SELECT id, total_requests, answered_requests FROM ai_helper.users WHERE LOWER(email) = LOWER(:email)"),
            {'email': email}
        ).fetchone()
        
        if pg_user:
            pg_id, pg_total, pg_answered = pg_user
            # User exists - ADD image values
            new_total = pg_total + image_total
            new_answered = pg_answered + image_answered
            
            print(f"{email}:")
            print(f"  Mevcut: Total={pg_total}, Answered={pg_answered}")
            print(f"  Resim: Total={image_total}, Answered={image_answered}")
            print(f"  YENI: Total={new_total}, Answered={new_answered}")
            
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
                    'full_name': user_data['full_name'],
                    'department': user_data['department'],
                    'is_admin': user_data['is_admin'],
                    'is_active': user_data['is_active']
                }
            )
            updated_count += 1
        else:
            # User doesn't exist - create with image values
            print(f"{email}: YENI KULLANICI - Total={image_total}, Answered={image_answered}")
            
            pg_session.execute(
                text("""
                    INSERT INTO ai_helper.users 
                    (email, full_name, department, total_requests, answered_requests, is_admin, is_active, profile_completed)
                    VALUES 
                    (:email, :full_name, :department, :total_requests, :answered_requests, :is_admin, :is_active, :profile_completed)
                """),
                {
                    'email': user_data['email'],
                    'full_name': user_data['full_name'],
                    'department': user_data['department'],
                    'total_requests': image_total,
                    'answered_requests': image_answered,
                    'is_admin': user_data['is_admin'],
                    'is_active': user_data['is_active'],
                    'profile_completed': user_data['profile_completed']
                }
            )
            created_count += 1
        
        print()
    
    pg_session.commit()
    print(f"\n✓ Başarılı: {updated_count} güncellendi, {created_count} oluşturuldu")
    
except Exception as e:
    print(f"\n❌ HATA: {e}")
    pg_session.rollback()
    import traceback
    traceback.print_exc()
finally:
    pg_session.close()

