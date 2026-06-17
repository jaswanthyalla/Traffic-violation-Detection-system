#!/usr/bin/env python3
"""
System verification script - checks if all components are properly configured
"""
import os
import sys
import json
from pathlib import Path

def check_structure():
    """Check if all required directories exist"""
    print("\n" + "="*60)
    print("DIRECTORY STRUCTURE CHECK")
    print("="*60)
    
    dirs_to_check = [
        'src',
        'data',
        'data/videos',
        'output',
        'output/screenshots',
        'output/logs',
        'database',
        'templates',
        'static',
        'static/css',
        'static/js'
    ]
    
    all_exist = True
    for dir_path in dirs_to_check:
        exists = os.path.exists(dir_path)
        status = "✓" if exists else "✗"
        print(f"  {status} {dir_path}")
        if not exists:
            all_exist = False
    
    return all_exist

def check_files():
    """Check if all required files exist"""
    print("\n" + "="*60)
    print("FILE EXISTENCE CHECK")
    print("="*60)
    
    files_to_check = {
        'Core Files': [
            'web_app.py',
            'app.py',
            'process_traffic_video.py'
        ],
        'Source Modules': [
            'src/database.py',
            'src/detection.py',
            'src/helmet_check.py',
            'src/ocr_reader.py',
            'src/plate_detection.py',
            'src/rider_count.py',
            'src/video_reader.py',
            'src/violation_logic.py'
        ],
        'Web Files': [
            'templates/dashboard.html',
            'static/css/style.css',
            'static/js/dashboard.js'
        ],
        'Config Files': [
            'requirements.txt',
            'config.yaml'
        ]
    }
    
    all_exist = True
    for category, files in files_to_check.items():
        print(f"\n  {category}:")
        for file_path in files:
            exists = os.path.exists(file_path)
            status = "✓" if exists else "✗"
            print(f"    {status} {file_path}")
            if not exists:
                all_exist = False
    
    return all_exist

def check_dependencies():
    """Check if required Python packages are installed"""
    print("\n" + "="*60)
    print("PYTHON DEPENDENCIES CHECK")
    print("="*60)
    
    required_packages = {
        'cv2': 'opencv-python',
        'flask': 'flask',
        'flask_cors': 'flask-cors',
        'yaml': 'pyyaml',
        'numpy': 'numpy',
        'PIL': 'Pillow'
    }
    
    missing = []
    for module, package in required_packages.items():
        try:
            __import__(module)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package}")
            missing.append(package)
    
    return len(missing) == 0, missing

def check_models():
    """Check if YOLOv8 models are available"""
    print("\n" + "="*60)
    print("MODEL FILES CHECK")
    print("="*60)
    
    models_to_check = {
        'Main Detection': 'yolov8n.pt',
        'Helmet Detection': 'models/yolo_helmet.pt',
        'Plate Detection': 'models/yolo_plate.pt'
    }
    
    all_exist = True
    for name, model_path in models_to_check.items():
        exists = os.path.exists(model_path)
        status = "✓" if exists else "✗"
        print(f"  {status} {name}: {model_path}")
        if not exists:
            all_exist = False
    
    return all_exist

def check_database():
    """Check database configuration"""
    print("\n" + "="*60)
    print("DATABASE CHECK")
    print("="*60)
    
    db_path = 'database/violations.db'
    db_exists = os.path.exists(db_path)
    
    if db_exists:
        size = os.path.getsize(db_path) / 1024
        print(f"  ✓ Database exists ({size:.2f} KB)")
    else:
        print(f"  ✗ Database not found (will be created on first run)")
    
    return True

def check_videos():
    """Check for sample videos"""
    print("\n" + "="*60)
    print("SAMPLE VIDEOS CHECK")
    print("="*60)
    
    videos_dir = 'data/videos'
    
    if os.path.exists(videos_dir):
        videos = [f for f in os.listdir(videos_dir) 
                 if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'))]
        
        if videos:
            print(f"  ✓ Found {len(videos)} video(s):")
            for video in videos:
                path = os.path.join(videos_dir, video)
                size = os.path.getsize(path) / (1024*1024)
                print(f"    - {video} ({size:.2f} MB)")
        else:
            print(f"  ✗ No videos found in {videos_dir}")
            print(f"    Tip: Place a traffic video in {videos_dir}/")
    
    return True

def generate_report(all_checks):
    """Generate final report"""
    print("\n" + "="*60)
    print("SUMMARY REPORT")
    print("="*60)
    
    passed = sum(1 for v in all_checks.values() if v)
    total = len(all_checks)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All checks passed! System is ready.")
        print("\nNext steps:")
        print("  1. Start the dashboard: python web_app.py")
        print("  2. Open browser: http://localhost:5000")
        print("  3. Upload a video or run: python process_traffic_video.py <video>")
        return True
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        print("\nTroubleshooting:")
        if not all_checks.get('directories', False):
            print("  - Create missing directories")
        if not all_checks.get('files', False):
            print("  - Ensure all source files are present")
        if not all_checks.get('dependencies', False):
            print("  - Run: pip install -r requirements.txt")
        if not all_checks.get('models', False):
            print("  - Download YOLOv8 models to the specified paths")
        return False

def main():
    """Run all checks"""
    print("\n" + "="*60)
    print("TRAFFIC VIOLATION DETECTION SYSTEM - VERIFICATION")
    print("="*60)
    
    all_checks = {
        'directories': check_structure(),
        'files': check_files(),
        'models': check_models(),
        'database': check_database(),
        'videos': check_videos()
    }
    
    # Check dependencies separately to handle errors
    deps_ok, missing = check_dependencies()
    all_checks['dependencies'] = deps_ok
    
    if not deps_ok:
        print(f"\n  Install missing packages: pip install {' '.join(missing)}")
    
    success = generate_report(all_checks)
    
    print("="*60 + "\n")
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
