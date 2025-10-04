import time
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def wait_for_page_load(driver, timeout=10):
    """Wait for page to fully load"""
    WebDriverWait(driver, timeout).until(
        lambda driver: driver.execute_script("return document.readyState") == "complete"
    )


def wait_for_react_to_load(driver, timeout=10):
    """Wait for React application to load"""
    WebDriverWait(driver, timeout).until(
        lambda driver: driver.execute_script(
            "return window.React !== undefined || document.querySelector('[data-reactroot]') !== null"
        )
    )


def scroll_to_bottom(driver):
    """Scroll to bottom of page"""
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)


def scroll_to_top(driver):
    """Scroll to top of page"""
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)


def take_screenshot(driver, filename):
    """Take screenshot for debugging"""
    try:
        driver.save_screenshot(f"screenshots/{filename}")
    except Exception as e:
        print(f"Failed to take screenshot: {e}")


def clear_browser_data(driver):
    """Clear browser data"""
    driver.delete_all_cookies()
    driver.execute_script("window.localStorage.clear();")
    driver.execute_script("window.sessionStorage.clear();")


def wait_for_url_change(driver, current_url, timeout=10):
    """Wait for URL to change from current URL"""
    WebDriverWait(driver, timeout).until(
        lambda driver: driver.current_url != current_url
    )


def wait_for_url_contains(driver, url_part, timeout=10):
    """Wait for URL to contain specific part"""
    WebDriverWait(driver, timeout).until(
        EC.url_contains(url_part)
    )


def is_element_present(driver, by, value):
    """Check if element is present"""
    try:
        driver.find_element(by, value)
        return True
    except:
        return False


def is_element_visible(driver, by, value):
    """Check if element is visible"""
    try:
        element = driver.find_element(by, value)
        return element.is_displayed()
    except:
        return False


def get_element_text_safe(driver, by, value):
    """Safely get element text"""
    try:
        element = driver.find_element(by, value)
        return element.text
    except:
        return ""


def click_element_safe(driver, by, value):
    """Safely click element"""
    try:
        element = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((by, value))
        )
        element.click()
        return True
    except:
        return False


def send_keys_safe(driver, by, value, text):
    """Safely send keys to element"""
    try:
        element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((by, value))
        )
        element.clear()
        element.send_keys(text)
        return True
    except:
        return False


def wait_for_element_to_disappear(driver, by, value, timeout=10):
    """Wait for element to disappear"""
    WebDriverWait(driver, timeout).until_not(
        EC.presence_of_element_located((by, value))
    )


def wait_for_text_change(driver, by, value, old_text, timeout=10):
    """Wait for element text to change"""
    WebDriverWait(driver, timeout).until(
        lambda driver: driver.find_element(by, value).text != old_text
    )


def check_api_health(api_url):
    """Check if API is healthy"""
    try:
        response = requests.get(f"{api_url}/api/posts/", timeout=5)
        return response.status_code in [200, 404]  # 404 is OK if no posts exist
    except:
        return False


def create_test_post_via_api(api_url, post_data):
    """Create test post via API for setup"""
    try:
        response = requests.post(f"{api_url}/api/posts/", json=post_data, timeout=5)
        return response.status_code == 201
    except:
        return False


def cleanup_test_posts_via_api(api_url):
    """Clean up test posts via API"""
    try:
        # Get all posts
        response = requests.get(f"{api_url}/api/posts/", timeout=5)
        if response.status_code == 200:
            posts = response.json()
            # Delete posts that look like test data
            for post in posts:
                if 'test' in post.get('title', '').lower() or 'test' in post.get('author', '').lower():
                    requests.delete(f"{api_url}/api/posts/{post['id']}/", timeout=5)
        return True
    except:
        return False


def generate_test_post_data(index=1):
    """Generate test post data"""
    return {
        'title': f'Test Post {index}',
        'content': f'This is test content for post {index}. It contains enough text to meet validation requirements.',
        'author': f'Test Author {index}',
        'tags': f'test, selenium, post{index}',
        'image_url': f'https://example.com/image{index}.jpg'
    }


def validate_post_data(actual_post, expected_post):
    """Validate post data matches expected"""
    errors = []
    
    if actual_post.get('title') != expected_post.get('title'):
        errors.append(f"Title mismatch: {actual_post.get('title')} != {expected_post.get('title')}")
    
    if actual_post.get('author') != expected_post.get('author'):
        errors.append(f"Author mismatch: {actual_post.get('author')} != {expected_post.get('author')}")
    
    # Content might be truncated in list view, so check if it starts with expected
    if not actual_post.get('content', '').startswith(expected_post.get('content', '')[:50]):
        errors.append(f"Content mismatch: {actual_post.get('content')} doesn't start with {expected_post.get('content')[:50]}")
    
    return errors


class TestDataManager:
    """Manage test data for tests"""
    
    def __init__(self, api_url):
        self.api_url = api_url
        self.created_posts = []
    
    def create_post(self, post_data):
        """Create a post and track it"""
        try:
            response = requests.post(f"{self.api_url}/api/posts/", json=post_data, timeout=5)
            if response.status_code == 201:
                post = response.json()
                self.created_posts.append(post['id'])
                return post
        except:
            pass
        return None
    
    def cleanup(self):
        """Clean up all created posts"""
        for post_id in self.created_posts:
            try:
                requests.delete(f"{self.api_url}/api/posts/{post_id}/", timeout=5)
            except:
                pass
        self.created_posts.clear()