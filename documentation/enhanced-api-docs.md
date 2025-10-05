# Enhanced FinTalk Platform API Documentation

## Overview

The Enhanced FinTalk Platform provides a comprehensive REST API for managing blog posts, user authentication, role-based access control, email subscriptions, content moderation, and social features. This API is built using Django REST Framework and follows RESTful conventions.

**Version:** 1.0.0  
**Last Updated:** 2024-01-15  
**Test Coverage:** 85%+  

## Base URL

```
http://localhost:8000/api/
```

## Quick Start

1. **Authentication**: Register and verify your account
2. **Create Content**: Use the posts endpoints to create articles
3. **Social Features**: Follow users and save articles
4. **Moderation**: Flag inappropriate content
5. **Notifications**: Subscribe to email updates

## Authentication

The API uses session-based authentication. Users must log in to access protected endpoints.

### Authentication Headers

For authenticated requests, include the session cookie or use the following header:

```
Cookie: sessionid=<session_id>
```

## API Endpoints

### 1. Authentication Endpoints

#### 1.1 User Registration

**POST** `/api/auth/register/`

Register a new user account with email verification.

**Request Body:**
```json
{
    "username": "newuser",
    "email": "user@example.com",
    "password": "strongpassword123",
    "password_confirm": "strongpassword123",
    "first_name": "John",
    "last_name": "Doe"
}
```

**Response (201 Created):**
```json
{
    "message": "User registered successfully. Please check your email for verification.",
    "user_id": 123,
    "username": "newuser",
    "email": "user@example.com"
}
```

**Response (400 Bad Request):**
```json
{
    "username": ["A user with that username already exists."],
    "email": ["User with this email already exists."],
    "password_confirm": ["Passwords do not match."]
}
```

#### 1.2 User Login

**POST** `/api/auth/login/`

Authenticate user and create session.

**Request Body:**
```json
{
    "username": "newuser",
    "password": "strongpassword123"
}
```

**Response (200 OK):**
```json
{
    "message": "Login successful",
    "user": {
        "id": 123,
        "username": "newuser",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "is_email_verified": true,
        "roles": ["reader"]
    }
}
```

#### 1.3 User Logout

**POST** `/api/auth/logout/`

End user session.

**Response (200 OK):**
```json
{
    "message": "Logout successful"
}
```

#### 1.4 Email Verification

**POST** `/api/auth/verify-email/`

Verify user email with token.

**Request Body:**
```json
{
    "token": "abc123def456"
}
```

**Response (200 OK):**
```json
{
    "message": "Email verified successfully"
}
```

**GET** `/api/auth/verify-email/<token>/`

Verify email via GET request (for email links).

#### 1.5 Resend Verification Email

**POST** `/api/auth/resend-verification/`

Resend email verification token.

**Request Body:**
```json
{
    "email": "user@example.com"
}
```

#### 1.6 User Profile

**GET** `/api/auth/profile/`

Get current user's profile information.

**Response (200 OK):**
```json
{
    "id": 123,
    "username": "newuser",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "bio": "Software developer and financial blogger",
    "website": "https://johndoe.com",
    "location": "New York, NY",
    "birth_date": "1990-01-15",
    "age": 34,
    "avatar_url": "/media/avatars/123_abc123.jpg",
    "is_email_verified": true,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-15T14:30:00Z"
}
```

**PATCH** `/api/auth/profile/`

Update user profile information.

**Request Body:**
```json
{
    "bio": "Updated bio text",
    "website": "https://newwebsite.com",
    "location": "San Francisco, CA",
    "first_name": "Jonathan"
}
```

#### 1.7 Public User Profile

**GET** `/api/auth/profile/<user_id>/`

Get public profile information for any user.

### 2. Role-Based Access Control (RBAC) Endpoints

#### 2.1 List Roles

**GET** `/api/auth/roles/`

Get list of available roles (admin only).

