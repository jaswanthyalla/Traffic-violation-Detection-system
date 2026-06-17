#!/usr/bin/env python3
"""Quick verification of database refactoring"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("\n=== Database Refactoring Verification ===\n")

try:
    print("1. Testing database module import...", end=" ")
    from database import get_database_manager
    print("✓")
    
    print("2. Creating database manager...", end=" ")
    db = get_database_manager('database/violations.db')
    print("✓")
    
    print("3. Verifying database file created...", end=" ")
    assert os.path.exists('database/violations.db'), "Database not created"
    print("✓")
    
    print("4. Testing get_statistics()...", end=" ")
    stats = db.get_statistics()
    print("✓")
    
    print("5. Testing violation_logic imports...", end=" ")
    from violation_logic import ViolationDetector
    print("✓")
    
    print("6. Creating ViolationDetector...", end=" ")
    detector = ViolationDetector('database/violations.db')
    print("✓")
    
    print("7. Checking web_app.py config...", end=" ")
    with open('web_app.py', 'r') as f:
        content = f.read()
        assert 'from database import get_database_manager' in content
    print("✓")
    
    print("8. Checking app.py config...", end=" ")
    with open('app.py', 'r') as f:
        content = f.read()
        assert "'database_path': 'database/violations.db'" in content
    print("✓")
    
    print("\n=== All Verifications Passed! ===\n")
    print("✓ Database refactoring completed successfully")
    print("✓ Centralized database manager is working")
    print("✓ All modules properly integrated")
    print("✓ Configuration files updated")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
