#!/usr/bin/env python3
"""Extract users from old container SQLite"""
import sqlite3
import json
import sys

db_path = sys.argv[1] if len(sys.argv) > 1 else '/app/data/ai_helper.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Resimdeki değerler
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

users_data = []

for email, (image_total, image_answered) in IMAGE_VALUES.items():
    cursor.execute("""
        SELECT id, email, full_name, department, is_admin, is_active, created_at, last_login, profile_completed
        FROM users 
        WHERE LOWER(email) = LOWER(?)
    """, (email,))
    
    user = cursor.fetchone()
    if user:
        user_id, email_db, full_name, department, is_admin, is_active, created_at, last_login, profile_completed = user
        
        users_data.append({
            'email': email_db,
            'full_name': full_name,
            'department': department,
            'total_requests': image_total,
            'answered_requests': image_answered,
            'is_admin': bool(is_admin),
            'is_active': bool(is_active),
            'created_at': str(created_at) if created_at else None,
            'last_login': str(last_login) if last_login else None,
            'profile_completed': bool(profile_completed) if profile_completed is not None else True
        })

# Output JSON
print(json.dumps(users_data, indent=2, ensure_ascii=False, default=str))

conn.close()

