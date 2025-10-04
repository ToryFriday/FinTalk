from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time


class BasePage:
    """Base page object with common functionality"""
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
    
    def wait_for_element(self, by, value, timeout=10):
        """Wait for element to be present"""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
    
    def wait_for_clickable(self, by, value, timeout=10):
        """Wait for element to be clickable"""
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
    
    def wait_for_text_in_element(self, by, value, text, timeout=10):
        """Wait for text to appear in element"""
        return WebDriverWait(self.driver, timeout).until(
            EC.text_to_be_present_in_element((by, value), text)
        )
    
    def scroll_to_element(self, element):
        """Scroll to element"""
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)


class HomePage(BasePage):
    """Page object for the home page (post list)"""
    
    # Locators
    ADD_POST_BUTTON = (By.CSS_SELECTOR, "[data-testid='add-post-btn'], .add-post-btn, button[href='/add'], a[href='/add']")
    POST_CARDS = (By.CSS_SELECTOR, "[data-testid='post-card'], .post-card, .post-item")
    POST_TITLE = (By.CSS_SELECTOR, "[data-testid='post-title'], .post-title, h2, h3")
    POST_CONTENT = (By.CSS_SELECTOR, "[data-testid='post-content'], .post-content, .post-excerpt")
    POST_AUTHOR = (By.CSS_SELECTOR, "[data-testid='post-author'], .post-author, .author")
    EDIT_BUTTON = (By.CSS_SELECTOR, "[data-testid='edit-btn'], .edit-btn, button[data-action='edit']")
    DELETE_BUTTON = (By.CSS_SELECTOR, "[data-testid='delete-btn'], .delete-btn, button[data-action='delete']")
    VIEW_BUTTON = (By.CSS_SELECTOR, "[data-testid='view-btn'], .view-btn, button[data-action='view']")
    LOADING_SPINNER = (By.CSS_SELECTOR, "[data-testid='loading'], .loading, .spinner")
    ERROR_MESSAGE = (By.CSS_SELECTOR, "[data-testid='error'], .error, .error-message")
    
    def navigate_to_home(self, base_url):
        """Navigate to home page"""
        self.driver.get(base_url)
        return self
    
    def click_add_post(self):
        """Click add post button"""
        add_btn = self.wait_for_clickable(*self.ADD_POST_BUTTON)
        self.scroll_to_element(add_btn)
        add_btn.click()
        return AddPostPage(self.driver)
    
    def get_post_cards(self):
        """Get all post cards"""
        try:
            return self.driver.find_elements(*self.POST_CARDS)
        except:
            return []
    
    def get_post_count(self):
        """Get number of posts displayed"""
        return len(self.get_post_cards())
    
    def click_edit_post(self, post_index=0):
        """Click edit button for a specific post"""
        edit_buttons = self.driver.find_elements(*self.EDIT_BUTTON)
        if edit_buttons and post_index < len(edit_buttons):
            self.scroll_to_element(edit_buttons[post_index])
            edit_buttons[post_index].click()
            return EditPostPage(self.driver)
        raise Exception(f"Edit button not found for post index {post_index}")
    
    def click_view_post(self, post_index=0):
        """Click view button for a specific post"""
        view_buttons = self.driver.find_elements(*self.VIEW_BUTTON)
        if view_buttons and post_index < len(view_buttons):
            self.scroll_to_element(view_buttons[post_index])
            view_buttons[post_index].click()
            return ViewPostPage(self.driver)
        
        # Fallback: try clicking on post title
        post_titles = self.driver.find_elements(*self.POST_TITLE)
        if post_titles and post_index < len(post_titles):
            self.scroll_to_element(post_titles[post_index])
            post_titles[post_index].click()
            return ViewPostPage(self.driver)
        
        raise Exception(f"View button/title not found for post index {post_index}")
    
    def click_delete_post(self, post_index=0):
        """Click delete button for a specific post"""
        delete_buttons = self.driver.find_elements(*self.DELETE_BUTTON)
        if delete_buttons and post_index < len(delete_buttons):
            self.scroll_to_element(delete_buttons[post_index])
            delete_buttons[post_index].click()
            return self
        raise Exception(f"Delete button not found for post index {post_index}")
    
    def is_loading(self):
        """Check if loading spinner is visible"""
        try:
            loading = self.driver.find_element(*self.LOADING_SPINNER)
            return loading.is_displayed()
        except:
            return False
    
    def get_error_message(self):
        """Get error message text"""
        try:
            error = self.driver.find_element(*self.ERROR_MESSAGE)
            return error.text if error.is_displayed() else None
        except:
            return None
    
    def wait_for_posts_to_load(self):
        """Wait for posts to load"""
        # Wait for loading to disappear or posts to appear
        try:
            self.wait.until(
                lambda driver: not self.is_loading() or len(self.get_post_cards()) > 0
            )
        except:
            pass
        return self


