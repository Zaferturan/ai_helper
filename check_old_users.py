#!/usr/bin/env python3
"""Check users from old container SQLite database"""
import sqlite3
import sys

db_path = sys.argv[1] if len(sys.argv) > 1 else '/app/data/ai_helper.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get table schema
cursor.execute("PRAGMA table_info(users)")
columns = [col[1] for col in cursor.fetchall()]
print("Users table columns:", columns)
print("\n" + "="*80 + "\n")

# Get users from image
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

print("Users from image found in old container:\n")
found_count = 0
for email in emails_from_image:
    cursor.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email,))
    user = cursor.fetchone()
    if user:
        found_count += 1
        user_dict = dict(zip(columns, user))
        print(f"{user_dict.get('email', 'N/A')}:")
        print(f"  ID: {user_dict.get('id', 'N/A')}")
        print(f"  Full Name: {user_dict.get('full_name', 'N/A')}")
        print(f"  Department: {user_dict.get('department', 'N/A')}")
        print(f"  Total Requests: {user_dict.get('total_requests', 0)}")
        print(f"  Answered Requests: {user_dict.get('answered_requests', 0)}")
        print(f"  Is Admin: {user_dict.get('is_admin', False)}")
        print(f"  Is Active: {user_dict.get('is_active', True)}")
        print()
    else:
        print(f"{email}: NOT FOUND\n")

print(f"\nFound: {found_count}/{len(emails_from_image)} users")
print("\n" + "="*80 + "\n")

# Get all users count
cursor.execute("SELECT COUNT(*) FROM users")
total_users = cursor.fetchone()[0]
print(f"Total users in old container: {total_users}")

conn.close()

