import pytest
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time


@pytest.fixture(scope="session")
def test_data():
    """Load test data from fixtures"""
    fixtures_path = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'test_data.json')
    with open(fixtures_path, 'r') as f:
        return json.load(f)


@pytest.fixture(scope="function")
def driver():
    """Set up Chrome WebDriver with options"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode for CI/CD
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    
    # Use webdriver-manager to automatically manage ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Set implicit wait
    driver.implicitly_wait(10)
    
    yield driver
    
    # Cleanup
    driver.quit()


@pytest.fixture(scope="function")
def driver_with_ui():
    """Set up Chrome WebDriver with UI for debugging"""
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(10)
    
    yield driver
    
    driver.quit()


@pytest.fixture(scope="function")
def wait(driver):
    """WebDriverWait instance"""
    return WebDriverWait(driver, 10)


@pytest.fixture(scope="function")
def base_url():
    """Base URL for the application"""
    return os.getenv('FRONTEND_URL', 'http://localhost:3000')


@pytest.fixture(scope="function")
def api_base_url():
    """Base URL for the API"""
    return os.getenv('API_URL', 'http://localhost:8000')


@pytest.fixture(autouse=True)
def setup_test_environment(driver, base_url):
    """Set up test environment before each test"""
    # Navigate to the application
    driver.get(base_url)
    
    # Wait for the application to load
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
    except Exception as e:
        pytest.skip(f"Application not available at {base_url}: {e}")


def wait_for_element(driver, by, value, timeout=10):
    """Helper function to wait for element"""
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )


def wait_for_clickable(driver, by, value, timeout=10):
    """Helper function to wait for clickable element"""
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    )


def wait_for_text_in_element(driver, by, value, text, timeout=10):
    """Helper function to wait for text in element"""
    return WebDriverWait(driver, timeout).until(
        EC.text_to_be_present_in_element((by, value), text)
    )