# FinTalk Enhanced Blog Platform - API Documentation

## Overview

The FinTalk Enhanced Blog Platform provides a comprehensive REST API for managing blog posts, user authentication, role-based access control, email subscriptions, content moderation, and social features. This API is built using Django REST Framework and follows RESTful conventions.

**Version:** 1.0.0  
**Base URL:** `http://localhost:8000/api/` (development) / `https://yourdomain.com/api/` (production)  
**Authentication:** Session-based authentication with CSRF protection  
**Content Type:** `application/json`

## Quick Start

1. **Register Account**: Create and verify your account
2. **Authenticate**: Log in to receive session cookie
3. **Create Content**: Use posts endpoints to create articles
4. **Social Features**: Follow users and save articles
5. **Moderation**: Flag inappropriate content when needed

## Authentication

### Session-Based Authentication

The API uses Django's session-based authentication. Include session cookies in requests to authenticated endpoints.

**Headers for authenticated requests:**
```
Cookie: sessionid=<session_id>
X-CSRFToken: <csrf_token>
```

### Authentication Endpoints

#### Register User
**POST** `/api/auth/register/`

Create a new user account with email verification.

**Request:**
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

**Response (201):**
```json
{
    "message": "User registered successfully. Please check your email for verification.",
    "user_id": 123,
    "username": "newuser",
    "email": "user@example.com"
}
```

#### Login
**POST** `/api/auth/login/`

Authenticate user and create session.

**Request:**
```json
{
    "username": "newuser",
    "password": "strongpassword123"
}
```

**Response (200):**
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

#### Logout
**POST** `/api/auth/logout/`

End user session.

#### Email Verification
**POST** `/api/auth/verify-email/`

Verify email with token.

**Request:**
```json
{
    "token": "abc123def456"
}
```

#### User Profile
**GET** `/api/auth/profile/`

Get current user's profile.

**PATCH** `/api/auth/profile/`

Update user profile.

**Request:**
```json
{
    "bio": "Financial analyst and blogger",
    "website": "https://example.com",
    "location": "New York, NY"
}
```

## Posts API

### List Posts
**GET** `/api/posts/`

Get paginated list of published posts.

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 10, max: 50)
- `search`: Search in title and content
- `author`: Filter by author username
- `tags`: Filter by tags (comma-separated)
- `ordering`: Sort by field (`-created_at`, `title`, `-view_count`)

