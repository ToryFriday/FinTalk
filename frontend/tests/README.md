# Selenium UI Tests for Blog Post Manager

This directory contains Selenium WebDriver tests for the Blog Post Manager frontend application. The tests cover complete user workflows, form validation, navigation, and error handling.

## Test Structure

```
tests/
├── selenium/
│   ├── conftest.py              # Test configuration and fixtures
│   ├── test_post_crud.py        # CRUD operation tests
│   ├── test_form_validation.py  # Form validation tests
│   └── test_navigation.py       # Navigation and routing tests
├── utils/
│   ├── page_objects.py          # Page Object Model classes
│   └── test_helpers.py          # Test utility functions
├── fixtures/
│   └── test_data.json          # Test data fixtures
├── pytest.ini                  # Pytest configuration
├── run_selenium_tests.py       # Test runner script
└── README.md                   # This file
```

## Prerequisites

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install selenium pytest pytest-html webdriver-manager

# Or install from requirements if available
pip install -r requirements.txt
```

### 2. Start Application Servers

Before running tests, ensure both frontend and backend servers are running:

```bash
# Terminal 1: Start backend server
cd backend
python manage.py runserver

# Terminal 2: Start frontend server
cd frontend
npm start
```

### 3. Browser Setup

The tests use Chrome by default with automatic ChromeDriver management via `webdriver-manager`. No manual driver installation is required.

## Running Tests

### Using the Test Runner Script (Recommended)

```bash
# Run all tests
python tests/run_selenium_tests.py

# Run with custom server URLs
python tests/run_selenium_tests.py --frontend-url http://localhost:3000 --api-url http://localhost:8000

# Run specific test file
python tests/run_selenium_tests.py --test-file test_post_crud.py

# Run specific test function
python tests/run_selenium_tests.py --test-function test_create_post_workflow

# Run tests with specific markers
python tests/run_selenium_tests.py --markers crud

# Run in headless mode
python tests/run_selenium_tests.py --headless

# Skip server health checks
python tests/run_selenium_tests.py --skip-server-check
```

### Using Pytest Directly

```bash
# Run all Selenium tests
pytest tests/selenium/ -v

# Run specific test file
pytest tests/selenium/test_post_crud.py -v

# Run with HTML report
pytest tests/selenium/ --html=test_reports/report.html --self-contained-html

# Run with markers
pytest tests/selenium/ -m crud -v
```

## Test Categories

### CRUD Operation Tests (`test_post_crud.py`)

Tests complete Create, Read, Update, Delete workflows:

- **Create Post**: Form submission, validation, success handling
- **Read Post**: Post listing, detail view, data display
- **Update Post**: Edit form, pre-population, update submission
- **Delete Post**: Deletion confirmation, list updates
- **Full CRUD Cycle**: End-to-end workflow testing

### Form Validation Tests (`test_form_validation.py`)

Tests form validation and error handling:

- **Empty Form Validation**: Required field validation
- **Field-Specific Validation**: Title, content, author validation
- **Client-Side Validation**: HTML5 validation, real-time feedback
- **Error Display**: Error message visibility and clarity
- **Valid Submission**: Successful form processing

### Navigation Tests (`test_navigation.py`)

Tests React Router functionality and navigation:

- **Page Navigation**: Home, add, edit, view page navigation
- **URL Updates**: Proper URL changes during navigation
- **Browser Navigation**: Back/forward button functionality
- **Direct URL Access**: Deep linking and route handling
- **Error Handling**: 404 pages, invalid routes
- **Keyboard Navigation**: Tab navigation, accessibility

## Page Object Model

The tests use the Page Object Model pattern for maintainable and reusable test code:

### Page Objects

- **`BasePage`**: Common functionality for all pages
- **`HomePage`**: Post listing and navigation
- **`AddPostPage`**: Post creation form
- **`EditPostPage`**: Post editing form (extends AddPostPage)
- **`ViewPostPage`**: Post detail view
- **`ConfirmDeleteDialog`**: Delete confirmation handling

### Example Usage

```python
from utils.page_objects import HomePage, AddPostPage

def test_create_post(driver, base_url):
    # Navigate to home page
    home_page = HomePage(driver).navigate_to_home(base_url)
    
    # Click add post button
    add_page = home_page.click_add_post()
    
    # Fill and submit form
    post_data = {'title': 'Test', 'content': 'Content', 'author': 'Author'}
    add_page.create_post(post_data)
```

## Test Configuration

### Environment Variables

- `FRONTEND_URL`: Frontend server URL (default: http://localhost:3000)
- `API_URL`: Backend API URL (default: http://localhost:8000)
- `SELENIUM_HEADLESS`: Run in headless mode (true/false)
- `SELENIUM_BROWSER`: Browser to use (chrome/firefox/edge)

### Pytest Markers

- `@pytest.mark.crud`: CRUD operation tests
- `@pytest.mark.validation`: Form validation tests
- `@pytest.mark.navigation`: Navigation tests
- `@pytest.mark.slow`: Slow-running tests

### Browser Configuration

Tests run in Chrome by default with these options:
- Headless mode for CI/CD
- Window size: 1920x1080
- Disabled extensions and security features for testing
- Automatic driver management

## Test Data Management

### Fixtures

Test data is loaded from `fixtures/test_data.json`:

```json
{
  "sample_posts": [
    {
      "title": "Test Post 1",
      "content": "Test content",
      "author": "Test Author",
      "tags": "test, sample"
    }
  ]
}
```

### Test Data Cleanup

The `TestDataManager` class handles test data lifecycle:
- Creates test posts via API
- Tracks created posts
- Cleans up after tests complete

## Troubleshooting

### Common Issues

1. **Server Not Running**
   ```
   Error: Frontend/Backend server is not responding
   Solution: Start the application servers before running tests
   ```

2. **ChromeDriver Issues**
   ```
   Error: ChromeDriver not found
   Solution: Tests use webdriver-manager for automatic driver management
   ```

3. **Element Not Found**
   ```
   Error: Element not located
   Solution: Check if application UI has changed, update selectors in page objects
   ```

4. **Timeout Errors**
   ```
   Error: WebDriverWait timeout
   Solution: Increase timeout values or check if application is slow to load
   ```

### Debug Mode

Run tests with UI visible for debugging:

```bash
python tests/run_selenium_tests.py --test-function test_create_post_workflow
```

### Screenshots

Screenshots are automatically taken on test failures and saved to `test_reports/screenshots/`.

## CI/CD Integration

For continuous integration, run tests in headless mode:

```bash
# CI/CD command
python tests/run_selenium_tests.py --headless --skip-server-check
```

Ensure servers are started before running tests in CI environment.

## Contributing

When adding new tests:

1. Follow the Page Object Model pattern
2. Use descriptive test names
3. Add appropriate pytest markers
4. Include test data cleanup
5. Handle both success and error scenarios
6. Update this README if adding new test categories

## Test Reports

HTML test reports are generated in `test_reports/selenium_report.html` with:
- Test results summary
- Individual test details
- Screenshots on failures
- Execution time metrics