**Response (200 OK):**
```json
{
    "count": 5,
    "results": [
        {
            "id": 1,
            "name": "admin",
            "display_name": "Administrator",
            "description": "Full system access",
            "is_active": true,
            "permissions": ["can_manage_users", "can_moderate_content"]
        },
        {
            "id": 2,
            "name": "editor",
            "display_name": "Editor",
            "description": "Content moderation and writer management",
            "is_active": true,
            "permissions": ["can_moderate_content", "can_manage_writers"]
        }
    ]
}
```

#### 2.2 Role Assignment

**POST** `/api/auth/role-assignment/`

Assign role to user (admin/editor only).

**Request Body:**
```json
{
    "user_id": 123,
    "role_name": "writer",
    "notes": "Promoted to writer role"
}
```

#### 2.3 Role Revocation

**POST** `/api/auth/role-revocation/`

Revoke role from user (admin/editor only).

**Request Body:**
```json
{
    "user_id": 123,
    "role_name": "writer"
}
```

### 3. Posts Endpoints

#### 3.1 List Posts

**GET** `/api/posts/`

Get paginated list of published posts.

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Number of posts per page (default: 10, max: 50)
- `search`: Search in title and content
- `author`: Filter by author username
- `tags`: Filter by tags (comma-separated)
- `ordering`: Sort by field (`-created_at`, `title`, `-view_count`)

**Response (200 OK):**
```json
{
    "count": 150,
    "next": "http://localhost:8000/api/posts/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "title": "Understanding Financial Markets",
            "content": "Financial markets are complex systems...",
            "author": "John Doe",
            "author_user": {
                "id": 123,
                "username": "johndoe",
                "full_name": "John Doe"
            },
            "tags": "finance, markets, investing",
            "image_url": "https://example.com/image.jpg",
            "status": "published",
            "view_count": 1250,
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:00:00Z",
            "media_files": [
                {
                    "id": 1,
                    "file_url": "/media/2024/01/01/chart.png",
                    "thumbnail_url": "/media/thumbnails/2024/01/01/thumb_chart.png",
                    "file_type": "image",
                    "alt_text": "Financial market chart"
                }
            ]
        }
    ]
}
```

#### 3.2 Create Post

**POST** `/api/posts/`

Create a new blog post (writer+ role required).

**Request Body:**
```json
{
    "title": "New Financial Insights",
    "content": "Today I want to share some insights about...",
    "tags": "finance, insights, analysis",
    "image_url": "https://example.com/image.jpg",
    "status": "draft"
}
```

**Response (201 Created):**
```json
{
    "id": 2,
    "title": "New Financial Insights",
    "content": "Today I want to share some insights about...",
    "author": "John Doe",
    "author_user": {
        "id": 123,
        "username": "johndoe",
        "full_name": "John Doe"
    },
    "tags": "finance, insights, analysis",
    "status": "draft",
    "created_at": "2024-01-15T14:30:00Z"
}
```

#### 3.3 Get Post Details

**GET** `/api/posts/<post_id>/`

Get detailed information about a specific post.

#### 3.4 Update Post

**PUT/PATCH** `/api/posts/<post_id>/`

Update an existing post (author or editor+ required).

#### 3.5 Delete Post

**DELETE** `/api/posts/<post_id>/`

Delete a post (author or editor+ required).

#### 3.6 Draft Posts

**GET** `/api/posts/drafts/`

Get user's draft posts (authenticated users only).

#### 3.7 Schedule Post

**POST** `/api/posts/<post_id>/schedule/`

Schedule a post for future publication.

**Request Body:**
```json
{
    "scheduled_publish_date": "2024-02-01T09:00:00Z"
}
```

#### 3.8 Publish Post

**POST** `/api/posts/<post_id>/publish/`

Immediately publish a draft or scheduled post.

### 4. Saved Articles Endpoints

#### 4.1 Save Article

**POST** `/api/posts/<post_id>/save/`

Save an article for later reading (authenticated users only).