**Response (200):**
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
                "full_name": "John Doe",
                "avatar_url": "/media/avatars/123.jpg"
            },
            "tags": "finance, markets, investing",
            "tags_list": ["finance", "markets", "investing"],
            "image_url": "https://example.com/image.jpg",
            "status": "published",
            "view_count": 1250,
            "like_count": 45,
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:00:00Z",
            "media_files": [
                {
                    "id": 1,
                    "file_url": "/media/2024/01/01/chart.png",
                    "thumbnail_url": "/media/thumbnails/chart.png",
                    "file_type": "image",
                    "alt_text": "Financial market chart"
                }
            ]
        }
    ]
}
```

### Create Post
**POST** `/api/posts/`

Create new blog post (writer+ role required).

**Request:**
```json
{
    "title": "New Financial Insights",
    "content": "Today I want to share insights about market trends...",
    "tags": "finance, insights, analysis",
    "image_url": "https://example.com/image.jpg",
    "status": "draft"
}
```

**Response (201):**
```json
{
    "id": 2,
    "title": "New Financial Insights",
    "content": "Today I want to share insights about market trends...",
    "author": "John Doe",
    "author_user": {
        "id": 123,
        "username": "johndoe",
        "full_name": "John Doe"
    },
    "tags": "finance, insights, analysis",
    "tags_list": ["finance", "insights", "analysis"],
    "status": "draft",
    "created_at": "2024-01-15T14:30:00Z",
    "updated_at": "2024-01-15T14:30:00Z"
}
```

### Get Post
**GET** `/api/posts/{id}/`

Get specific post details.

### Update Post
**PUT/PATCH** `/api/posts/{id}/`

Update existing post (author or editor+ required).

### Delete Post
**DELETE** `/api/posts/{id}/`

Delete post (author or editor+ required).

### Draft Posts
**GET** `/api/posts/drafts/`

Get user's draft posts (authenticated users only).

### Schedule Post
**POST** `/api/posts/{id}/schedule/`

Schedule post for future publication.

**Request:**
```json
{
    "scheduled_publish_date": "2024-02-01T09:00:00Z"
}
```

### Publish Post
**POST** `/api/posts/{id}/publish/`

Immediately publish a draft or scheduled post.

## Social Features

### Save Article
**POST** `/api/posts/{id}/save/`

Save article for later reading.

**Response (201):**
```json
{
    "message": "Article saved successfully",
    "saved_at": "2024-01-15T14:30:00Z"
}
```

### Unsave Article
**DELETE** `/api/posts/{id}/save/`

Remove article from saved list.

### List Saved Articles
**GET** `/api/posts/saved/`

Get user's saved articles.

### Follow User
**POST** `/api/auth/users/{id}/follow/`

Follow another user.

**Response (201):**
```json
{
    "message": "Successfully followed user",
    "following": true
}
```

### Unfollow User
**DELETE** `/api/auth/users/{id}/follow/`

Unfollow user.

### User Followers
**GET** `/api/auth/users/{id}/followers/`

Get user's followers list.

### User Following
**GET** `/api/auth/users/{id}/following/`

Get users that this user follows.

## Media Upload

### Upload Media
**POST** `/api/posts/media/upload/`

Upload image or video file.

**Request (multipart/form-data):**
```
file: [binary file data]
alt_text: "Description of the image"
```

**Response (201):**
```json
{
    "id": 1,
    "file_url": "/media/2024/01/15/image.jpg",
    "thumbnail_url": "/media/thumbnails/image.jpg",
    "file_type": "image",
    "original_name": "financial_chart.jpg",
    "file_size": 245760,
    "alt_text": "Financial market chart",
    "width": 1200,
    "height": 800,
    "created_at": "2024-01-15T14:30:00Z"
}
```

### List Media Files
**GET** `/api/posts/media/`

Get user's uploaded media files.

### Attach Media to Post
**POST** `/api/posts/{id}/media/`

Attach media files to a post.

**Request:**
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

## Email Subscriptions

### Subscribe
**POST** `/api/notifications/subscribe/`

Subscribe to email notifications.

**Request:**
```json
{
    "email": "subscriber@example.com",
    "subscription_type": "all_posts"
}
```

**Response (201):**
```json
{
    "message": "Successfully subscribed",
    "subscription_id": 123,
    "unsubscribe_token": "abc123def456"
}
```

### Manage Subscriptions
**GET** `/api/notifications/subscriptions/`

Get user's subscriptions (authenticated users).

### Unsubscribe
**GET** `/api/notifications/unsubscribe/{token}/`

Unsubscribe using token from email.

## Content Moderation

### Flag Content
**POST** `/api/posts/{id}/flag/`

Flag inappropriate content.

**Request:**
```json
{
    "reason": "spam",
    "description": "This post appears to be spam content."
}
```

**Response (201):**
```json
{
    "id": 1,
    "reason": "spam",
    "status": "pending",
    "created_at": "2024-01-15T14:30:00Z",
    "message": "Content flagged successfully."
}
```

### List Flags (Moderators)
**GET** `/api/moderation/flags/`

Get content flags (moderator+ role required).

**Query Parameters:**
- `status`: Filter by status (`pending`, `under_review`, `resolved_valid`, `resolved_invalid`)
- `reason`: Filter by reason
- `post`: Filter by post ID

### Review Flag (Moderators)
**PUT** `/api/moderation/flags/{id}/`

Review and resolve flag (moderator+ role required).

**Request:**
```json
{
    "status": "resolved_valid",
    "resolution_notes": "Content removed for policy violation.",
    "action_taken": "content_removed"
}
```

### Moderation Dashboard
**GET** `/api/moderation/dashboard/`

Get moderation statistics (moderator+ role required).

## Role Management

### List Roles (Admin)
**GET** `/api/auth/roles/`

Get available roles (admin only).

### Assign Role (Admin)
**POST** `/api/auth/role-assignment/`

Assign role to user (admin/editor only).

**Request:**
```json
{
    "user_id": 123,
    "role_name": "writer",
    "notes": "Promoted based on quality content"
}
```

### Revoke Role (Admin)
**POST** `/api/auth/role-revocation/`

Revoke role from user (admin/editor only).

## System Monitoring

### Health Check
**GET** `/health/`

Check API health status.

**Response (200):**
```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T14:30:00Z",
    "version": "1.0.0",
    "database": "connected",
    "redis": "connected"
}
```

### System Stats (Admin)
**GET** `/api/monitoring/stats/`

Get system statistics (admin only).

## Error Handling

### Standard Error Format

```json
{
    "error": "Error message",
    "code": "ERROR_CODE",
    "details": {
        "field_name": ["Specific field error message"]
    }
}
```

### HTTP Status Codes

- **200 OK**: Request successful
- **201 Created**: Resource created
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error

### Common Errors

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

**400 Validation Error:**
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

- **Anonymous users**: 100 requests/hour
- **Authenticated users**: 1000 requests/hour
- **Premium users**: 5000 requests/hour

Rate limit headers:
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

Query parameters for filtering:
- **Search**: `?search=keyword`
- **Filtering**: `?field_name=value`
- **Ordering**: `?ordering=-created_at`
- **Date ranges**: `?created_after=2024-01-01&created_before=2024-01-31`

## Data Validation

### Post Validation
- **Title**: 5-200 characters, no HTML
- **Content**: Minimum 10 characters, safe HTML allowed
- **Author**: 2-100 characters, no HTML
- **Tags**: Maximum 500 characters, comma-separated
- **Image URL**: Valid URL format

### User Validation
- **Username**: 3-150 characters, alphanumeric and @/./+/-/_ only
- **Email**: Valid email format
- **Password**: Minimum 8 characters, not too common
- **Bio**: Maximum 500 characters
- **Website**: Valid URL format

## Security Features

### Input Sanitization
- HTML content sanitization to prevent XSS
- SQL injection protection via Django ORM
- URL validation for image URLs
- File type validation for uploads

### CORS Configuration
- Configured for specific origins only
- Credentials support for authenticated requests
- Preflight request handling

### CSRF Protection
- CSRF tokens required for state-changing requests
- Secure cookie settings
- Trusted origins configuration

## Testing the API

### Using cURL

**List Posts:**
```bash
curl -X GET "http://localhost:8000/api/posts/" \
  -H "Accept: application/json"
