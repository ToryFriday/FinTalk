"""
Performance and load testing using Locust.
Run with: locust -f test_performance_load.py --host=http://localhost:8000
"""

import json
import random
from locust import HttpUser, task, between


class BlogPlatformUser(HttpUser):
    """Simulates a user interacting with the blog platform."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Called when a user starts. Perform login."""
        # Create a test user or use existing one
        self.username = f"testuser_{random.randint(1000, 9999)}"
        self.email = f"{self.username}@example.com"
        self.password = "testpass123"
        
        # Register user
        registration_data = {
            "username": self.username,
            "email": self.email,
            "password": self.password,
            "password_confirm": self.password,
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = self.client.post("/api/auth/register/", json=registration_data)
        if response.status_code == 201:
            # Login
            login_data = {
                "username": self.username,
                "password": self.password
            }
            self.client.post("/api/auth/login/", json=login_data)
    
    @task(3)
    def view_posts(self):
        """View list of posts (most common action)."""
        self.client.get("/api/posts/")
    
    @task(2)
    def view_post_detail(self):
        """View a specific post detail."""
        # Get a random post ID (assuming posts exist)
        response = self.client.get("/api/posts/")
        if response.status_code == 200:
            posts = response.json().get('results', [])
            if posts:
                post_id = random.choice(posts)['id']
                self.client.get(f"/api/posts/{post_id}/")
    
    @task(1)
    def search_posts(self):
        """Search for posts."""
        search_terms = ["finance", "investment", "market", "trading", "analysis"]
        search_term = random.choice(search_terms)
        self.client.get(f"/api/posts/?search={search_term}")
    
    @task(1)
    def view_user_profile(self):
        """View user profile."""
        self.client.get("/api/auth/profile/")
    
    @task(1)
    def create_post(self):
        """Create a new post (authenticated users only)."""
        post_data = {
            "title": f"Test Post {random.randint(1, 1000)}",
            "content": "This is a test post content for performance testing. " * 10,
            "tags": "test, performance, load",
            "status": "draft"
        }
        self.client.post("/api/posts/", json=post_data)
    
    @task(1)
    def save_post(self):
        """Save a post for later reading."""
        # Get a random post to save
        response = self.client.get("/api/posts/")
        if response.status_code == 200:
            posts = response.json().get('results', [])
            if posts:
                post_id = random.choice(posts)['id']
                self.client.post(f"/api/posts/{post_id}/save/")


class AnonymousUser(HttpUser):
    """Simulates anonymous users browsing the platform."""
    
    wait_time = between(2, 5)
    
    @task(5)
    def view_posts(self):
        """View public posts."""
        self.client.get("/api/posts/")
    
    @task(3)
    def view_post_detail(self):
        """View specific post details."""
        response = self.client.get("/api/posts/")
        if response.status_code == 200:
            posts = response.json().get('results', [])
            if posts:
                post_id = random.choice(posts)['id']
                self.client.get(f"/api/posts/{post_id}/")
    
    @task(2)
    def search_posts(self):
        """Search for posts."""
        search_terms = ["finance", "investment", "market", "trading", "analysis"]
        search_term = random.choice(search_terms)
        self.client.get(f"/api/posts/?search={search_term}")
    
    @task(1)
    def subscribe_to_notifications(self):
        """Subscribe to email notifications."""
        subscription_data = {
            "email": f"subscriber_{random.randint(1000, 9999)}@example.com",
            "subscription_type": "all_posts"
        }
        self.client.post("/api/notifications/subscribe/", json=subscription_data)


class ModeratorUser(HttpUser):
    """Simulates moderator users performing moderation tasks."""
    
    wait_time = between(5, 10)
    
    def on_start(self):
        """Login as moderator."""
        # Use a pre-created moderator account
        login_data = {
            "username": "moderator",
            "password": "moderatorpass123"
        }
        self.client.post("/api/auth/login/", json=login_data)
    
    @task(3)
    def view_moderation_dashboard(self):
        """View moderation dashboard."""
        self.client.get("/api/moderation/dashboard/")
    
    @task(2)
    def view_content_flags(self):
        """View content flags."""
        self.client.get("/api/moderation/flags/")
    
    @task(1)
    def review_flag(self):
        """Review a content flag."""
        # Get pending flags
        response = self.client.get("/api/moderation/flags/?status=pending")
        if response.status_code == 200:
            flags = response.json().get('results', [])
            if flags:
                flag_id = random.choice(flags)['id']
                resolution_data = {
                    "status": "resolved_invalid",
                    "resolution_notes": "Content is appropriate."
                }
                self.client.put(f"/api/moderation/flags/{flag_id}/", json=resolution_data)


# Performance test scenarios
class HighLoadScenario(HttpUser):
    """High load scenario for stress testing."""
    
    wait_time = between(0.5, 1.5)  # Faster requests
    
    @task
    def rapid_post_viewing(self):
        """Rapidly view posts to test under load."""
        self.client.get("/api/posts/")
        
        # Sometimes view post details
        if random.random() < 0.3:
            response = self.client.get("/api/posts/")
            if response.status_code == 200:
                posts = response.json().get('results', [])
                if posts:
                    post_id = random.choice(posts)['id']
                    self.client.get(f"/api/posts/{post_id}/")


class DatabaseStressTest(HttpUser):
    """Test database performance under load."""
    
    wait_time = between(0.1, 0.5)  # Very fast requests
    
    @task(2)
    def complex_search(self):
        """Perform complex searches that stress the database."""
        search_params = {
            "search": random.choice(["finance", "investment", "market"]),
            "ordering": random.choice(["-created_at", "title", "-view_count"]),
            "page_size": random.choice([10, 25, 50])
        }
        
        params = "&".join([f"{k}={v}" for k, v in search_params.items()])
        self.client.get(f"/api/posts/?{params}")
    
    @task(1)
    def filter_posts(self):
        """Filter posts by various criteria."""
        filters = {
            "author": f"user{random.randint(1, 100)}",
            "tags": random.choice(["finance", "investment", "trading"]),
        }
        
        params = "&".join([f"{k}={v}" for k, v in filters.items()])
        self.client.get(f"/api/posts/?{params}")


# Custom test for specific endpoints
class APIEndpointTest(HttpUser):
    """Test specific API endpoints for performance."""
    
    wait_time = between(1, 2)
    
    def on_start(self):
        """Setup test user."""
        self.username = f"apitest_{random.randint(1000, 9999)}"
        login_data = {
            "username": self.username,
            "password": "testpass123"
        }
        # Assume user exists or create one
        self.client.post("/api/auth/login/", json=login_data)
    
    @task
    def test_pagination_performance(self):
        """Test pagination performance with different page sizes."""
        page_sizes = [10, 25, 50, 100]
        page_size = random.choice(page_sizes)
        page = random.randint(1, 5)
        
        self.client.get(f"/api/posts/?page={page}&page_size={page_size}")
    
    @task
    def test_concurrent_post_creation(self):
        """Test concurrent post creation."""
        post_data = {
            "title": f"Concurrent Test Post {random.randint(1, 10000)}",
            "content": "This is a test post for concurrent creation testing. " * 5,
            "tags": "test, concurrent, performance",
            "status": "draft"
        }
        self.client.post("/api/posts/", json=post_data)
    
    @task
    def test_media_upload_simulation(self):
        """Simulate media upload (without actual file)."""
        # This would normally upload a file, but we'll just test the endpoint
        self.client.get("/api/posts/media/")  # List media files instead


if __name__ == "__main__":
    # Run specific performance tests
    import subprocess
    import sys
    
    print("Running performance tests...")
    print("Make sure your Django server is running on http://localhost:8000")
    print("\nAvailable test scenarios:")
    print("1. BlogPlatformUser - Normal user behavior")
    print("2. AnonymousUser - Anonymous browsing")
    print("3. ModeratorUser - Moderation tasks")
    print("4. HighLoadScenario - High load stress test")
    print("5. DatabaseStressTest - Database performance")
    print("6. APIEndpointTest - Specific endpoint testing")
    
    # Example commands to run different scenarios:
    print("\nExample commands:")
    print("locust -f test_performance_load.py BlogPlatformUser --host=http://localhost:8000")
    print("locust -f test_performance_load.py HighLoadScenario --host=http://localhost:8000 --users 100 --spawn-rate 10")