class AddPostPage(BasePage):
    """Page object for add post page"""
    
    # Locators
    TITLE_INPUT = (By.CSS_SELECTOR, "[data-testid='title-input'], input[name='title'], #title")
    CONTENT_INPUT = (By.CSS_SELECTOR, "[data-testid='content-input'], textarea[name='content'], #content")
    AUTHOR_INPUT = (By.CSS_SELECTOR, "[data-testid='author-input'], input[name='author'], #author")
    TAGS_INPUT = (By.CSS_SELECTOR, "[data-testid='tags-input'], input[name='tags'], #tags")
    IMAGE_URL_INPUT = (By.CSS_SELECTOR, "[data-testid='image-url-input'], input[name='image_url'], #image_url")
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "[data-testid='submit-btn'], button[type='submit'], .submit-btn")
    CANCEL_BUTTON = (By.CSS_SELECTOR, "[data-testid='cancel-btn'], .cancel-btn, button[type='button']")
    FORM_ERROR = (By.CSS_SELECTOR, "[data-testid='form-error'], .form-error, .error")
    FIELD_ERROR = (By.CSS_SELECTOR, "[data-testid='field-error'], .field-error, .invalid-feedback")
    SUCCESS_MESSAGE = (By.CSS_SELECTOR, "[data-testid='success'], .success, .alert-success")
    
    def fill_title(self, title):
        """Fill title field"""
        title_input = self.wait_for_element(*self.TITLE_INPUT)
        title_input.clear()
        title_input.send_keys(title)
        return self
    
    def fill_content(self, content):
        """Fill content field"""
        content_input = self.wait_for_element(*self.CONTENT_INPUT)
        content_input.clear()
        content_input.send_keys(content)
        return self
    
    def fill_author(self, author):
        """Fill author field"""
        author_input = self.wait_for_element(*self.AUTHOR_INPUT)
        author_input.clear()
        author_input.send_keys(author)
        return self
    
    def fill_tags(self, tags):
        """Fill tags field"""
        try:
            tags_input = self.wait_for_element(*self.TAGS_INPUT)
            tags_input.clear()
            tags_input.send_keys(tags)
        except:
            pass  # Tags field might be optional
        return self
    
    def fill_image_url(self, image_url):
        """Fill image URL field"""
        try:
            image_input = self.wait_for_element(*self.IMAGE_URL_INPUT)
            image_input.clear()
            image_input.send_keys(image_url)
        except:
            pass  # Image URL field might be optional
        return self
    
    def submit_form(self):
        """Submit the form"""
        submit_btn = self.wait_for_clickable(*self.SUBMIT_BUTTON)
        self.scroll_to_element(submit_btn)
        submit_btn.click()
        return self
    
    def cancel_form(self):
        """Cancel form and return to home"""
        cancel_btn = self.wait_for_clickable(*self.CANCEL_BUTTON)
        cancel_btn.click()
        return HomePage(self.driver)
    
    def get_form_error(self):
        """Get form error message"""
        try:
            error = self.driver.find_element(*self.FORM_ERROR)
            return error.text if error.is_displayed() else None
        except:
            return None
    
    def get_field_errors(self):
        """Get all field error messages"""
        try:
            errors = self.driver.find_elements(*self.FIELD_ERROR)
            return [error.text for error in errors if error.is_displayed()]
        except:
            return []
    
    def get_success_message(self):
        """Get success message"""
        try:
            success = self.driver.find_element(*self.SUCCESS_MESSAGE)
            return success.text if success.is_displayed() else None
        except:
            return None
    
    def create_post(self, post_data):
        """Create a post with given data"""
        self.fill_title(post_data.get('title', ''))
        self.fill_content(post_data.get('content', ''))
        self.fill_author(post_data.get('author', ''))
        
        if 'tags' in post_data:
            self.fill_tags(post_data['tags'])
        
        if 'image_url' in post_data:
            self.fill_image_url(post_data['image_url'])
        
        self.submit_form()
        return self