```

**Create Post:**
```bash
curl -X POST "http://localhost:8000/api/posts/" \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: your-csrf-token" \
  -b "sessionid=your-session-id" \
  -d '{
    "title": "Test Post",
    "content": "This is test content with sufficient length.",
    "tags": "test, api"
  }'
```

### Using Python Requests

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000/api"
session = requests.Session()

# Login
login_data = {
    "username": "testuser",
    "password": "testpassword"
}
response = session.post(f"{BASE_URL}/auth/login/", json=login_data)

# Get CSRF token
csrf_token = session.cookies.get('csrftoken')
session.headers.update({'X-CSRFToken': csrf_token})

# Create post
post_data = {
    "title": "API Test Post",
    "content": "Testing the API using Python requests.",
    "tags": "python, api, testing"
}
response = session.post(f"{BASE_URL}/posts/", json=post_data)
print(response.json())
```

### Using JavaScript/Axios

```javascript
import axios from 'axios';

// Configure axios with credentials
const api = axios.create({
    baseURL: 'http://localhost:8000/api/',
    withCredentials: true,
    headers: {
        'Content-Type': 'application/json',
    }
});

// Add CSRF token to requests
api.interceptors.request.use((config) => {
    const csrfToken = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    
    if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken;
    }
    
    return config;
});

// Login
const login = async (username, password) => {
    const response = await api.post('/auth/login/', {
        username,
        password
    });
    return response.data;
};

// Create post
const createPost = async (postData) => {
    const response = await api.post('/posts/', postData);
    return response.data;
};
```

## Webhooks (Future Enhancement)

Planned webhook events:
- `post.published`: New post published
- `user.registered`: New user registered
- `content.flagged`: Content flagged for moderation
- `subscription.created`: New email subscription

## API Versioning

Current version: v1
Future versions will use URL-based versioning:
- `/api/v1/posts/` (current)
- `/api/v2/posts/` (future)

## Support and Resources

- **API Documentation**: Interactive docs at `/api/docs/`
- **Postman Collection**: Available for download
- **SDK Libraries**: JavaScript, Python, PHP, Ruby
- **Community Forum**: Developer discussions and support
- **GitHub Issues**: Bug reports and feature requests

---

For additional help or questions about the API, please refer to the user guide or contact our support team.