**Response (201 Created):**
```json
{
    "message": "Article saved successfully",
    "saved_at": "2024-01-15T14:30:00Z"
}
```

#### 4.2 Unsave Article

**DELETE** `/api/posts/<post_id>/save/`

Remove article from saved list.

#### 4.3 List Saved Articles

**GET** `/api/posts/saved/`

Get user's saved articles.

**Response (200 OK):**
```json
{
    "count": 5,
    "results": [
        {
            "id": 1,
            "post": {
                "id": 1,
                "title": "Understanding Financial Markets",
                "author": "John Doe",
                "created_at": "2024-01-01T10:00:00Z"
            },
            "saved_at": "2024-01-10T15:20:00Z",
            "notes": "Great article about market analysis"
        }
    ]
}
```

### 5. Media Upload Endpoints

#### 5.1 Upload Media File

**POST** `/api/posts/media/upload/`

Upload image or video file (authenticated users only).

**Request Body (multipart/form-data):**
```
file: [binary file data]
alt_text: "Description of the image"
```

**Response (201 Created):**
```json
{
    "id": 1,
    "file_url": "/media/2024/01/15/image.jpg",
    "thumbnail_url": "/media/thumbnails/2024/01/15/thumb_image.jpg",
    "file_type": "image",
    "original_name": "financial_chart.jpg",
    "file_size": 245760,
    "alt_text": "Financial market chart showing growth",
    "width": 1200,
    "height": 800,
    "created_at": "2024-01-15T14:30:00Z"
}
```

#### 5.2 List Media Files

**GET** `/api/posts/media/`

Get user's uploaded media files.

#### 5.3 Attach Media to Post

**POST** `/api/posts/<post_id>/media/`

Attach media files to a post.

**Request Body:**
```json
{
    "media_files": [
        {
            "media_file_id": 1,
            "order": 0,
            "caption": "Market analysis chart"
        }
    ]
}
```

### 6. Social Features Endpoints

#### 6.1 Follow User

**POST** `/api/auth/users/<user_id>/follow/`

Follow another user (authenticated users only).

**Response (201 Created):**
```json
{
    "message": "Successfully followed user",
    "following": true
}
```

#### 6.2 Unfollow User

**DELETE** `/api/auth/users/<user_id>/follow/`

Unfollow a user.

#### 6.3 User Followers

**GET** `/api/auth/users/<user_id>/followers/`

Get list of user's followers.

**Response (200 OK):**
```json
{
    "count": 25,
    "results": [
        {
            "id": 456,
            "username": "follower1",
            "full_name": "Jane Smith",
            "avatar_url": "/media/avatars/456_def789.jpg",
            "followed_at": "2024-01-10T12:00:00Z"
        }
    ]
}
```

#### 6.4 User Following

**GET** `/api/auth/users/<user_id>/following/`

Get list of users that this user follows.

### 7. Email Subscription Endpoints

#### 7.1 Subscribe to Notifications

**POST** `/api/notifications/subscribe/`

Subscribe to email notifications (public endpoint).

**Request Body:**
```json
{
    "email": "subscriber@example.com",
    "subscription_type": "all_posts"
}
```

**Response (201 Created):**
```json
{
    "message": "Successfully subscribed to notifications",
    "subscription_id": 123,
    "unsubscribe_token": "abc123def456"
}
```

#### 7.2 Manage Subscriptions

**GET** `/api/notifications/subscriptions/`

Get user's email subscriptions (authenticated users only).

#### 7.3 Unsubscribe

**GET** `/api/notifications/unsubscribe/<token>/`

Unsubscribe from notifications using token.

#### 7.4 Author Subscription Toggle

**POST** `/api/notifications/authors/<author_id>/toggle/`

Subscribe/unsubscribe to specific author's posts.

### 8. Content Moderation Endpoints

#### 8.1 Flag Content

**POST** `/api/posts/<post_id>/flag/`

Flag inappropriate content (authenticated users only).

