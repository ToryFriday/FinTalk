# API Documentation

## Overview

The Blog Post Manager API is a RESTful web service built with Django REST Framework. It provides endpoints for managing blog posts with full CRUD (Create, Read, Update, Delete) functionality.

## Base Information

- **Base URL**: `http://localhost:8000` (development) / `https://yourdomain.com` (production)
- **API Version**: v1
- **Content Type**: `application/json`
- **Authentication**: None (public API)

## Endpoints

### Posts

#### List All Posts

Retrieve a paginated list of all blog posts.

```http
GET /api/posts/
```

**Query Parameters:**
- `page` (optional): Page number for pagination (default: 1)
- `page_size` (optional): Number of items per page (default: 10, max: 100)

**Response (200 OK):**
```json
{
  "count": 25,
  "next": "http://localhost:8000/api/posts/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Getting Started with Django",
      "content": "Django is a high-level Python web framework that encourages rapid development...",
      "author": "John Doe",
      "tags": "django, python, web development",
      "tags_list": ["django", "python", "web development"],
      "image_url": "https://example.com/django-image.jpg",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": 2,
      "title": "React Best Practices",
      "content": "React is a popular JavaScript library for building user interfaces...",
      "author": "Jane Smith",
      "tags": "react, javascript, frontend",
      "tags_list": ["react", "javascript", "frontend"],
      "image_url": null,
      "created_at": "2024-01-14T15:45:00Z",
      "updated_at": "2024-01-16T09:20:00Z"
    }
  ]
}
```

#### Create New Post

Create a new blog post.

```http
POST /api/posts/
Content-Type: application/json
```

**Request Body:**
```json
{
  "title": "My New Blog Post",
  "content": "This is the content of my new blog post. It contains valuable information about web development and best practices.",
  "author": "Alice Johnson",
  "tags": "web development, tutorial, beginner",
  "image_url": "https://example.com/new-post-image.jpg"
}
```

**Response (201 Created):**
```json
{
  "id": 3,
  "title": "My New Blog Post",
  "content": "This is the content of my new blog post. It contains valuable information about web development and best practices.",
  "author": "Alice Johnson",
  "tags": "web development, tutorial, beginner",
  "tags_list": ["web development", "tutorial", "beginner"],
  "image_url": "https://example.com/new-post-image.jpg",
  "created_at": "2024-01-17T12:00:00Z",
  "updated_at": "2024-01-17T12:00:00Z"
}
```

#### Retrieve Specific Post

Get details of a specific blog post by ID.

```http
GET /api/posts/{id}/
```

**Path Parameters:**
- `id` (required): Integer ID of the post

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Getting Started with Django",
  "content": "Django is a high-level Python web framework that encourages rapid development and clean, pragmatic design. Built by experienced developers, it takes care of much of the hassle of web development, so you can focus on writing your app without needing to reinvent the wheel.",
  "author": "John Doe",
  "tags": "django, python, web development",
  "tags_list": ["django", "python", "web development"],
  "image_url": "https://example.com/django-image.jpg",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### Update Post

Update an existing blog post.

```http
PUT /api/posts/{id}/
Content-Type: application/json
```

**Path Parameters:**
- `id` (required): Integer ID of the post to update

**Request Body:**
```json
{
  "title": "Getting Started with Django - Updated",
  "content": "Django is a high-level Python web framework that encourages rapid development and clean, pragmatic design. This updated version includes more examples and best practices.",
  "author": "John Doe",
  "tags": "django, python, web development, updated",
  "image_url": "https://example.com/django-updated-image.jpg"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Getting Started with Django - Updated",
  "content": "Django is a high-level Python web framework that encourages rapid development and clean, pragmatic design. This updated version includes more examples and best practices.",
  "author": "John Doe",
  "tags": "django, python, web development, updated",
  "tags_list": ["django", "python", "web development", "updated"],
  "image_url": "https://example.com/django-updated-image.jpg",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-17T14:15:00Z"
}
```

#### Delete Post

Delete a specific blog post.

```http
DELETE /api/posts/{id}/
```

**Path Parameters:**
- `id` (required): Integer ID of the post to delete

**Response (204 No Content):**
```
(Empty response body)
```

## Data Models

### Post Model

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| id | Integer | Auto | Primary Key | Unique identifier |
| title | String | Yes | 5-200 chars | Post title |
| content | Text | Yes | Min 10 chars | Post content |
| author | String | Yes | 2-100 chars | Author name |
| tags | String | No | Max 500 chars | Comma-separated tags |
| image_url | URL | No | Valid URL | Optional image |
| created_at | DateTime | Auto | ISO 8601 | Creation timestamp |
| updated_at | DateTime | Auto | ISO 8601 | Last update timestamp |

## Validation Rules

### Title Validation
- **Required**: Yes
- **Length**: 5-200 characters
- **Format**: Plain text only (no HTML)
- **Security**: XSS protection, SQL injection prevention

