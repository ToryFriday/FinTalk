# Testing Guide

## Overview

This guide provides comprehensive information about testing the Blog Post Manager application. The testing strategy includes unit tests, integration tests, and end-to-end tests to ensure reliability and maintainability.

## Testing Philosophy

### Testing Pyramid

The application follows the testing pyramid approach:

- **Unit Tests (70%)**: Fast, isolated tests for individual components
- **Integration Tests (20%)**: Tests for component interactions  
- **End-to-End Tests (10%)**: Full user workflow tests

### Test-Driven Development (TDD)

We follow TDD principles:
1. **Red**: Write a failing test
2. **Green**: Write minimal code to pass
3. **Refactor**: Improve code while keeping tests green

## Backend Testing

### Running Backend Tests

```bash
cd backend

# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=posts --cov-report=html

# Run specific test file
python -m pytest posts/tests/test_models.py

# Run tests with specific markers
python -m pytest -m "not slow"
python -m pytest -m integration

# Run tests in parallel
python -m pytest -n auto
```

### Model Testing Example

```python
import pytest
from django.core.exceptions import ValidationError
from posts.models import Post

@pytest.mark.django_db
class TestPostModel:
    def test_create_valid_post(self):
        post = Post.objects.create(
            title="Test Post Title",
            content="This is test content with sufficient length.",
            author="Test Author"
        )
        
        assert post.id is not None
        assert post.title == "Test Post Title"
        assert post.content == "This is test content with sufficient length."
        assert post.author == "Test Author"
    
    def test_title_validation_too_short(self):
        with pytest.raises(ValidationError) as exc_info:
            post = Post(
                title="Hi",  # Too short
                content="This is test content with sufficient length.",
                author="Test Author"
            )
            post.full_clean()
        
        assert 'title' in exc_info.value.message_dict
```

### API Testing Example

```python
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

@pytest.mark.django_db
class TestPostAPI:
    def setup_method(self):
        self.client = APIClient()
        self.valid_post_data = {
            'title': 'Test Post Title',
            'content': 'This is test content with sufficient length.',
            'author': 'Test Author',
            'tags': 'test, api, django'
        }
    
    def test_create_post_success(self):
        url = reverse('posts:post-list-create')
        response = self.client.post(url, self.valid_post_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Post.objects.count() == 1
```

## Frontend Testing

### Running Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run tests without watch mode (CI)
npm test -- --watchAll=false

# Run Selenium UI tests
npm run test:selenium
```

### Component Testing Example

```javascript
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import PostCard from '../PostCard';

const renderWithRouter = (component) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('PostCard Component', () => {
  const mockPost = {
    id: 1,
    title: 'Test Post Title',
    content: 'This is test content.',
    author: 'Test Author',
    tags: 'test, react',
    tags_list: ['test', 'react'],
    created_at: '2024-01-15T10:30:00Z',
  };

  test('renders post information correctly', () => {
    renderWithRouter(<PostCard post={mockPost} />);

    expect(screen.getByText('Test Post Title')).toBeInTheDocument();
    expect(screen.getByText('Test Author')).toBeInTheDocument();
    expect(screen.getByText(/This is test content/)).toBeInTheDocument();
  });
});
```

## End-to-End Testing

### Selenium Setup

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def get_webdriver(headless=False):
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument('--headless')
    
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    
    return driver
```

### E2E Test Example

```python
import pytest
from tests.utils.webdriver_setup import get_webdriver, get_base_url
from tests.utils.page_objects import HomePage, AddPostPage

@pytest.mark.selenium
class TestPostCRUD:
    @classmethod
    def setup_class(cls):
        cls.driver = get_webdriver(headless=True)
        cls.base_url = get_base_url()
        cls.home_page = HomePage(cls.driver)
        cls.add_page = AddPostPage(cls.driver)
    
    def test_create_post_success(self):
        # Navigate to add post page
        self.home_page.navigate_to(self.base_url)
        self.home_page.click_add_post()
        
        # Fill and submit form
        self.add_page.fill_form(
            title="Test Post Title",
            content="This is test content for the new post.",
            author="Test Author"
        )
        self.add_page.submit_form()
        
        # Verify post appears in list
        self.home_page.wait_for_posts_to_load()
        post_titles = self.home_page.get_post_titles()
        assert "Test Post Title" in post_titles
```

## Test Data Management

### Test Fixtures

```python
@pytest.fixture
def sample_post():
    return Post.objects.create(
        title='Sample Post Title',
        content='This is sample content for testing.',
        author='Sample Author',
        tags='sample, test'
    )

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()
```

## Performance Testing

### Load Testing with Locust

```python
from locust import HttpUser, task, between
import json

class BlogPostUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def list_posts(self):
        self.client.get("/api/posts/")
    
    @task(1)
    def create_post(self):
        post_data = {
            "title": "Load Test Post",
            "content": "This is content for load testing.",
            "author": "Load Test Author"
        }
        
        self.client.post(
            "/api/posts/",
            data=json.dumps(post_data),
            headers={"Content-Type": "application/json"}
        )
```

## Best Practices

### Test Organization
1. **Follow AAA Pattern**: Arrange, Act, Assert
2. **One Assertion Per Test**: Focus on single behavior
3. **Descriptive Test Names**: Clearly describe what is being tested
4. **Independent Tests**: Tests should not depend on each other

### Coverage Goals
- **Unit Tests**: 90%+ coverage
- **Integration Tests**: Cover all API endpoints
- **E2E Tests**: Cover critical user journeys
- **Overall**: Maintain 80%+ total coverage

### Continuous Integration

Tests run automatically on:
- Pull requests
- Pushes to main branch
- Scheduled nightly builds

Coverage reports are generated and tracked over time to ensure quality standards are maintained.