**Request Body:**
```json
{
    "reason": "spam",
    "description": "This post appears to be spam content promoting unrelated products."
}
```

**Response (201 Created):**
```json
{
    "id": 1,
    "reason": "spam",
    "status": "pending",
    "created_at": "2024-01-15T14:30:00Z",
    "message": "Content flagged successfully. Moderators will review it shortly."
}
```

#### 8.2 List Content Flags

**GET** `/api/moderation/flags/`

Get list of content flags (moderator+ role required).

**Query Parameters:**
- `status`: Filter by flag status (`pending`, `under_review`, `resolved_valid`, `resolved_invalid`)
- `reason`: Filter by flag reason
- `post`: Filter by post ID

**Response (200 OK):**
```json
{
    "count": 15,
    "summary": {
        "pending": 8,
        "under_review": 3,
        "resolved_valid": 3,
        "resolved_invalid": 1
    },
    "results": [
        {
            "id": 1,
            "post": {
                "id": 1,
                "title": "Understanding Financial Markets",
                "author": "John Doe"
            },
            "flagged_by": {
                "id": 456,
                "username": "reporter1"
            },
            "reason": "spam",
            "description": "This post appears to be spam...",
            "status": "pending",
            "created_at": "2024-01-15T14:30:00Z"
        }
    ]
}
```

#### 8.3 Review Flag

**PUT** `/api/moderation/flags/<flag_id>/`

Review and resolve a content flag (moderator+ role required).

**Request Body:**
```json
{
    "status": "resolved_valid",
    "resolution_notes": "Content removed for violating community guidelines.",
    "action_taken": "content_removed"
}
```

#### 8.4 Moderation Dashboard

**GET** `/api/moderation/dashboard/`

Get moderation dashboard statistics (moderator+ role required).

**Response (200 OK):**
```json
{
    "pending_flags": 8,
    "flags_today": 12,
    "flags_this_week": 45,
    "recent_actions": [
        {
            "id": 1,
            "action_type": "content_removed",
            "post_title": "Spam Post",
            "moderator": "admin",
            "created_at": "2024-01-15T14:00:00Z"
        }
    ],
    "flag_reasons_breakdown": {
        "spam": 15,
        "inappropriate": 8,
        "harassment": 3
    }
}
```

### 9. Monitoring and Health Endpoints

#### 9.1 Health Check

**GET** `/health/`

Check API health status.

**Response (200 OK):**
```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T14:30:00Z",
    "version": "1.0.0",
    "database": "connected",
    "redis": "connected"
}
```

#### 9.2 System Monitoring

**GET** `/api/monitoring/stats/`

Get system statistics (admin only).

**Response (200 OK):**
```json
{
    "users": {
        "total": 1250,
        "active_today": 45,
        "new_this_week": 12
    },
    "posts": {
        "total": 350,
        "published": 320,
        "drafts": 25,
        "scheduled": 5
    },
    "system": {
        "cpu_usage": 25.5,
        "memory_usage": 68.2,
        "disk_usage": 45.8
    }
}
```

## Error Responses

### Standard Error Format

All API errors follow a consistent format:

```json
{
    "error": "Error message",
    "code": "ERROR_CODE",
    "details": {
        "field_name": ["Specific field error message"]
    }
}
```

### Common HTTP Status Codes

- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error

### Error Examples

**401 Unauthorized:**
```json
{
    "error": "Authentication credentials were not provided.",
    "code": "AUTHENTICATION_REQUIRED"
}
```

**403 Forbidden:**
```json
{
    "error": "You do not have permission to perform this action.",
    "code": "PERMISSION_DENIED"
}
```

**400 Bad Request:**
```json
{
    "error": "Validation failed",
    "code": "VALIDATION_ERROR",
    "details": {
        "title": ["This field is required."],
        "email": ["Enter a valid email address."]
    }
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Anonymous users**: 100 requests per hour
- **Authenticated users**: 1000 requests per hour
- **Premium users**: 5000 requests per hour

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642262400
```

