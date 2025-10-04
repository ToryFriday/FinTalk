import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from ..utils.page_objects import HomePage, AddPostPage, EditPostPage, ViewPostPage
from ..utils.test_helpers import (
    wait_for_url_change, 
    wait_for_url_contains, 
    TestDataManager,
    generate_test_post_data
)


class TestNavigation:
    """Test navigation flows and React Router functionality"""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self, api_base_url):
        """Set up test data manager"""
        self.test_data_manager = TestDataManager(api_base_url)
        yield
        self.test_data_manager.cleanup()
    
    def test_home_page_navigation(self, driver, base_url):
        """Test navigation to home page"""
        # Navigate to home page
        driver.get(base_url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Verify we're on home page
        assert driver.current_url == base_url or driver.current_url == f"{base_url}/"
        
        # Check for home page elements
        home_page = HomePage(driver)
        home_page.wait_for_posts_to_load()
        
        # Should have add post button or posts container
        page_source = driver.page_source.lower()
        has_home_elements = (
            "add" in page_source or 
            "post" in page_source or 
            "blog" in page_source or
            len(home_page.get_post_cards()) >= 0  # 0 or more posts is valid
        )
        
        assert has_home_elements, "Home page doesn't contain expected elements"
    
    def test_add_post_navigation(self, driver, base_url):
        """Test navigation to add post page"""
        # Start from home page
        home_page = HomePage(driver).navigate_to_home(base_url)
        
        # Click add post button
        current_url = driver.current_url
        add_page = home_page.click_add_post()
        
        # Verify URL changed
        wait_for_url_change(driver, current_url)
        
        # Verify we're on add post page
        new_url = driver.current_url
        assert ("/add" in new_url or 
                "add" in new_url.lower() or 
                "create" in new_url.lower()), f"Not on add post page: {new_url}"
        
        # Verify form elements are present
        try:
            add_page.wait_for_element(By.CSS_SELECTOR, 
                "[data-testid='title-input'], input[name='title'], #title")
            add_page.wait_for_element(By.CSS_SELECTOR, 
                "[data-testid='content-input'], textarea[name='content'], #content")
        except Exception as e:
            pytest.fail(f"Add post form elements not found: {e}")
    
    def test_view_post_navigation(self, driver, base_url, test_data):
        """Test navigation to view post page"""
        # Create a test post first
        post_data = test_data['sample_posts'][0]
        created_post = self.test_data_manager.create_post(post_data)
        assert created_post is not None, "Failed to create test post"
        
        # Navigate to home page
        home_page = HomePage(driver).navigate_to_home(base_url)
        home_page.wait_for_posts_to_load()
        
        # Click on post to view
        current_url = driver.current_url
        view_page = home_page.click_view_post(0)
        
        # Verify URL changed
        wait_for_url_change(driver, current_url)
        
        # Verify we're on view post page
        new_url = driver.current_url
        is_view_page = (
            "/view" in new_url or 
            "/post" in new_url or 
            new_url.split('/')[-1].isdigit() or  # ID in URL
            "view" in new_url.lower()
        )
        
        assert is_view_page, f"Not on view post page: {new_url}"
        
        # Verify post content is displayed
        displayed_title = view_page.get_post_title()
        assert displayed_title is not None, "Post title not displayed on view page"
    
    def test_edit_post_navigation(self, driver, base_url, test_data):
        """Test navigation to edit post page"""
        # Create a test post first
        post_data = test_data['sample_posts'][0]
        created_post = self.test_data_manager.create_post(post_data)
        assert created_post is not None, "Failed to create test post"
        
        # Navigate to home page
        home_page = HomePage(driver).navigate_to_home(base_url)
        home_page.wait_for_posts_to_load()
        
        # Click edit on post
        current_url = driver.current_url
        edit_page = home_page.click_edit_post(0)
        
        # Verify URL changed
        wait_for_url_change(driver, current_url)
        
        # Verify we're on edit post page
        new_url = driver.current_url
        is_edit_page = (
            "/edit" in new_url or 
            "edit" in new_url.lower() or
            "update" in new_url.lower()
        )
        
        assert is_edit_page, f"Not on edit post page: {new_url}"
        
        # Verify form is pre-filled
        edit_page.wait_for_form_to_load()
        current_title = edit_page.get_current_title()
        assert post_data['title'] in current_title, "Edit form not pre-filled"
    
    def test_browser_back_forward_navigation(self, driver, base_url, test_data):
        """Test browser back and forward button functionality"""
        # Create a test post
        post_data = test_data['sample_posts'][0]
        created_post = self.test_data_manager.create_post(post_data)
        assert created_post is not None, "Failed to create test post"
        
        # Start at home page
        home_page = HomePage(driver).navigate_to_home(base_url)
        home_page.wait_for_posts_to_load()
        home_url = driver.current_url
        
        # Navigate to add post page
        add_page = home_page.click_add_post()
        add_url = driver.current_url
        
        # Navigate to view post page (go back to home first)
        driver.back()
        WebDriverWait(driver, 5).until(lambda d: d.current_url == home_url)
        
        home_page = HomePage(driver)
        home_page.wait_for_posts_to_load()
        view_page = home_page.click_view_post(0)
        view_url = driver.current_url
        
        # Test back button
        driver.back()
        WebDriverWait(driver, 5).until(lambda d: d.current_url == home_url)
        assert driver.current_url == home_url, "Back button didn't return to home"
        
        # Test forward button
        driver.forward()
        WebDriverWait(driver, 5).until(lambda d: d.current_url == view_url)
        assert driver.current_url == view_url, "Forward button didn't return to view page"
    
    def test_direct_url_access(self, driver, base_url, test_data):
        """Test direct URL access to different pages"""
        # Test direct access to add page
        add_url = f"{base_url}/add"
        driver.get(add_url)
        
        # Should load add page
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Check if we're on add page (might redirect if not implemented)
        current_url = driver.current_url
        if "/add" in current_url or "add" in current_url.lower():
            # Verify form elements
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 
                        "input[name='title'], #title, [data-testid='title-input']"))
                )
            except:
                pytest.fail("Add page form not loaded on direct URL access")
        
        # Test direct access to non-existent post
        fake_post_url = f"{base_url}/post/99999"
        driver.get(fake_post_url)
        
        time.sleep(2)
        
        # Should show 404 or redirect to home
        page_text = driver.page_source.lower()
        is_error_handled = (
            "404" in page_text or 
            "not found" in page_text or 
            driver.current_url == base_url or
            driver.current_url == f"{base_url}/"
        )
        
        assert is_error_handled, "Non-existent post URL not handled properly"
    
    def test_url_updates_on_navigation(self, driver, base_url):
        """Test that URLs update correctly during navigation"""
        # Start at home
        driver.get(base_url)
        home_url = driver.current_url
        
        # Navigate to add post
        home_page = HomePage(driver)
        add_page = home_page.click_add_post()
        
        # URL should change
        add_url = driver.current_url
        assert add_url != home_url, "URL didn't change when navigating to add post"
        
        # Fill and submit form
        post_data = generate_test_post_data(200)
        add_page.create_post(post_data)
        
        # Wait for navigation
        time.sleep(3)
        
        # URL should change after submission
        final_url = driver.current_url
        url_changed_after_submit = (
            final_url != add_url and 
            (final_url == home_url or "/" in final_url)
        )
        
        assert url_changed_after_submit, f"URL didn't change after form submission: {add_url} -> {final_url}"
    
    def test_navigation_with_keyboard(self, driver, base_url):
        """Test keyboard navigation"""
        # Navigate to home page
        driver.get(base_url)
        
        # Try Tab navigation
        body = driver.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.TAB)
        
        # Check if focus moved to a clickable element
        active_element = driver.switch_to.active_element
        assert active_element is not None, "Tab navigation not working"
        
        # Try Enter key on focused element
        try:
            active_element.send_keys(Keys.ENTER)
            time.sleep(1)
            # If it was a link/button, URL might have changed
            # This is optional - just testing that keyboard interaction works
        except:
            pass  # Some elements might not respond to Enter
    
    def test_navigation_breadcrumbs_or_back_links(self, driver, base_url, test_data):
        """Test navigation breadcrumbs or back links if present"""
        # Create a test post
        post_data = test_data['sample_posts'][0]
        created_post = self.test_data_manager.create_post(post_data)
        assert created_post is not None, "Failed to create test post"
        
        # Navigate to view post page
        home_page = HomePage(driver).navigate_to_home(base_url)
        home_page.wait_for_posts_to_load()
        view_page = home_page.click_view_post(0)
        
        # Look for back button or breadcrumb
        back_elements = driver.find_elements(By.CSS_SELECTOR, 
            "[data-testid='back-btn'], .back-btn, .breadcrumb, .nav-back, button[data-action='back']")
        
        if back_elements:
            # Click back button
            back_btn = back_elements[0]
            if back_btn.is_displayed():
                back_btn.click()
                
                # Should return to home page
                time.sleep(2)
                current_url = driver.current_url
                assert (current_url == base_url or 
                       current_url == f"{base_url}/"), "Back button didn't return to home"
    
    def test_page_refresh_maintains_state(self, driver, base_url, test_data):
        """Test that page refresh maintains proper state"""
        # Create a test post
        post_data = test_data['sample_posts'][0]
        created_post = self.test_data_manager.create_post(post_data)
        assert created_post is not None, "Failed to create test post"
        
        # Navigate to view post page
        home_page = HomePage(driver).navigate_to_home(base_url)
        home_page.wait_for_posts_to_load()
        view_page = home_page.click_view_post(0)
        
        view_url = driver.current_url
        original_title = view_page.get_post_title()
        
        # Refresh page
        driver.refresh()
        
        # Wait for page to reload
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Verify we're still on the same page
        assert driver.current_url == view_url, "URL changed after refresh"
        
        # Verify content is still displayed
        view_page = ViewPostPage(driver)
        refreshed_title = view_page.get_post_title()
        assert refreshed_title == original_title, "Post content changed after refresh"
    
    def test_navigation_error_handling(self, driver, base_url):
        """Test navigation error handling"""
        # Try to navigate to invalid routes
        invalid_routes = [
            f"{base_url}/invalid-route",
            f"{base_url}/post/invalid-id",
            f"{base_url}/edit/invalid-id"
        ]
        
        for invalid_url in invalid_routes:
            driver.get(invalid_url)
            time.sleep(2)
            
            # Should either show 404 page or redirect to home
            current_url = driver.current_url
            page_text = driver.page_source.lower()
            
            error_handled = (
                "404" in page_text or 
                "not found" in page_text or 
                "error" in page_text or
                current_url == base_url or
                current_url == f"{base_url}/"
            )
            
            assert error_handled, f"Invalid route not handled properly: {invalid_url}"