#!/usr/bin/env python3
"""
Test Script for Traffic Violation Detection System
Tests individual components
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test if all modules can be imported"""
    print("Testing imports...")
    try:
        from video_reader import VideoReader
        print("  ✓ VideoReader imported")
        
        from detection import ObjectDetector
        print("  ✓ ObjectDetector imported")
        
        from helmet_check import HelmetChecker
        print("  ✓ HelmetChecker imported")
        
        from rider_count import RiderCounter
        print("  ✓ RiderCounter imported")
        
        from plate_detection import PlateDetector
        print("  ✓ PlateDetector imported")
        
        from ocr_reader import OCRReader
        print("  ✓ OCRReader imported")
        
        from violation_logic import ViolationDetector
        print("  ✓ ViolationDetector imported")
        
        return True
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        return False

def test_database():
    """Test database initialization"""
    print("\nTesting database...")
    try:
        from violation_logic import ViolationDetector
        
        # Test database creation
        detector = ViolationDetector('test_violations.db')
        print("  ✓ Database initialized")
        
        # Test recording a violation
        test_violation = {
            'type': 'test',
            'description': 'Test violation',
            'confidence': 0.95,
            'plate_number': 'TEST001'
        }
        violation_id = detector.record_violation(test_violation)
        
        if violation_id > 0:
            print(f"  ✓ Violation recorded (ID: {violation_id})")
        else:
            print("  ✗ Failed to record violation")
            return False
        
        # Test retrieving violations
        violations = detector.get_recent_violations(limit=1)
        if violations:
            print(f"  ✓ Retrieved {len(violations)} violation(s)")
        else:
            print("  ✗ Failed to retrieve violations")
            return False
        
        # Cleanup
        if os.path.exists('test_violations.db'):
            os.remove('test_violations.db')
        print("  ✓ Test database cleaned up")
        
        return True
    except Exception as e:
        print(f"  ✗ Database test error: {e}")
        return False

def test_components():
    """Test individual components"""
    print("\nTesting components...")
    
    try:
        from helmet_check import HelmetChecker
        helmet_checker = HelmetChecker()
        print("  ✓ HelmetChecker initialized")
        
        from rider_count import RiderCounter
        rider_counter = RiderCounter()
        print("  ✓ RiderCounter initialized")
        
        from ocr_reader import OCRReader
        ocr_reader = OCRReader()
        print("  ✓ OCRReader initialized")
        
        from violation_logic import ViolationDetector
        detector = ViolationDetector('test_components.db')  # Use temporary DB for testing
        print("  ✓ ViolationDetector initialized")
        
        # Test violation detection logic
        test_frame_data = {
            'detections': [],
            'helmet_violations': [],
            'rider_count': {'count': 1},
            'plates': []
        }
        violations = detector.detect_violations(test_frame_data)
        print(f"  ✓ Violation detection logic works ({len(violations)} violations)")
        
        return True
    except Exception as e:
        print(f"  ✗ Component test error: {e}")
        return False

def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")
    try:
        import yaml
        
        config_path = 'config.yaml'
        if not os.path.exists(config_path):
            print(f"  ✗ Configuration file not found: {config_path}")
            return False
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if config:
            print("  ✓ Configuration loaded successfully")
            print(f"    - Detection model: {config.get('detection_model')}")
            print(f"    - Video path: {config.get('video_path')}")
            print(f"    - Database: {config.get('database_path')}")
            return True
        else:
            print("  ✗ Configuration file is empty")
            return False
    except Exception as e:
        print(f"  ✗ Configuration test error: {e}")
        return False

def test_directory_structure():
    """Test directory structure"""
    print("\nTesting directory structure...")
    try:
        required_dirs = [
            'data',
            'data/videos',
            'models',
            'src',
            'output',
            'output/screenshots',
            'output/logs',
            'templates',
            'static',
            'static/css',
            'static/js'
        ]
        
        all_exist = True
        for dir_path in required_dirs:
            if os.path.isdir(dir_path):
                print(f"  ✓ {dir_path}")
            else:
                print(f"  ✗ {dir_path}")
                all_exist = False
        
        return all_exist
    except Exception as e:
        print(f"  ✗ Directory structure test error: {e}")
        return False

def main():
    print("=" * 60)
    print("Traffic Violation Detection System - Test Suite".center(60))
    print("=" * 60)
    
    tests = [
        ("Directory Structure", test_directory_structure),
        ("Configuration", test_config),
        ("Imports", test_imports),
        ("Components", test_components),
        ("Database", test_database)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    all_passed = True
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    
    # Cleanup test databases
    if os.path.exists('test_violations.db'):
        os.remove('test_violations.db')
    if os.path.exists('test_components.db'):
        os.remove('test_components.db')
    
    if all_passed:
        print("\n✓ All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("  1. Run: python app.py          (Detection system)")
        print("  2. Run: python web_app.py      (Web dashboard)")
        print("  3. Open: http://localhost:5000 (Dashboard)")
        return 0
    else:
        print("\n✗ Some tests failed. Please fix the issues and try again.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