### Content Validation
- **Required**: Yes
- **Length**: Minimum 10 characters
- **Format**: Safe HTML allowed (sanitized)
- **Security**: XSS protection, content length limits

### Author Validation
- **Required**: Yes
- **Length**: 2-100 characters
- **Format**: Plain text only (no HTML)
- **Security**: XSS protection, SQL injection prevention

### Tags Validation
- **Required**: No
- **Length**: Maximum 500 characters
- **Format**: Comma-separated values
- **Processing**: Automatically converted to array in response

### Image URL Validation
- **Required**: No
- **Format**: Valid URL format
- **Security**: URL validation, safe domain checking

## Error Handling

### HTTP Status Codes

- **200 OK**: Successful GET, PUT requests
- **201 Created**: Successful POST requests
- **204 No Content**: Successful DELETE requests
- **400 Bad Request**: Validation errors, malformed requests
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server-side errors

### Error Response Format

All error responses follow a consistent format:

```json
{
  "error": true,
  "message": "An error occurred",
  "details": {
    "field_name": ["Error message for this field"],
    "another_field": ["Another error message"]
  }
}
```

### Common Error Examples

#### Validation Error (400)
```json
{
  "error": true,
  "message": "An error occurred",
  "details": {
    "title": ["Title must be at least 5 characters long."],
    "content": ["Content must be at least 10 characters long."],
    "author": ["Author is required."]
  }
}
```

#### Not Found Error (404)
```json
{
  "error": true,
  "message": "An error occurred",
  "details": {
    "detail": "Not found."
  }
}
```

#### Server Error (500)
```json
{
  "error": true,
  "message": "An error occurred",
  "details": {
    "detail": "A server error occurred."
  }
}
```

## Pagination

The API uses cursor-based pagination for list endpoints:

### Pagination Parameters
- `page`: Page number (starts from 1)
- `page_size`: Items per page (default: 10, max: 100)

### Pagination Response
```json
{
  "count": 150,
  "next": "http://localhost:8000/api/posts/?page=3",
  "previous": "http://localhost:8000/api/posts/?page=1",
  "results": [...]
}
```

## Rate Limiting

Currently, no rate limiting is implemented. In production environments, consider implementing:

- **Per-IP limits**: 1000 requests per hour
- **Per-endpoint limits**: 100 POST requests per hour
- **Burst protection**: Maximum 10 requests per minute

## Security Features

### Input Sanitization
- HTML content is sanitized to prevent XSS attacks
- SQL injection protection through Django ORM
- URL validation for image URLs

### CORS Configuration
- Configured for specific origins only
- Credentials support enabled for authenticated requests
- Preflight request handling

### Content Security Policy
- XSS protection headers
- Content type validation
- Secure cookie settings

## API Testing

### Using cURL

#### List Posts
```bash
curl -X GET "http://localhost:8000/api/posts/" \
  -H "Accept: application/json"
```

#### Create Post
```bash
curl -X POST "http://localhost:8000/api/posts/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Post",
    "content": "This is a test post content with sufficient length.",
    "author": "Test Author",
    "tags": "test, api, curl"
  }'
```

#### Update Post
```bash
curl -X PUT "http://localhost:8000/api/posts/1/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Test Post",
    "content": "This is updated test post content.",
    "author": "Test Author",
    "tags": "test, api, curl, updated"
  }'
```

#### Delete Post
```bash
curl -X DELETE "http://localhost:8000/api/posts/1/"
```

### Using Python Requests

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000/api"

# List posts
response = requests.get(f"{BASE_URL}/posts/")
posts = response.json()

# Create post
new_post = {
    "title": "Python API Test",
    "content": "Testing the API using Python requests library.",
    "author": "Python Developer",
    "tags": "python, api, testing"
}
response = requests.post(f"{BASE_URL}/posts/", json=new_post)
created_post = response.json()

# Update post
updated_data = {
    "title": "Updated Python API Test",
    "content": "Updated content for the API test.",
    "author": "Python Developer",
    "tags": "python, api, testing, updated"
}
response = requests.put(f"{BASE_URL}/posts/{created_post['id']}/", json=updated_data)

# Delete post
response = requests.delete(f"{BASE_URL}/posts/{created_post['id']}/")
```

## Changelog

### Version 1.0.0 (Current)
- Initial API implementation
- Full CRUD operations for blog posts
- Input validation and sanitization
- Pagination support
- Error handling and logging
- Security features (CORS, XSS protection)

## Future Enhancements

### Planned Features
- User authentication and authorization
- Post categories and advanced filtering
- Full-text search capabilities
- File upload for images
- API versioning
- Rate limiting
- Caching layer
- Webhook support for integrations

### API Versioning Strategy
Future versions will use URL-based versioning:
- `/api/v1/posts/` (current)
- `/api/v2/posts/` (future)

Backward compatibility will be maintained for at least one major version.