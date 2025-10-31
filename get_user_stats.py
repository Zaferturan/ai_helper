#!/usr/bin/env python3
"""Get user stats from old container SQLite"""
import sqlite3
import sys

db_path = sys.argv[1] if len(sys.argv) > 1 else '/app/data/ai_helper.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

emails_from_image = [
    'zaferturan@nilufer.bel.tr',
    'enginakyildiz@nilufer.bel.tr',
    'hakanulucan@nilufer.bel.tr',
    'senceroncul@nilufer.bel.tr',
    'erhanaptioglu@nilufer.bel.tr',
    'gulsahakpinar@nilufer.bel.tr',
    'burakelove@nilufer.bel.tr',
    'seymaaktas@nilufer.bel.tr',
    'nalanmazlum@nilufer.bel.tr',
    'busracicek@nilufer.bel.tr',
    'mesutsolaklar@nilufer.bel.tr',
    'oznuravdal@nilufer.bel.tr',
    'yasarkizilirmak@nilufer.bel.tr'
]

print("="*80)
print("USER STATS FROM OLD CONTAINER (SQLite)")
print("="*80)
print()

results = []
for email in emails_from_image:
    # Get user
    cursor.execute("SELECT id, email, full_name, department, is_admin, is_active FROM users WHERE LOWER(email) = LOWER(?)", (email,))
    user = cursor.fetchone()
    if not user:
        print(f"{email}: NOT FOUND")
        continue
    
    user_id, email_db, full_name, department, is_admin, is_active = user
    
    # Count total requests
    cursor.execute("SELECT COUNT(*) FROM requests WHERE user_id = ?", (user_id,))
    total_requests = cursor.fetchone()[0]
    
    # Count answered requests
    cursor.execute("SELECT COUNT(DISTINCT request_id) FROM responses WHERE user_id = ?", (user_id,))
    answered_requests = cursor.fetchone()[0]
    
    results.append({
        'email': email_db,
        'full_name': full_name,
        'department': department,
        'total_requests': total_requests,
        'answered_requests': answered_requests,
        'is_admin': bool(is_admin),
        'is_active': bool(is_active)
    })
    
    print(f"{email_db}")
    print(f"  Name: {full_name}")
    print(f"  Department: {department}")
    print(f"  Total Requests: {total_requests}")
    print(f"  Answered Requests: {answered_requests}")
    print(f"  Is Admin: {is_admin}, Is Active: {is_active}")
    print()

print("="*80)
print(f"Total: {len(results)} users found")
print("="*80)

conn.close()

