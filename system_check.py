#!/usr/bin/env python3
# System Health Check Script
# Verifies all components of the Feng Shui AI system

import sys
import os
import importlib
import traceback
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"

def print_header(text):
    """Print a formatted header."""
    print(f"\n{BLUE}{'='*70}")
    print(f"{text:^70}")
    print(f"{'='*70}{RESET}\n")

def print_success(text):
    """Print a success message."""
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    """Print an error message."""
    print(f"{RED}✗ {text}{RESET}")

def print_warning(text):
    """Print a warning message."""
    print(f"{YELLOW}⚠ {text}{RESET}")

def print_info(text):
    """Print an info message."""
    print(f"{BLUE}ℹ {text}{RESET}")

def check_python_version():
    """Check Python version."""
    print_header("PYTHON VERSION CHECK")
    version = sys.version
    print(f"Python: {version}")
    
    major, minor = sys.version_info[:2]
    if major > 3 or (major == 3 and minor >= 10):
        print_success(f"Python {major}.{minor} meets production baseline (3.10+)")
        return True
    else:
        print_error(f"Python {major}.{minor} is too old for production (require 3.10+)")
        return False

def check_directory_structure():
    """Check if all required directories exist."""
    print_header("DIRECTORY STRUCTURE CHECK")
    
    backend_path = BACKEND_DIR
    required_dirs = [
        backend_path / "buildings_data",
        backend_path / "dem",
        backend_path / "Hydroshed",
        backend_path / "ndvi",
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if dir_path.exists():
            print_success(f"Directory exists: {dir_path.relative_to(BASE_DIR)}/")
        else:
            print_error(f"Directory missing: {dir_path.relative_to(BASE_DIR)}/")
            all_exist = False
    
    return all_exist

def check_file_existence():
    """Check if all critical files exist."""
    print_header("FILE EXISTENCE CHECK")
    
    required_files = [
        BACKEND_DIR / "app.py",
        BACKEND_DIR / "config.py",
        BACKEND_DIR / "feature_extractor.py",
        BACKEND_DIR / "buildings_data" / "__init__.py",
        BACKEND_DIR / "buildings_data" / "config.py",
        BACKEND_DIR / "buildings_data" / "buildings_service.py",
        BACKEND_DIR / "buildings_data" / "test_buildings.py",
        BACKEND_DIR / "amap_service.py",
        BACKEND_DIR / "scorer.py",
    ]
    
    all_exist = True
    for file_path in required_files:
        if file_path.exists():
            print_success(f"File exists: {file_path.relative_to(BASE_DIR)}")
        else:
            print_error(f"File missing: {file_path.relative_to(BASE_DIR)}")
            all_exist = False
    
    return all_exist

def check_imports():
    """Check if all modules can be imported."""
    print_header("IMPORT CHECK")
    
    modules_to_check = [
        ("buildings_data", "BuildingsService"),
        ("buildings_data.config", "BuildingsConfig"),
        ("buildings_data.buildings_service", "BuildingsService"),
        ("amap_service", "geocode_address"),
        ("feature_extractor", "extract_features"),
        ("config", "Config"),
    ]
    
    all_imported = True
    for module_name, item_name in modules_to_check:
        try:
            module = importlib.import_module(module_name)
            item = getattr(module, item_name, None)
            if item is not None:
                print_success(f"Import successful: {module_name}.{item_name}")
            else:
                print_warning(f"Module imported but {item_name} not found in {module_name}")
        except ImportError as e:
            print_error(f"Import failed: {module_name}")
            print(f"       Error: {str(e)}")
            all_imported = False
        except Exception as e:
            print_error(f"Error checking {module_name}: {str(e)}")
            all_imported = False
    
    return all_imported

def check_buildings_service():
    """Check if BuildingsService can be instantiated."""
    print_header("BUILDINGS SERVICE CHECK")
    
    try:
        from buildings_data.buildings_service import BuildingsService
        from buildings_data.config import BuildingsConfig
        
        print_info("Attempting to instantiate BuildingsService...")
        service = BuildingsService()
        print_success(f"BuildingsService instantiated successfully")
        
        # Check if key methods exist
        methods = ['get_building_data', 'calculate_building_harmony_score', '_estimate_building_height']
        for method_name in methods:
            if hasattr(service, method_name):
                print_success(f"Method exists: {method_name}()")
            else:
                print_error(f"Method missing: {method_name}()")
                return False
        
        return True
    except Exception as e:
        print_error(f"BuildingsService check failed")
        print(f"Error: {traceback.format_exc()}")
        return False

def check_feature_extractor():
    """Check if feature_extractor has buildings_service parameter."""
    print_header("FEATURE EXTRACTOR CHECK")
    
    try:
        import inspect
        from feature_extractor import extract_features
        
        # Get function signature
        sig = inspect.signature(extract_features)
        params = list(sig.parameters.keys())
        
        print_info(f"extract_features parameters: {', '.join(params)}")
        
        required_params = ['poi_data', 'road_data', 'longitude', 'latitude', 'radius']
        optional_params = ['dem_service', 'hydrosheds_service', 'buildings_service']
        
        for param in required_params:
            if param in params:
                print_success(f"Required parameter: {param}")
            else:
                print_error(f"Missing required parameter: {param}")
                return False
        
        for param in optional_params:
            if param in params:
                print_success(f"Optional parameter: {param}")
            else:
                print_warning(f"Missing optional parameter: {param}")
        
        return True
    except Exception as e:
        print_error(f"Feature extractor check failed")
        print(f"Error: {traceback.format_exc()}")
        return False

def check_app_integration():
    """Check if app.py imports and initializes BuildingsService."""
    print_header("APP.PY INTEGRATION CHECK")
    
    try:
        with open(BACKEND_DIR / "app.py", "r") as f:
            app_content = f.read()
        
        checks = [
            ("from buildings_data import BuildingsService", "BuildingsService import"),
            ("from buildings_data.config import BuildingsConfig", "BuildingsConfig import"),
            ("BuildingsService()", "BuildingsService instantiation"),
            ("buildings_service=buildings_service", "buildings_service parameter"),
        ]
        
        all_found = True
        for check_string, check_name in checks:
            if check_string in app_content:
                print_success(f"Found: {check_name}")
            else:
                print_error(f"Not found: {check_name}")
                all_found = False
        
        return all_found
    except Exception as e:
        print_error(f"App integration check failed")
        print(f"Error: {str(e)}")
        return False

def check_dependencies():
    """Check if required dependencies are installed."""
    print_header("DEPENDENCY CHECK")
    
    required_packages = [
        ("flask", "Flask"),
        ("flask_cors", "Flask-CORS"),
        ("requests", "Requests"),
        ("dotenv", "Python-dotenv"),
    ]
    
    all_installed = True
    for package_name, display_name in required_packages:
        try:
            importlib.import_module(package_name)
            print_success(f"Installed: {display_name}")
        except ImportError:
            print_error(f"Missing: {display_name}")
            all_installed = False
    
    return all_installed

def generate_summary(results):
    """Generate a summary of all checks."""
    print_header("SYSTEM STATUS SUMMARY")
    
    total_checks = len(results)
    passed_checks = sum(1 for v in results.values() if v)
    failed_checks = total_checks - passed_checks
    
    print(f"Total Checks: {total_checks}")
    print(f"{GREEN}Passed: {passed_checks}{RESET}")
    if failed_checks > 0:
        print(f"{RED}Failed: {failed_checks}{RESET}")
    
    print()
    
    for check_name, result in results.items():
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {check_name}: {status}")
    
    print()
    
    if all(results.values()):
        print(f"{GREEN}{'='*70}")
        print(f"{'✓ ALL SYSTEMS GO! System is ready for production':^70}")
        print(f"{'='*70}{RESET}\n")
        return 0
    else:
        print(f"{RED}{'='*70}")
        print(f"{'✗ System has issues that need to be fixed':^70}")
        print(f"{'='*70}{RESET}\n")
        return 1

def main():
    """Run all system checks."""
    print(f"\n{BLUE}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║         FENG SHUI AI SYSTEM - HEALTH CHECK                        ║")
    print("║                  Buildings Data Integration                        ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{RESET}")
    
    # Add backend directory for imports without changing cwd
    sys.path.insert(0, str(BACKEND_DIR))
    
    results = {
        "Python Version": check_python_version(),
        "Directory Structure": check_directory_structure(),
        "File Existence": check_file_existence(),
        "Module Imports": check_imports(),
        "Buildings Service": check_buildings_service(),
        "Feature Extractor": check_feature_extractor(),
        "App Integration": check_app_integration(),
        "Dependencies": check_dependencies(),
    }
    
    exit_code = generate_summary(results)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
