#!/usr/bin/env python3
"""
Railway Deployment Verification Script
Run this before deploying to ensure everything is ready.
"""

import json
import os
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists and report status."""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} - NOT FOUND")
        return False

def validate_json(filepath):
    """Validate JSON file syntax."""
    try:
        with open(filepath, 'r') as f:
            json.load(f)
        print(f"✅ JSON Valid: {filepath}")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ JSON Invalid: {filepath} - {e}")
        return False
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        return False

def check_requirements():
    """Check if requirements.txt has essential packages."""
    try:
        with open('requirements.txt', 'r') as f:
            content = f.read()
        
        required_packages = ['fastapi', 'uvicorn', 'pymongo', 'python-jose', 'faiss-cpu']
        missing = []
        
        for package in required_packages:
            if package not in content:
                missing.append(package)
        
        if not missing:
            print("✅ All essential packages found in requirements.txt")
            return True
        else:
            print(f"❌ Missing packages in requirements.txt: {', '.join(missing)}")
            return False
    except FileNotFoundError:
        print("❌ requirements.txt not found")
        return False

def main():
    print("🚀 Railway Deployment Verification\n")
    
    all_good = True
    
    # Check essential files
    files_to_check = [
        ('Procfile', 'Railway start command'),
        ('requirements.txt', 'Python dependencies'),
        ('run.py', 'Application entry point'),
        ('.env.example', 'Environment template'),
        ('README.md', 'Documentation')
    ]
    
    for filepath, description in files_to_check:
        if not check_file_exists(filepath, description):
            all_good = False
    
    # Check JSON files
    json_files = ['railway.json']
    for json_file in json_files:
        if os.path.exists(json_file):
            if not validate_json(json_file):
                all_good = False
    
    # Check requirements
    if not check_requirements():
        all_good = False
    
    # Check if app directory exists
    if not os.path.exists('app'):
        print("❌ App directory not found")
        all_good = False
    else:
        print("✅ App directory exists")
    
    print("\n" + "="*50)
    if all_good:
        print("🎉 All checks passed! Ready for Railway deployment.")
        print("\nNext steps:")
        print("1. git add .")
        print("2. git commit -m 'Prepare for Railway deployment'")
        print("3. git push origin main")
        print("4. Deploy on Railway dashboard")
    else:
        print("❌ Some issues found. Please fix before deploying.")
        sys.exit(1)

if __name__ == "__main__":
    main()
