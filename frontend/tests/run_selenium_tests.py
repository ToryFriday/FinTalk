#!/usr/bin/env python3
"""
Selenium Test Runner for Blog Post Manager Frontend

This script runs the Selenium UI tests for the blog post manager application.
It includes options for different test configurations and environments.
"""

import os
import sys
import subprocess
import argparse
import time
import requests
from pathlib import Path


def check_frontend_server(url, timeout=30):
    """Check if frontend server is running"""
    print(f"Checking if frontend server is running at {url}...")
    
    for i in range(timeout):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print("✓ Frontend server is running")
                return True
        except requests.exceptions.RequestException:
            pass
        
        if i < timeout - 1:
            print(f"Waiting for frontend server... ({i+1}/{timeout})")
            time.sleep(1)
    
    print("✗ Frontend server is not responding")
    return False


def check_backend_server(url, timeout=30):
    """Check if backend server is running"""
    print(f"Checking if backend server is running at {url}...")
    
    for i in range(timeout):
        try:
            response = requests.get(f"{url}/api/posts/", timeout=5)
            if response.status_code in [200, 404]:  # 404 is OK if no posts exist
                print("✓ Backend server is running")
                return True
        except requests.exceptions.RequestException:
            pass
        
        if i < timeout - 1:
            print(f"Waiting for backend server... ({i+1}/{timeout})")
            time.sleep(1)
    
    print("✗ Backend server is not responding")
    return False


def run_tests(args):
    """Run the Selenium tests"""
    # Set up environment variables
    env = os.environ.copy()
    env['FRONTEND_URL'] = args.frontend_url
    env['API_URL'] = args.api_url
    
    # Create test reports directory
    reports_dir = Path(__file__).parent / "test_reports"
    reports_dir.mkdir(exist_ok=True)
    
    # Build pytest command
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/selenium/",
        "-v",
        "--tb=short",
        f"--html=test_reports/selenium_report.html",
        "--self-contained-html"
    ]
    
    # Add test selection options
    if args.test_file:
        cmd.append(f"tests/selenium/{args.test_file}")
    
    if args.test_function:
        cmd.extend(["-k", args.test_function])
    
    if args.markers:
        cmd.extend(["-m", args.markers])
    
    # Add browser options
    if args.headless:
        env['SELENIUM_HEADLESS'] = 'true'
    
    if args.browser:
        env['SELENIUM_BROWSER'] = args.browser
    
    # Add parallel execution if requested
    if args.parallel and args.parallel > 1:
        cmd.extend(["-n", str(args.parallel)])
    
    # Run tests
    print(f"Running command: {' '.join(cmd)}")
    print(f"Environment: FRONTEND_URL={env['FRONTEND_URL']}, API_URL={env['API_URL']}")
    
    try:
        result = subprocess.run(cmd, env=env, cwd=Path(__file__).parent.parent)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Run Selenium UI tests for Blog Post Manager")
    
    # Server configuration
    parser.add_argument(
        "--frontend-url", 
        default="http://localhost:3000",
        help="Frontend server URL (default: http://localhost:3000)"
    )
    parser.add_argument(
        "--api-url", 
        default="http://localhost:8000",
        help="Backend API URL (default: http://localhost:8000)"
    )
    
    # Test selection
    parser.add_argument(
        "--test-file", 
        help="Run specific test file (e.g., test_post_crud.py)"
    )
    parser.add_argument(
        "--test-function", 
        help="Run specific test function (e.g., test_create_post)"
    )
    parser.add_argument(
        "--markers", 
        help="Run tests with specific markers (e.g., 'crud', 'validation')"
    )
    
    # Browser configuration
    parser.add_argument(
        "--browser", 
        choices=["chrome", "firefox", "edge"],
        default="chrome",
        help="Browser to use for tests (default: chrome)"
    )
    parser.add_argument(
        "--headless", 
        action="store_true",
        help="Run browser in headless mode"
    )
    
    # Execution options
    parser.add_argument(
        "--parallel", 
        type=int,
        help="Run tests in parallel (requires pytest-xdist)"
    )
    parser.add_argument(
        "--skip-server-check", 
        action="store_true",
        help="Skip checking if servers are running"
    )
    
    args = parser.parse_args()
    
    # Check if servers are running (unless skipped)
    if not args.skip_server_check:
        if not check_frontend_server(args.frontend_url):
            print("\nPlease start the frontend server before running tests:")
            print("  cd frontend && npm start")
            return 1
        
        if not check_backend_server(args.api_url):
            print("\nPlease start the backend server before running tests:")
            print("  cd backend && python manage.py runserver")
            return 1
    
    # Run tests
    return run_tests(args)


if __name__ == "__main__":
    sys.exit(main())