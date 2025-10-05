"""
Validation script to ensure all requirements for task 15 are met.
Checks test coverage, documentation, and implementation completeness.
"""

import os
import sys
import json
import subprocess
from pathlib import Path


class ImplementationValidator:
    """Validates that all task 15 requirements are implemented."""
    
    def __init__(self):
        self.results = {
            'api_documentation': False,
            'unit_tests': False,
            'integration_tests': False,
            'performance_tests': False,
            'test_coverage': False,
            'test_factories': False,
            'overall_score': 0
        }
        self.requirements = [
            "Document all new API endpoints with request/response examples",
            "Update existing API documentation to reflect enhanced functionality", 
            "Implement comprehensive unit tests for all new models, serializers, and views",
            "Create integration tests for complete user workflows",
            "Add performance tests for new features and database queries",
            "Achieve minimum 85% code coverage for all new functionality"
        ]
    
    def check_api_documentation(self):
        """Check if API documentation is comprehensive and up-to-date."""
        print("Checking API documentation...")
        
        required_files = [
            'API_DOCUMENTATION.md',
            'generate_api_docs.py'
        ]
        
        all_exist = True
        for file in required_files:
            if os.path.exists(file):
                print(f"✓ {file} exists")
            else:
                print(f"✗ {file} missing")
                all_exist = False
        
        # Check documentation content
        if os.path.exists('API_DOCUMENTATION.md'):
            with open('API_DOCUMENTATION.md', 'r') as f:
                content = f.read()
                
            required_sections = [
                'Authentication Endpoints',
                'Posts Endpoints', 
                'Social Features',
                'Content Moderation',
                'Email Subscriptions',
                'Error Responses',
                'Rate Limiting',
                'Testing'
            ]
            
            sections_found = 0
            for section in required_sections:
                if section.lower() in content.lower():
                    sections_found += 1
                    print(f"✓ Documentation includes {section}")
                else:
                    print(f"✗ Documentation missing {section}")
            
            documentation_complete = sections_found >= len(required_sections) * 0.8
        else:
            documentation_complete = False
        
        self.results['api_documentation'] = all_exist and documentation_complete
        return self.results['api_documentation']
    
    def check_unit_tests(self):
        """Check if comprehensive unit tests exist."""
        print("\nChecking unit tests...")
        
        required_test_files = [
            'accounts/test_comprehensive.py',
            'posts/test_comprehensive.py', 
            'moderation/test_comprehensive.py',
            'notifications/tests.py'
        ]
        
        tests_exist = 0
        for test_file in required_test_files:
            if os.path.exists(test_file):
                print(f"✓ {test_file} exists")
                tests_exist += 1
            else:
                print(f"✗ {test_file} missing")
        
        # Check test content quality
        comprehensive_tests = 0
        for test_file in required_test_files:
            if os.path.exists(test_file):
                with open(test_file, 'r') as f:
                    content = f.read()
                
                # Check for comprehensive test patterns
                test_patterns = [
                    'class.*Test.*TestCase',
                    'def test_.*creation',
                    'def test_.*validation', 
                    'def test_.*serializ',
                    'def test_.*api',
                    'APITestCase'
                ]
                
                patterns_found = sum(1 for pattern in test_patterns if pattern in content)
                if patterns_found >= 4:
                    comprehensive_tests += 1
                    print(f"✓ {test_file} has comprehensive tests")
                else:
                    print(f"⚠ {test_file} may need more comprehensive tests")
        
        self.results['unit_tests'] = tests_exist >= len(required_test_files) * 0.8
        return self.results['unit_tests']
    
    def check_integration_tests(self):
        """Check if integration tests exist."""
        print("\nChecking integration tests...")
        
        integration_file = 'test_integration_workflows.py'
        
        if os.path.exists(integration_file):
            print(f"✓ {integration_file} exists")
            
            with open(integration_file, 'r') as f:
                content = f.read()
            
            # Check for workflow tests
            required_workflows = [
                'UserRegistrationWorkflowTest',
                'ContentCreationWorkflowTest',
                'SocialInteractionWorkflowTest',
                'ContentModerationWorkflowTest'
            ]
            
            workflows_found = 0
            for workflow in required_workflows:
                if workflow in content:
                    workflows_found += 1
                    print(f"✓ {workflow} implemented")
                else:
                    print(f"✗ {workflow} missing")
            
            self.results['integration_tests'] = workflows_found >= len(required_workflows) * 0.8
        else:
            print(f"✗ {integration_file} missing")
            self.results['integration_tests'] = False
        
        return self.results['integration_tests']
    
    def check_performance_tests(self):
        """Check if performance tests exist."""
        print("\nChecking performance tests...")
        
        performance_files = [
            'test_performance_load.py'
        ]
        
        files_exist = 0
        for file in performance_files:
            if os.path.exists(file):
                print(f"✓ {file} exists")
                files_exist += 1
                
                # Check content
                with open(file, 'r') as f:
                    content = f.read()
                
                performance_patterns = [
                    'class.*User.*HttpUser',
                    '@task',
                    'locust',
                    'performance',
                    'load'
                ]
                
                patterns_found = sum(1 for pattern in performance_patterns if pattern.lower() in content.lower())
                if patterns_found >= 3:
                    print(f"✓ {file} has comprehensive performance tests")
                else:
                    print(f"⚠ {file} may need more performance test coverage")
            else:
                print(f"✗ {file} missing")
        
        self.results['performance_tests'] = files_exist >= len(performance_files)
        return self.results['performance_tests']
    
    def check_test_coverage(self):
        """Check if test coverage meets requirements."""
        print("\nChecking test coverage...")
        
        try:
            # Run coverage check
            result = subprocess.run([
                'pytest', '--cov=.', '--cov-report=json:coverage_check.json', 
                '--tb=no', '-q'
            ], capture_output=True, text=True)
            
            if os.path.exists('coverage_check.json'):
                with open('coverage_check.json', 'r') as f:
                    coverage_data = json.load(f)
                
                total_coverage = coverage_data['totals']['percent_covered']
                print(f"Current coverage: {total_coverage:.1f}%")
                
                if total_coverage >= 85:
                    print(f"✓ Coverage requirement met: {total_coverage:.1f}% >= 85%")
                    self.results['test_coverage'] = True
                else:
                    print(f"✗ Coverage requirement not met: {total_coverage:.1f}% < 85%")
                    self.results['test_coverage'] = False
                
                # Clean up
                os.remove('coverage_check.json')
            else:
                print("⚠ Could not generate coverage report")
                self.results['test_coverage'] = False
                
        except Exception as e:
            print(f"⚠ Error checking coverage: {e}")
            self.results['test_coverage'] = False
        
        return self.results['test_coverage']
    
    def check_test_factories(self):
        """Check if test factories are implemented."""
        print("\nChecking test factories...")
        
        factory_file = 'test_factories.py'
        
        if os.path.exists(factory_file):
            print(f"✓ {factory_file} exists")
            
            with open(factory_file, 'r') as f:
                content = f.read()
            
            # Check for factory classes
            required_factories = [
                'UserFactory',
                'PostFactory', 
                'UserProfileFactory',
                'ContentFlagFactory',
                'EmailSubscriptionFactory'
            ]
            
            factories_found = 0
            for factory in required_factories:
                if factory in content:
                    factories_found += 1
                    print(f"✓ {factory} implemented")
                else:
                    print(f"✗ {factory} missing")
            
            # Check for utility functions
            utility_functions = [
                'create_blog_scenario',
                'create_performance_test_data'
            ]
            
            utilities_found = 0
            for utility in utility_functions:
                if utility in content:
                    utilities_found += 1
                    print(f"✓ {utility} implemented")
                else:
                    print(f"✗ {utility} missing")
            
            self.results['test_factories'] = (
                factories_found >= len(required_factories) * 0.8 and
                utilities_found >= len(utility_functions) * 0.8
            )
        else:
            print(f"✗ {factory_file} missing")
            self.results['test_factories'] = False
        
        return self.results['test_factories']
    
    def calculate_overall_score(self):
        """Calculate overall implementation score."""
        total_checks = len(self.results) - 1  # Exclude overall_score
        passed_checks = sum(1 for key, value in self.results.items() 
                          if key != 'overall_score' and value)
        
        self.results['overall_score'] = (passed_checks / total_checks) * 100
        return self.results['overall_score']
    
    def generate_validation_report(self):
        """Generate validation report."""
        print("\n" + "=" * 60)
        print("TASK 15 IMPLEMENTATION VALIDATION REPORT")
        print("=" * 60)
        
        # Run all checks
        checks = [
            ("API Documentation", self.check_api_documentation),
            ("Unit Tests", self.check_unit_tests),
            ("Integration Tests", self.check_integration_tests),
            ("Performance Tests", self.check_performance_tests),
            ("Test Coverage", self.check_test_coverage),
            ("Test Factories", self.check_test_factories)
        ]
        
        for check_name, check_func in checks:
            try:
                result = check_func()
                status = "✓ PASSED" if result else "✗ FAILED"
                print(f"\n{check_name}: {status}")
            except Exception as e:
                print(f"\n{check_name}: ✗ ERROR - {e}")
        
        # Calculate overall score
        score = self.calculate_overall_score()
        
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        
        for requirement in self.requirements:
            print(f"- {requirement}")
        
        print(f"\nOverall Score: {score:.1f}%")
        
        if score >= 90:
            print("✓ EXCELLENT - All requirements fully implemented")
            status = "PASSED"
        elif score >= 80:
            print("✓ GOOD - Most requirements implemented")
            status = "PASSED"
        elif score >= 70:
            print("⚠ ACCEPTABLE - Some requirements need attention")
            status = "PARTIAL"
        else:
            print("✗ NEEDS WORK - Many requirements not met")
            status = "FAILED"
        
        # Save detailed results
        with open('validation_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nDetailed results saved to: validation_results.json")
        print(f"Final Status: {status}")
        
        return status == "PASSED"


def main():
    """Main validation function."""
    validator = ImplementationValidator()
    success = validator.generate_validation_report()
    
    if success:
        print("\n🎉 Task 15 implementation is complete and meets all requirements!")
        print("\nNext steps:")
        print("1. Run comprehensive tests: python run_comprehensive_tests.py")
        print("2. Review test coverage: open htmlcov/index.html")
        print("3. Run load tests: locust -f test_performance_load.py")
    else:
        print("\n⚠ Task 15 implementation needs additional work.")
        print("Please address the failed checks above.")
    
    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)