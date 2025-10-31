#!/usr/bin/env python3
"""Prepare user data from old container with image values"""
import sqlite3
import json

db_path = '/app/data/ai_helper.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Resimdeki değerler (Toplam Ürettiği Yanıt, Cevapladığı İstek Sayısı)
image_values = {
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

print("="*80)
print("HAZIRLANAN KULLANICI VERILERI (Eski container + Resim değerleri)")
print("="*80)
print()

users_data = []

for email, (total_requests, answered_requests) in image_values.items():
    cursor.execute("""
        SELECT id, email, full_name, department, is_admin, is_active, created_at, last_login, profile_completed
        FROM users 
        WHERE LOWER(email) = LOWER(?)
    """, (email,))
    
    user = cursor.fetchone()
    if not user:
        print(f"{email}: NOT FOUND in old container")
        continue
    
    user_id, email_db, full_name, department, is_admin, is_active, created_at, last_login, profile_completed = user
    
    user_data = {
        'email': email_db,
        'full_name': full_name,
        'department': department,
        'total_requests': total_requests,  # Resimden
        'answered_requests': answered_requests,  # Resimden
        'is_admin': bool(is_admin),
        'is_active': bool(is_active),
        'created_at': str(created_at) if created_at else None,
        'last_login': str(last_login) if last_login else None,
        'profile_completed': bool(profile_completed) if profile_completed is not None else True
    }
    
    users_data.append(user_data)
    
    print(f"{email_db}:")
    print(f"  Name: {full_name}")
    print(f"  Department: {department}")
    print(f"  Total Requests: {total_requests} (from image)")
    print(f"  Answered Requests: {answered_requests} (from image)")
    print(f"  Is Admin: {is_admin}, Is Active: {is_active}")
    print()

print("="*80)
print(f"Total: {len(users_data)} users prepared")
print("="*80)
print()
print("JSON Output:")
print(json.dumps(users_data, indent=2, ensure_ascii=False, default=str))

conn.close()

