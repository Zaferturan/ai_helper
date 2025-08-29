#!/usr/bin/env python3
"""
Migration script to add has_been_copied column to requests table
"""

import sqlite3
import os

def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute("PRAGMA table_info(requests)")
    columns = cursor.fetchall()
    return any(col[1] == column_name for col in columns)

def main():
    # Database file path
    db_path = "ai_helper.db"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Starting migration: adding has_been_copied column to requests table...")
        
        # Check if column already exists
        if not column_exists(cursor, "requests", "has_been_copied"):
            print("Adding has_been_copied column...")
            cursor.execute("ALTER TABLE requests ADD COLUMN has_been_copied BOOLEAN DEFAULT 0")
            print("✅ has_been_copied column added successfully")
        else:
            print("ℹ️ has_been_copied column already exists")
        
        # Commit changes
        conn.commit()
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()


