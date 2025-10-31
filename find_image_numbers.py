#!/usr/bin/env python3
"""Find the numbers from the image in old container SQLite"""
import sqlite3
import sys

db_path = sys.argv[1] if len(sys.argv) > 1 else '/app/data/ai_helper.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Resimdeki değerler
target_values = {
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
print("RESIMDEKI SAYILARI BULMA ANALIZI")
print("="*80)
print()

# Check responses table structure
cursor.execute("PRAGMA table_info(responses)")
resp_columns = [col[1] for col in cursor.fetchall()]
print("Responses table columns:", resp_columns)
print()

for email, (target_total, target_answered) in target_values.items():
    cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (email,))
    user_row = cursor.fetchone()
    if not user_row:
        print(f"{email}: USER NOT FOUND\n")
        continue
    
    user_id = user_row[0]
    
    # Method 1: Total from requests
    cursor.execute("SELECT COUNT(*) FROM requests WHERE user_id = ?", (user_id,))
    method1_total = cursor.fetchone()[0]
    
    # Method 2: Total from responses
    cursor.execute("SELECT COUNT(*) FROM responses WHERE user_id = ?", (user_id,))
    method2_total = cursor.fetchone()[0]
    
    # Method 3: Answered from responses (distinct request_id)
    cursor.execute("SELECT COUNT(DISTINCT request_id) FROM responses WHERE user_id = ?", (user_id,))
    method3_answered = cursor.fetchone()[0]
    
    # Method 4: Answered from responses with has_been_copied
    method4_answered = 0
    if 'has_been_copied' in resp_columns:
        cursor.execute("SELECT COUNT(DISTINCT request_id) FROM responses WHERE user_id = ? AND has_been_copied = 1", (user_id,))
        method4_answered = cursor.fetchone()[0]
    
    # Method 5: Copy events count
    cursor.execute("SELECT COUNT(*) FROM copy_events WHERE user_id = ?", (user_id,))
    method5_answered = cursor.fetchone()[0]
    
    # Method 6: Check if there's a different calculation
    # Maybe total = responses count, answered = copy_events?
    
    print(f"{email}:")
    print(f"  RESIM: Total={target_total}, Answered={target_answered}")
    print(f"  Method 1 - requests COUNT: {method1_total}")
    print(f"  Method 2 - responses COUNT: {method2_total}")
    print(f"  Method 3 - responses DISTINCT request_id: {method3_answered}")
    print(f"  Method 4 - responses has_been_copied: {method4_answered}")
    print(f"  Method 5 - copy_events COUNT: {method5_answered}")
    
    # Try combinations
    if method2_total == target_total and method5_answered == target_answered:
        print(f"  ✓ MATCH: Total=responses COUNT, Answered=copy_events")
    elif method2_total == target_total and method4_answered == target_answered:
        print(f"  ✓ MATCH: Total=responses COUNT, Answered=has_been_copied")
    elif method1_total == target_total and method5_answered == target_answered:
        print(f"  ✓ MATCH: Total=requests COUNT, Answered=copy_events")
    elif method1_total == target_total and method4_answered == target_answered:
        print(f"  ✓ MATCH: Total=requests COUNT, Answered=has_been_copied")
    elif method2_total == target_total and method3_answered == target_answered:
        print(f"  ✓ MATCH: Total=responses COUNT, Answered=DISTINCT request_id")
    elif method1_total == target_total and method3_answered == target_answered:
        print(f"  ✓ MATCH: Total=requests COUNT, Answered=DISTINCT request_id")
    
    print()

conn.close()

