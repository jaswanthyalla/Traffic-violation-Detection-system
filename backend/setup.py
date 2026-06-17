#!/usr/bin/env python3
"""
Quick Start Script for Traffic Violation Detection System
Run this to set up and test the system
"""

import os
import sys
import subprocess
from pathlib import Path

class SetupWizard:
    def __init__(self):
        self.project_root = Path(__file__).parent
        
    def print_header(self):
        print("=" * 70)
        print("   Traffic Violation Detection System - Setup Wizard".center(70))
        print("=" * 70)
        print()
    
    def check_python_version(self):
        print("✓ Checking Python version...")
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print(f"✗ Python 3.8+ required, found Python {version.major}.{version.minor}")
            return False
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} detected")
        return True
    
    def check_dependencies(self):
        print("\n✓ Checking dependencies...")
        required_packages = [
            'cv2',
            'ultralytics',
            'numpy',
            'torch',
            'flask',
            'PIL'
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package)
                print(f"  ✓ {package}")
            except ImportError:
                print(f"  ✗ {package} (missing)")
                missing.append(package)
        
        if missing:
            print(f"\n⚠ Missing packages: {', '.join(missing)}")
            print("Install with: pip install -r requirements.txt")
            return False
        return True
    
    def check_directories(self):
        print("\n✓ Checking directory structure...")
        required_dirs = [
            'data/videos',
            'models',
            'src',
            'output/screenshots',
            'output/logs',
            'templates',
            'static/css',
            'static/js'
        ]
        
        all_exist = True
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if full_path.exists():
                print(f"  ✓ {dir_path}")
            else:
                print(f"  ✗ {dir_path} (missing)")
                all_exist = False
        
        return all_exist
    
    def check_files(self):
        print("\n✓ Checking required files...")
        required_files = [
            'app.py',
            'web_app.py',
            'config.yaml',
            'requirements.txt',
            'src/detection.py',
            'src/video_reader.py',
            'src/helmet_check.py',
            'src/rider_count.py',
            'src/plate_detection.py',
            'src/ocr_reader.py',
            'src/violation_logic.py',
            'templates/dashboard.html',
            'static/css/style.css',
            'static/js/dashboard.js'
        ]
        
        all_exist = True
        for file_path in required_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                print(f"  ✓ {file_path}")
            else:
                print(f"  ✗ {file_path} (missing)")
                all_exist = False
        
        return all_exist
    
    def run_checks(self):
        self.print_header()
        
        checks = [
            ("Python Version", self.check_python_version),
            ("Directory Structure", self.check_directories),
            ("Required Files", self.check_files),
            ("Python Packages", self.check_dependencies)
        ]
        
        results = []
        for name, check_func in checks:
            try:
                result = check_func()
                results.append((name, result))
            except Exception as e:
                print(f"✗ Error checking {name}: {e}")
                results.append((name, False))
        
        print("\n" + "=" * 70)
        print("Summary:")
        all_passed = True
        for name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"  {status}: {name}")
            if not result:
                all_passed = False
        
        print("=" * 70 + "\n")
        return all_passed
    
    def print_next_steps(self):
        print("📋 Next Steps:")
        print("\n1. Prepare your data:")
        print("   - Place traffic video in: data/videos/traffic_sample.mp4")
        print("   - Download YOLO models to: models/")
        print()
        print("2. Configure the system:")
        print("   - Edit config.yaml with your settings")
        print("   - Adjust detection parameters as needed")
        print()
        print("3. Run the detection system:")
        print("   - Terminal 1: python app.py")
        print("   - This will process the video and store violations")
        print()
        print("4. Start the web dashboard:")
        print("   - Terminal 2: python web_app.py")
        print("   - Open browser: http://localhost:5000")
        print()
        print("5. Monitor violations:")
        print("   - View real-time violations in the dashboard")
        print("   - Update violation status")
        print("   - View screenshots and details")
        print()
    
    def main(self):
        all_passed = self.run_checks()
        
        if not all_passed:
            print("⚠ Some checks failed. Please fix the issues and try again.")
            print("See README.md for detailed setup instructions.")
            return 1
        
        print("✓ All checks passed! System is ready to use.\n")
        self.print_next_steps()
        
        return 0

if __name__ == '__main__':
    wizard = SetupWizard()
    sys.exit(wizard.main())