## Pagination

List endpoints use cursor-based pagination:

```json
{
    "count": 150,
    "next": "http://localhost:8000/api/posts/?cursor=abc123",
    "previous": "http://localhost:8000/api/posts/?cursor=def456",
    "results": [...]
}
```

## Filtering and Searching

Many endpoints support filtering and searching:

- **Search**: `?search=keyword`
- **Filtering**: `?field_name=value`
- **Ordering**: `?ordering=-created_at`
- **Date ranges**: `?created_after=2024-01-01&created_before=2024-01-31`

## Webhooks

The API supports webhooks for real-time notifications:

### Available Events

- `post.published`: New post published
- `user.registered`: New user registered
- `content.flagged`: Content flagged for moderation
- `subscription.created`: New email subscription

### Webhook Payload Example

```json
{
    "event": "post.published",
    "timestamp": "2024-01-15T14:30:00Z",
    "data": {
        "post": {
            "id": 1,
            "title": "New Financial Insights",
            "author": "John Doe",
            "url": "http://localhost:3000/posts/1"
        }
    }
}
```

## SDK and Client Libraries

Official client libraries are available for:

- JavaScript/TypeScript
- Python
- PHP
- Ruby

Example JavaScript usage:

```javascript
import { FinTalkAPI } from '@fintalk/api-client';

const api = new FinTalkAPI({
    baseURL: 'http://localhost:8000/api/',
    sessionId: 'your-session-id'
});

// Get posts
const posts = await api.posts.list({ page: 1, page_size: 10 });

// Create post
const newPost = await api.posts.create({
    title: 'My New Post',
    content: 'Post content here...',
    status: 'draft'
});
```

## Testing

The API includes comprehensive test coverage with unit tests, integration tests, and performance tests.

### Test Coverage

- **Unit Tests**: 85%+ coverage for all models, serializers, and views
- **Integration Tests**: Complete user workflow testing
- **Performance Tests**: Load testing with Locust
- **API Documentation**: Automated documentation validation

### Running Tests

```bash
# Setup testing environment (first time only)
python setup_testing.py

# Run comprehensive test suite
python run_comprehensive_tests.py

# Run specific test types
pytest -m unit                    # Unit tests only
pytest -m integration            # Integration tests only
pytest -m performance           # Performance tests only

# Run with coverage
pytest --cov=. --cov-report=html --cov-report=term-missing

# Run load tests
locust -f test_performance_load.py --host=http://localhost:8000
```

### Test Categories

#### Unit Tests
- Model validation and methods
- Serializer functionality
- View permissions and responses
- Service layer logic

#### Integration Tests
- Complete user registration workflow
- Content creation and publishing
- Social interaction workflows
- Content moderation workflows
- Email notification workflows

#### Performance Tests
- API response times
- Database query optimization
- Pagination performance
- Search functionality performance
- Concurrent request handling

### Test Data Factories

The API includes comprehensive test data factories for consistent testing:

```python
from test_factories import UserFactory, PostFactory, create_blog_scenario

# Create test users
user = UserFactory()
admin = AdminUserFactory()

# Create test posts
post = PostFactory()
published_post = PublishedPostFactory()

# Create complete test scenario
scenario = create_blog_scenario()
```

### Continuous Integration

Tests are designed to run in CI/CD pipelines with:
- Automated test execution
- Coverage reporting
- Performance benchmarking
- API documentation validation

## Changelog

### Version 1.0.0 (2024-01-15)

- Initial release with full CRUD operations for posts
- User authentication and profile management
- Role-based access control (RBAC)
- Email subscription system
- Content moderation and flagging
- Social features (following, saved articles)
- Media upload and management
- Comprehensive API documentation

## Support

For API support and questions:

- Documentation: [API Docs](http://localhost:8000/api/docs/)
- Issues: [GitHub Issues](https://github.com/fintalk/api/issues)
- Email: api-support@fintalk.com