class EditPostPage(AddPostPage):
    """Page object for edit post page (inherits from AddPostPage)"""
    
    def wait_for_form_to_load(self):
        """Wait for form to load with existing data"""
        self.wait_for_element(*self.TITLE_INPUT)
        # Wait a bit for form to populate
        time.sleep(1)
        return self
    
    def get_current_title(self):
        """Get current title value"""
        title_input = self.driver.find_element(*self.TITLE_INPUT)
        return title_input.get_attribute('value')
    
    def get_current_content(self):
        """Get current content value"""
        content_input = self.driver.find_element(*self.CONTENT_INPUT)
        return content_input.get_attribute('value')
    
    def get_current_author(self):
        """Get current author value"""
        author_input = self.driver.find_element(*self.AUTHOR_INPUT)
        return author_input.get_attribute('value')


class ViewPostPage(BasePage):
    """Page object for view post page"""
    
    # Locators
    POST_TITLE = (By.CSS_SELECTOR, "[data-testid='post-title'], .post-title, h1, h2")
    POST_CONTENT = (By.CSS_SELECTOR, "[data-testid='post-content'], .post-content, .content")
    POST_AUTHOR = (By.CSS_SELECTOR, "[data-testid='post-author'], .post-author, .author")
    POST_TAGS = (By.CSS_SELECTOR, "[data-testid='post-tags'], .post-tags, .tags")
    POST_DATE = (By.CSS_SELECTOR, "[data-testid='post-date'], .post-date, .date")
    EDIT_BUTTON = (By.CSS_SELECTOR, "[data-testid='edit-btn'], .edit-btn, button[data-action='edit']")
    DELETE_BUTTON = (By.CSS_SELECTOR, "[data-testid='delete-btn'], .delete-btn, button[data-action='delete']")
    BACK_BUTTON = (By.CSS_SELECTOR, "[data-testid='back-btn'], .back-btn, button[data-action='back']")
    NOT_FOUND_MESSAGE = (By.CSS_SELECTOR, "[data-testid='not-found'], .not-found, .error-404")
    
    def get_post_title(self):
        """Get post title"""
        try:
            title = self.wait_for_element(*self.POST_TITLE)
            return title.text
        except:
            return None
    
    def get_post_content(self):
        """Get post content"""
        try:
            content = self.driver.find_element(*self.POST_CONTENT)
            return content.text
        except:
            return None
    
    def get_post_author(self):
        """Get post author"""
        try:
            author = self.driver.find_element(*self.POST_AUTHOR)
            return author.text
        except:
            return None
    
    def get_post_tags(self):
        """Get post tags"""
        try:
            tags = self.driver.find_element(*self.POST_TAGS)
            return tags.text
        except:
            return None
    
    def click_edit(self):
        """Click edit button"""
        edit_btn = self.wait_for_clickable(*self.EDIT_BUTTON)
        edit_btn.click()
        return EditPostPage(self.driver)
    
    def click_delete(self):
        """Click delete button"""
        delete_btn = self.wait_for_clickable(*self.DELETE_BUTTON)
        delete_btn.click()
        return self
    
    def click_back(self):
        """Click back button"""
        back_btn = self.wait_for_clickable(*self.BACK_BUTTON)
        back_btn.click()
        return HomePage(self.driver)
    
    def is_not_found(self):
        """Check if post not found message is displayed"""
        try:
            not_found = self.driver.find_element(*self.NOT_FOUND_MESSAGE)
            return not_found.is_displayed()
        except:
            return False


class ConfirmDeleteDialog(BasePage):
    """Page object for delete confirmation dialog"""
    
    # Locators
    CONFIRM_BUTTON = (By.CSS_SELECTOR, "[data-testid='confirm-delete'], .confirm-delete, button[data-action='confirm']")
    CANCEL_BUTTON = (By.CSS_SELECTOR, "[data-testid='cancel-delete'], .cancel-delete, button[data-action='cancel']")
    DIALOG = (By.CSS_SELECTOR, "[data-testid='delete-dialog'], .delete-dialog, .modal, .dialog")
    
    def wait_for_dialog(self):
        """Wait for delete dialog to appear"""
        self.wait_for_element(*self.DIALOG)
        return self
    
    def confirm_delete(self):
        """Confirm deletion"""
        confirm_btn = self.wait_for_clickable(*self.CONFIRM_BUTTON)
        confirm_btn.click()
        return HomePage(self.driver)
    
    def cancel_delete(self):
        """Cancel deletion"""
        cancel_btn = self.wait_for_clickable(*self.CANCEL_BUTTON)
        cancel_btn.click()
        return self