import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ..utils.page_objects import HomePage, AddPostPage, EditPostPage, ViewPostPage, ConfirmDeleteDialog
from ..utils.test_helpers import (
    wait_for_page_load, 
    wait_for_url_change, 
    generate_test_post_data,
    TestDataManager
)


class TestPostCRUD:
    """Test complete CRUD workflows for blog posts"""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self, api_base_url):
        """Set up test data manager"""
        self.test_data_manager = TestDataManager(api_base_url)
        yield
        self.test_data_manager.cleanup()
    
    def test_create_post_workflow(self, driver, base_url, test_data):
        """Test complete post creation workflow"""
        # Navigate to home page
        home_page = HomePage(driver).navigate_to_home(base_url)
        home_page.wait_for_posts_to_load()
        
        # Get initial post count
        initial_count = home_page.get_post_count()
        
        # Click add post button
        add_page = home_page.click_add_post()
        
        # Verify we're on add post page
        assert "/add" in driver.current_url or "add" in driver.current_url.lower()
        
        # Fill form with test data
        post_data = test_data['sample_posts'][0]
        add_page.create_post(post_data)
        
        # Wait for redirect or success message
        try:
            # Wait for either redirect to home or success message
            WebDriverWait(driver, 10).until(
                lambda d: "/" == d.current_url.split('/')[-1] or 
                         add_page.get_success_message() is not None
            )
        except:
            pass
        
        # If still on add page, check for success message and navigate home
        if "/add" in driver.current_url:
            success_msg = add_page.get_success_message()
            assert success_msg is not None, "No success message displayed"
            driver.get(base_url)
        
        # Verify post was created
        home_page = HomePage(driver)
        home_page.wait_for_posts_to_load()
        
        final_count = home_page.get_post_count()
        assert final_count > initial_count, f"Post count didn't increase: {initial_count} -> {final_count}"
        
        # Verify post appears in list
        post_cards = home_page.get_post_cards()
        assert len(post_cards) > 0, "No posts found after creation"
        
        # Check if our post data appears (title should be visible)
        page_text = driver.page_source
        assert post_data['title'] in page_text, f"Post title '{post_data['title']}' not found on page"
    
    def test_read_post_workflow(self, driver, base_url, test_data):
        """Test post reading workflow"""
        # Create a test post first
        post_data = test_data['sample_posts'][0]
        created_post = self.test_data_manager.create_post(post_data)
        assert created_post is not None, "Failed to create test post"
        
        # Navigate to home page
        home_page = HomePage(driver).navigate_to_home(base_url)
        home_page.wait_for_posts_to_load()
        
        # Verify post appears in list
        post_cards = home_page.get_post_cards()
        assert len(post_cards) > 0, "No posts found"
        
        # Click on first post to view details
        view_page = home_page.click_view_post(0)
        
        # Verify we're on view page
        assert "/view" in driver.current_url or "/post" in driver.current_url or driver.current_url.split('/')[-1].isdigit()
        
        # Verify post details are displayed
        displayed_title = view_page.get_post_title()
        assert displayed_title is not None, "Post title not displayed"
        assert post_data['title'] in displayed_title, f"Expected title '{post_data['title']}' not in displayed title '{displayed_title}'"
        
        displayed_content = view_page.get_post_content()
        assert displayed_content is not None, "Post content not displayed"
        
        displayed_author = view_page.get_post_author()
        assert displayed_author is not None, "Post author not displayed"
        assert post_data['author'] in displayed_author, f"Expected author '{post_data['author']}' not in displayed author '{displayed_author}'"
    
    def test_update_post_workflow(self, driver, base_url, test_data):
        """Test post update workflow"""
        # Create a test post first
        original_post = test_data['sample_posts'][0]
        created_post = self.test_data_manager.create_post(original_post)
        assert created_post is not None, "Failed to create test post"
        
        # Navigate to home page
        home_page = HomePage(driver).navigate_to_home(base_url)
        home_page.wait_for_posts_to_load()
        
        # Click edit on first post
        edit_page = home_page.click_edit_post(0)
        
        # Verify we're on edit page
        assert "/edit" in driver.current_url or "edit" in driver.current_url.lower()
        
        # Wait for form to load with existing data
        edit_page.wait_for_form_to_load()
        
        # Verify form is pre-filled
        current_title = edit_page.get_current_title()
        assert original_post['title'] in current_title, f"Form not pre-filled with title: {current_title}"
        
        # Update post data
        updated_data = {
            'title': 'Updated Test Post Title',
            'content': 'This is updated content for the test post with sufficient length.',
            'author': 'Updated Test Author',
            'tags': 'updated, test, selenium'
        }
        
        edit_page.create_post(updated_data)  # Reuse create_post method for form filling
        
        # Wait for redirect or success
        try:
            WebDriverWait(driver, 10).until(
                lambda d: "/edit" not in d.current_url or 
                         edit_page.get_success_message() is not None
            )
        except:
            pass
        
        # Navigate back to home if needed
        if "/edit" in driver.current_url:
            driver.get(base_url)
        
        # Verify update was successful
        home_page = HomePage(driver)
        home_page.wait_for_posts_to_load()
        
        # Check if updated title appears
        page_text = driver.page_source
        assert updated_data['title'] in page_text, f"Updated title '{updated_data['title']}' not found"
    
    def test_delete_post_workflow(self, driver, base_url, test_data):
        """Test post deletion workflow"""
        # Create a test post first
        post_data = test_data['sample_posts'][0]
        created_post = self.test_data_manager.create_post(post_data)
        assert created_post is not None, "Failed to create test post"
        
        # Navigate to home page
        home_page = HomePage(driver).navigate_to_home(base_url)
        home_page.wait_for_posts_to_load()
        
        # Get initial post count
        initial_count = home_page.get_post_count()
        assert initial_count > 0, "No posts found to delete"
        
        # Click delete on first post
        home_page.click_delete_post(0)
        
        # Handle confirmation dialog if it appears
        try:
            # Look for confirmation dialog or button
            confirm_selectors = [
                "[data-testid='confirm-delete']",
                ".confirm-delete",
                "button[data-action='confirm']",
                ".modal button:last-child",
                ".dialog button:last-child"
            ]
            
            for selector in confirm_selectors:
                try:
                    confirm_btn = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    confirm_btn.click()
                    break
                except:
                    continue
        except:
            # No confirmation dialog, deletion might be immediate
            pass
        
        # Wait for deletion to complete
        time.sleep(2)
        
        # Refresh page to see updated list
        driver.refresh()
        home_page = HomePage(driver)
        home_page.wait_for_posts_to_load()
        
        # Verify post count decreased or post is no longer visible
        final_count = home_page.get_post_count()
        page_text = driver.page_source
        
        # Either count decreased or the specific post is no longer visible
        assert (final_count < initial_count or 
                post_data['title'] not in page_text), f"Post was not deleted. Count: {initial_count} -> {final_count}"
    
    def test_full_crud_cycle(self, driver, base_url, test_data):
        """Test complete CRUD cycle: Create -> Read -> Update -> Delete"""
        # CREATE
        home_page = HomePage(driver).navigate_to_home(base_url)
        home_page.wait_for_posts_to_load()
        
        initial_count = home_page.get_post_count()
        
        add_page = home_page.click_add_post()
        post_data = generate_test_post_data(999)  # Use unique data
        add_page.create_post(post_data)
        
        # Wait and navigate back to home
        time.sleep(2)
        if "/add" in driver.current_url:
            driver.get(base_url)
        
        home_page = HomePage(driver)
        home_page.wait_for_posts_to_load()
        
        # Verify creation
        assert home_page.get_post_count() > initial_count, "Post was not created"
        assert post_data['title'] in driver.page_source, "Created post not visible"
        
        # READ
        view_page = home_page.click_view_post(0)
        displayed_title = view_page.get_post_title()
        assert post_data['title'] in displayed_title, "Post title not displayed correctly"
        
        # UPDATE
        edit_page = view_page.click_edit()
        updated_data = generate_test_post_data(888)
        edit_page.create_post(updated_data)
        
        time.sleep(2)
        if "/edit" in driver.current_url:
            driver.get(base_url)
        
        # Verify update
        home_page = HomePage(driver)
        home_page.wait_for_posts_to_load()
        assert updated_data['title'] in driver.page_source, "Post was not updated"
        
        # DELETE
        home_page.click_delete_post(0)
        
        # Handle confirmation
        try:
            confirm_btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 
                    "[data-testid='confirm-delete'], .confirm-delete, button[data-action='confirm']"))
            )
            confirm_btn.click()
        except:
            pass
        
        time.sleep(2)
        driver.refresh()
        home_page = HomePage(driver)
        home_page.wait_for_posts_to_load()
        
        # Verify deletion
        assert updated_data['title'] not in driver.page_source, "Post was not deleted"
    
    def test_crud_with_validation_errors(self, driver, base_url):
        """Test CRUD operations with validation errors"""
        # Test create with invalid data
        home_page = HomePage(driver).navigate_to_home(base_url)
        add_page = home_page.click_add_post()
        
        # Try to submit empty form
        add_page.submit_form()
        
        # Check for validation errors
        time.sleep(1)
        form_errors = add_page.get_field_errors()
        form_error = add_page.get_form_error()
        
        # Should have validation errors or still be on add page
        assert (len(form_errors) > 0 or 
                form_error is not None or 
                "/add" in driver.current_url), "No validation errors shown for empty form"
        
        # Try with minimal invalid data
        add_page.fill_title("Hi")  # Too short
        add_page.fill_content("Short")  # Too short
        add_page.submit_form()
        
        time.sleep(1)
        
        # Should still have errors or be on add page
        form_errors = add_page.get_field_errors()
        form_error = add_page.get_form_error()
        
        assert (len(form_errors) > 0 or 
                form_error is not None or 
                "/add" in driver.current_url), "No validation errors shown for invalid data"