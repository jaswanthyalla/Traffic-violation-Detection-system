#!/usr/bin/env python3
"""
Utility Script for Traffic Violation Detection System
Provides helpful commands for system maintenance
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import get_database_manager

class ViolationUtility:
    """Utility functions for violation management"""
    
    def __init__(self, db_path='database/violations.db'):
        self.db = get_database_manager(db_path)
    
    def show_stats(self):
        """Display violation statistics"""
        print("\n" + "=" * 60)
        print("Violation Statistics".center(60))
        print("=" * 60)
        
        try:
            stats = self.db.get_statistics()
            
            print(f"Total Violations: {stats.get('total_violations', 0)}")
            
            # By type
            if stats.get('violations_by_type'):
                print("\nViolations by Type:")
                for vtype, count in stats['violations_by_type'].items():
                    print(f"  {vtype}: {count}")
            
            # By status
            if stats.get('violations_by_status'):
                print("\nViolations by Status:")
                for status, count in stats['violations_by_status'].items():
                    print(f"  {status}: {count}")
            
            print(f"\nViolations (Last 24 hours): {stats.get('last_24h_count', 0)}")
            
            if stats.get('avg_confidence'):
                print(f"Average Confidence: {stats['avg_confidence']:.2%}")
            
            print("\n" + "=" * 60)
        except Exception as e:
            print(f"Error: {e}")
    
    def recent_violations(self, limit=10, hours=None):
        """Show recent violations"""
        print("\n" + "=" * 100)
        print(f"Recent Violations (Last {limit})".center(100))
        print("=" * 100)
        
        try:
            violations = self.db.get_recent_violations(limit, hours)
            
            if not violations:
                print("No violations found.")
                return
            
            for row in violations:
                print(f"\nID: {row['id']}")
                print(f"  Time: {row['timestamp']}")
                print(f"  Type: {row['violation_type']}")
                print(f"  Description: {row['description']}")
                print(f"  Plate: {row['plate_number']}")
                print(f"  Confidence: {row['confidence']:.2%}" if row.get('confidence') else "  Confidence: N/A")
                print(f"  Status: {row['status']}")
                print(f"  Screenshot: {row['screenshot_path']}")
            
            print("\n" + "=" * 100)
        except Exception as e:
            print(f"Error: {e}")
    
    def export_violations(self, filename='violations_export.csv'):
        """Export violations to CSV"""
        print(f"\nExporting violations to {filename}...")
        
        try:
            self.db.export_to_csv(filename)
            print(f"✓ Export completed successfully")
        except Exception as e:
            print(f"Error: {e}")
    
    def cleanup_old_violations(self, days=30, dry_run=True):
        """Remove violations older than specified days"""
        try:
            if dry_run:
                # Just get count
                cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
                violations = self.db.get_recent_violations(limit=99999, hours=None)
                count = sum(1 for v in violations if v['timestamp'] < cutoff_date)
                
                if count == 0:
                    print(f"No violations older than {days} days found.")
                    return
                
                print(f"Would delete {count} violations older than {days} days.")
                print("Run with --confirm to actually delete.")
            else:
                # Actually delete
                self.db.delete_old_violations(days)
                print(f"✓ Deleted violations older than {days} days.")
        except Exception as e:
            print(f"Error: {e}")
    
    def update_status(self, violation_id, new_status):
        """Update violation status"""
        try:
            if self.db.update_violation_status(violation_id, new_status):
                print(f"✓ Updated violation {violation_id} status to {new_status}")
            else:
                print(f"✗ Violation {violation_id} not found")
        except Exception as e:
            print(f"Error: {e}")
    
    def search_by_plate(self, plate_number):
        """Search violations by license plate"""
        print(f"\nSearching for violations with plate: {plate_number}")
        print("=" * 100)
        
        try:
            violations = self.db.search_by_plate(plate_number)
            
            if not violations:
                print(f"No violations found for plate: {plate_number}")
                return
            
            print(f"Found {len(violations)} violation(s):\n")
            
            for row in violations:
                print(f"ID: {row['id']}")
                print(f"  Time: {row['timestamp']}")
                print(f"  Type: {row['violation_type']}")
                print(f"  Status: {row['status']}")
                print()
        except Exception as e:
            print(f"Error: {e}")
    
    def database_info(self):
        """Show database information"""
        print("\n" + "=" * 60)
        print("Database Information".center(60))
        print("=" * 60)
        
        try:
            db_path = self.db.db_path
            
            if not os.path.exists(db_path):
                print(f"Database file not found: {db_path}")
                return
            
            # File size
            size_mb = os.path.getsize(db_path) / (1024 * 1024)
            print(f"Database File: {db_path}")
            print(f"Size: {size_mb:.2f} MB")
            
            # Get statistics
            stats = self.db.get_statistics()
            
            print(f"Total Records: {stats.get('total_violations', 0)}")
            
            # Date range
            violations = self.db.get_recent_violations(limit=99999, hours=None)
            if violations:
                timestamps = [v['timestamp'] for v in violations]
                print(f"Date Range: {min(timestamps)} to {max(timestamps)}")
            
            print(f"Columns: 10 (standard)")
            
            print("=" * 60)
        except Exception as e:
            print(f"Error: {e}")

def show_help():
    """Show help message"""
    print("""
Traffic Violation Detection System - Utility Script

Usage: python utility.py [command] [options]

Commands:
  stats                    Show violation statistics
  recent [limit]          Show recent violations (default: 10)
  export [filename]       Export violations to CSV
  search-plate [plate]    Search violations by license plate
  update [id] [status]    Update violation status
  cleanup [days]          Remove violations older than days (default: 30)
  db-info                 Show database information
  help                    Show this help message

Examples:
  python utility.py stats
  python utility.py recent 20
  python utility.py export violations_backup.csv
  python utility.py search-plate "ABC123"
  python utility.py update 5 processed
  python utility.py cleanup 30
  python utility.py db-info

Status Options:
  pending, processed, dismissed

""")

def main():
    if len(sys.argv) < 2:
        show_help()
        return 0
    
    util = ViolationUtility()
    command = sys.argv[1].lower()
    
    if command == 'stats':
        util.show_stats()
    elif command == 'recent':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        util.recent_violations(limit)
    elif command == 'export':
        filename = sys.argv[2] if len(sys.argv) > 2 else 'violations_export.csv'
        util.export_violations(filename)
    elif command == 'search-plate':
        if len(sys.argv) < 3:
            print("Error: Plate number required")
            return 1
        util.search_by_plate(sys.argv[2])
    elif command == 'update':
        if len(sys.argv) < 4:
            print("Error: Violation ID and status required")
            return 1
        util.update_status(int(sys.argv[2]), sys.argv[3])
    elif command == 'cleanup':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        confirm = '--confirm' in sys.argv
        util.cleanup_old_violations(days, dry_run=not confirm)
    elif command == 'db-info':
        util.database_info()
    elif command in ['help', '-h', '--help']:
        show_help()
    else:
        print(f"Unknown command: {command}")
        show_help()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
