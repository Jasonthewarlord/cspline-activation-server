"""
Set up test data for the activation server.
Creates some test license keys for testing.
"""

import sqlite3
import secrets
from app import init_database, generate_license_key

def create_test_keys():
    """Create some test license keys."""
    init_database()
    
    conn = sqlite3.connect('cspline_licenses.db')
    
    # Generate 5 test keys
    test_keys = [
        (generate_license_key(), "Test batch 1"),
        (generate_license_key(), "Test batch 1"), 
        (generate_license_key(), "Demo keys"),
        (generate_license_key(), "Demo keys"),
        ("CSPLINE-TEST-KEY1-2024", "Manual test key")
    ]
    
    for key, notes in test_keys:
        try:
            conn.execute(
                'INSERT OR IGNORE INTO license_keys (license_key, notes) VALUES (?, ?)',
                (key, notes)
            )
        except sqlite3.IntegrityError:
            pass  # Key already exists
    
    conn.commit()
    
    # Show created keys
    keys = conn.execute('SELECT license_key, notes, status FROM license_keys').fetchall()
    
    print("=== Test License Keys Created ===")
    for key, notes, status in keys:
        print(f"{key} ({status}) - {notes}")
    
    conn.close()
    
    print(f"\nTotal keys: {len(keys)}")
    print("Database: cspline_licenses.db")

if __name__ == "__main__":
    create_test_keys()
