"""
Setup script for testing environment.
Installs dependencies, creates test data, and configures testing environment.
"""

import os
import sys
import subprocess
import django
from django.core.management import execute_from_command_line

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog_manager.settings.test')
django.setup()

from test_factories import create_blog_scenario, create_performance_test_data


def install_test_dependencies():
    """Install testing dependencies."""
    print("Installing testing dependencies...")
    
    dependencies = [
        'pytest-cov==4.1.0',
        'coverage==7.3.2',
        'factory-boy==3.3.0',
        'faker==20.1.0',
        'pytest-mock==3.12.0',
        'pytest-xdist==3.5.0',
        'locust==2.17.0'
    ]
    
    for dep in dependencies:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', dep], check=True)
            print(f"✓ Installed {dep}")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {dep}: {e}")
            return False
    
    return True


def setup_test_database():
    """Setup test database with migrations."""
    print("Setting up test database...")
    
    try:
        # Run migrations
        execute_from_command_line(['manage.py', 'migrate', '--settings=blog_manager.settings.test'])
        print("✓ Database migrations completed")
        return True
    except Exception as e:
        print(f"✗ Database setup failed: {e}")
        return False


def create_test_data():
    """Create test data for testing."""
    print("Creating test data...")
    
    try:
        # Create basic blog scenario
        scenario = create_blog_scenario()
        print(f"✓ Created blog scenario with {len(scenario['writers'])} writers and {len(scenario['posts'])} posts")
        
        # Create performance test data
        post_count = create_performance_test_data()
        print(f"✓ Created performance test data with {post_count} posts")
        
        return True
    except Exception as e:
        print(f"✗ Test data creation failed: {e}")
        return False


def setup_test_configuration():
    """Setup test configuration files."""
    print("Setting up test configuration...")
    
    # Create pytest.ini if it doesn't exist
    pytest_config = """[tool:pytest]
DJANGO_SETTINGS_MODULE = blog_manager.settings.test
python_files = tests.py test_*.py *_tests.py
addopts = --tb=short --strict-markers --cov=. --cov-report=html --cov-report=term-missing --cov-fail-under=85
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    performance: marks tests as performance tests
    unit: marks tests as unit tests
"""
    
    if not os.path.exists('pytest.ini'):
        with open('pytest.ini', 'w') as f:
            f.write(pytest_config)
        print("✓ Created pytest.ini configuration")
    
    # Create .coveragerc for coverage configuration
    coverage_config = """[run]
source = .
omit = 
    */migrations/*
    */venv/*
    */env/*
    manage.py
    */settings/*
    */tests/*
    test_*.py
    *_test.py
    conftest.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    class .*\\(Protocol\\):
    @(abc\\.)?abstractmethod

[html]
directory = htmlcov
"""
    
    if not os.path.exists('.coveragerc'):
        with open('.coveragerc', 'w') as f:
            f.write(coverage_config)
        print("✓ Created .coveragerc configuration")
    
    return True


def verify_test_setup():
    """Verify that test setup is correct."""
    print("Verifying test setup...")
    
    checks = []
    
    # Check if pytest is available
    try:
        subprocess.run(['pytest', '--version'], check=True, capture_output=True)
        checks.append(("pytest", True))
    except (subprocess.CalledProcessError, FileNotFoundError):
        checks.append(("pytest", False))
    
    # Check if coverage is available
    try:
        subprocess.run(['coverage', '--version'], check=True, capture_output=True)
        checks.append(("coverage", True))
    except (subprocess.CalledProcessError, FileNotFoundError):
        checks.append(("coverage", False))
    
    # Check if locust is available
    try:
        subprocess.run(['locust', '--version'], check=True, capture_output=True)
        checks.append(("locust", True))
    except (subprocess.CalledProcessError, FileNotFoundError):
        checks.append(("locust", False))
    
    # Check if test files exist
    test_files = [
        'test_integration_workflows.py',
        'test_performance_load.py',
        'test_factories.py',
        'accounts/test_comprehensive.py',
        'posts/test_comprehensive.py',
        'moderation/test_comprehensive.py'
    ]
    
    for test_file in test_files:
        exists = os.path.exists(test_file)
        checks.append((f"test file: {test_file}", exists))
    
    # Print results
    all_passed = True
    for check_name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed


def main():
    """Main setup function."""
    print("=" * 60)
    print("ENHANCED FINTALK PLATFORM - TEST SETUP")
    print("=" * 60)
    
    steps = [
        ("Installing test dependencies", install_test_dependencies),
        ("Setting up test database", setup_test_database),
        ("Creating test data", create_test_data),
        ("Setting up test configuration", setup_test_configuration),
        ("Verifying test setup", verify_test_setup)
    ]
    
    all_success = True
    
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        try:
            success = step_func()
            if not success:
                all_success = False
                print(f"✗ {step_name} failed")
            else:
                print(f"✓ {step_name} completed")
        except Exception as e:
            print(f"✗ {step_name} failed with error: {e}")
            all_success = False
    
    print("\n" + "=" * 60)
    if all_success:
        print("✓ TEST SETUP COMPLETED SUCCESSFULLY")
        print("\nYou can now run tests with:")
        print("  python run_comprehensive_tests.py")
        print("  pytest")
        print("  locust -f test_performance_load.py --host=http://localhost:8000")
    else:
        print("✗ TEST SETUP FAILED")
        print("Please check the errors above and try again.")
    
    print("=" * 60)
    
    return all_success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)