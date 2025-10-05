"""
Comprehensive test runner for the Enhanced FinTalk Platform.
Runs all tests, generates coverage reports, and validates API documentation.
"""

import os
import sys
import subprocess
import json
from datetime import datetime
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog_manager.settings.test')
django.setup()


class TestRunner:
    """Comprehensive test runner with reporting."""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'unit_tests': {},
            'integration_tests': {},
            'performance_tests': {},
            'coverage': {},
            'api_docs': {},
            'overall_status': 'pending'
        }
    
    def run_unit_tests(self):
        """Run unit tests with coverage."""
        print("=" * 60)
        print("RUNNING UNIT TESTS")
        print("=" * 60)
        
        try:
            # Run pytest with coverage for unit tests
            cmd = [
                'pytest',
                '-m', 'unit or not (integration or performance)',
                '--cov=.',
                '--cov-report=html:htmlcov',
                '--cov-report=json:coverage.json',
                '--cov-report=term-missing',
                '--cov-fail-under=85',
                '--tb=short',
                '-v'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            self.results['unit_tests'] = {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            # Parse coverage results
            if os.path.exists('coverage.json'):
                with open('coverage.json', 'r') as f:
                    coverage_data = json.load(f)
                    self.results['coverage'] = {
                        'total_coverage': coverage_data['totals']['percent_covered'],
                        'lines_covered': coverage_data['totals']['covered_lines'],
                        'lines_missing': coverage_data['totals']['missing_lines'],
                        'files': len(coverage_data['files'])
                    }
            
            print(f"Unit tests: {'PASSED' if result.returncode == 0 else 'FAILED'}")
            if self.results['coverage']:
                print(f"Coverage: {self.results['coverage']['total_coverage']:.1f}%")
            
        except Exception as e:
            self.results['unit_tests'] = {
                'status': 'error',
                'error': str(e)
            }
            print(f"Error running unit tests: {e}")
    
    def run_integration_tests(self):
        """Run integration tests."""
        print("\n" + "=" * 60)
        print("RUNNING INTEGRATION TESTS")
        print("=" * 60)
        
        try:
            cmd = [
                'pytest',
                'test_integration_workflows.py',
                '-m', 'integration',
                '-v',
                '--tb=short'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            self.results['integration_tests'] = {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            print(f"Integration tests: {'PASSED' if result.returncode == 0 else 'FAILED'}")
            
        except Exception as e:
            self.results['integration_tests'] = {
                'status': 'error',
                'error': str(e)
            }
            print(f"Error running integration tests: {e}")
    
    def run_performance_tests(self):
        """Run basic performance tests."""
        print("\n" + "=" * 60)
        print("RUNNING PERFORMANCE TESTS")
        print("=" * 60)
        
        try:
            # Run pytest performance tests
            cmd = [
                'pytest',
                '-m', 'performance',
                '-v',
                '--tb=short'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            self.results['performance_tests'] = {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            print(f"Performance tests: {'PASSED' if result.returncode == 0 else 'FAILED'}")
            
            # Note about Locust tests
            print("\nNote: For comprehensive load testing, run:")
            print("locust -f test_performance_load.py --host=http://localhost:8000")
            
        except Exception as e:
            self.results['performance_tests'] = {
                'status': 'error',
                'error': str(e)
            }
            print(f"Error running performance tests: {e}")
    
    def validate_api_documentation(self):
        """Validate and update API documentation."""
        print("\n" + "=" * 60)
        print("VALIDATING API DOCUMENTATION")
        print("=" * 60)
        
        try:
            # Run documentation generator
            cmd = ['python', 'generate_api_docs.py']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            self.results['api_docs'] = {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            print(f"API documentation: {'UPDATED' if result.returncode == 0 else 'FAILED'}")
            
        except Exception as e:
            self.results['api_docs'] = {
                'status': 'error',
                'error': str(e)
            }
            print(f"Error updating API documentation: {e}")
    
    def check_test_requirements(self):
        """Check if all test requirements are met."""
        print("\n" + "=" * 60)
        print("CHECKING TEST REQUIREMENTS")
        print("=" * 60)
        
        requirements = {
            'minimum_coverage': 85,
            'required_test_files': [
                'accounts/test_comprehensive.py',
                'posts/test_comprehensive.py',
                'moderation/test_comprehensive.py',
                'test_integration_workflows.py'
            ],
            'required_test_types': ['unit', 'integration', 'performance']
        }
        
        # Check coverage requirement
        if self.results['coverage']:
            coverage = self.results['coverage']['total_coverage']
            if coverage >= requirements['minimum_coverage']:
                print(f"✓ Coverage requirement met: {coverage:.1f}% >= {requirements['minimum_coverage']}%")
            else:
                print(f"✗ Coverage requirement not met: {coverage:.1f}% < {requirements['minimum_coverage']}%")
        
        # Check test files exist
        for test_file in requirements['required_test_files']:
            if os.path.exists(test_file):
                print(f"✓ Test file exists: {test_file}")
            else:
                print(f"✗ Test file missing: {test_file}")
        
        # Check test types
        for test_type in requirements['required_test_types']:
            if test_type in self.results and self.results[test_type].get('status') == 'passed':
                print(f"✓ {test_type.title()} tests passed")
            else:
                print(f"✗ {test_type.title()} tests failed or not run")
    
    def generate_test_report(self):
        """Generate comprehensive test report."""
        print("\n" + "=" * 60)
        print("GENERATING TEST REPORT")
        print("=" * 60)
        
        # Determine overall status
        all_passed = all(
            result.get('status') == 'passed' 
            for result in [
                self.results['unit_tests'],
                self.results['integration_tests'],
                self.results['performance_tests'],
                self.results['api_docs']
            ]
        )
        
        coverage_met = (
            self.results['coverage'] and 
            self.results['coverage']['total_coverage'] >= 85
        )
        
        self.results['overall_status'] = 'passed' if all_passed and coverage_met else 'failed'
        
        # Save detailed results
        with open('test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Generate summary report
        report = []
        report.append("# Test Report Summary")
        report.append(f"**Generated:** {self.results['timestamp']}")
        report.append(f"**Overall Status:** {'✓ PASSED' if self.results['overall_status'] == 'passed' else '✗ FAILED'}")
        report.append("")
        
        # Test results
        report.append("## Test Results")
        report.append("")
        
        test_types = ['unit_tests', 'integration_tests', 'performance_tests', 'api_docs']
        for test_type in test_types:
            result = self.results[test_type]
            status = result.get('status', 'not_run')
            status_icon = '✓' if status == 'passed' else '✗' if status == 'failed' else '⚠'
            report.append(f"- **{test_type.replace('_', ' ').title()}:** {status_icon} {status.upper()}")
        
        report.append("")
        
        # Coverage information
        if self.results['coverage']:
            coverage = self.results['coverage']
            report.append("## Coverage Report")
            report.append("")
            report.append(f"- **Total Coverage:** {coverage['total_coverage']:.1f}%")
            report.append(f"- **Lines Covered:** {coverage['lines_covered']}")
            report.append(f"- **Lines Missing:** {coverage['lines_missing']}")
            report.append(f"- **Files Analyzed:** {coverage['files']}")
            report.append("")
        
        # Recommendations
        report.append("## Recommendations")
        report.append("")
        
        if self.results['overall_status'] == 'passed':
            report.append("✓ All tests passed and coverage requirements met.")
            report.append("✓ API documentation is up to date.")
            report.append("✓ Ready for deployment.")
        else:
            report.append("⚠ Some tests failed or coverage is insufficient.")
            report.append("- Review failed tests and fix issues")
            report.append("- Add tests to improve coverage")
            report.append("- Update API documentation if needed")
        
        report.append("")
        report.append("## Next Steps")
        report.append("")
        report.append("1. Review detailed test results in `test_results.json`")
        report.append("2. Check HTML coverage report in `htmlcov/index.html`")
        report.append("3. Run load tests: `locust -f test_performance_load.py`")
        report.append("4. Update API documentation if endpoints changed")
        
        # Save report
        with open('TEST_REPORT.md', 'w') as f:
            f.write('\n'.join(report))
        
        print("Test report generated: TEST_REPORT.md")
        print("Detailed results saved: test_results.json")
        
        if self.results['coverage']:
            print(f"HTML coverage report: htmlcov/index.html")
    
    def run_all_tests(self):
        """Run all tests and generate comprehensive report."""
        print("Enhanced FinTalk Platform - Comprehensive Test Suite")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all test suites
        self.run_unit_tests()
        self.run_integration_tests()
        self.run_performance_tests()
        self.validate_api_documentation()
        
        # Check requirements and generate report
        self.check_test_requirements()
        self.generate_test_report()
        
        print("\n" + "=" * 60)
        print("TEST SUITE COMPLETED")
        print("=" * 60)
        print(f"Overall Status: {'PASSED' if self.results['overall_status'] == 'passed' else 'FAILED'}")
        
        if self.results['coverage']:
            print(f"Coverage: {self.results['coverage']['total_coverage']:.1f}%")
        
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return self.results['overall_status'] == 'passed'


def main():
    """Main function to run comprehensive tests."""
    runner = TestRunner()
    success = runner.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()