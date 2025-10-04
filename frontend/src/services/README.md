# API Service Layer

This directory contains the frontend API service layer for the Blog Post Manager application.

## Files

- `api.js` - Main BlogAPI class with CRUD operations
- `apiConfig.js` - Configuration constants and utilities
- `api.test.js` - Unit tests for error handling utilities
- `api.integration.test.js` - Integration tests (requires backend)

## Usage

### Basic CRUD Operations

```javascript
import BlogAPI from './services/api';

// Get all posts
const result = await BlogAPI.getAllPosts();
if (result.success) {
  console.log('Posts:', result.data);
} else {
  console.error('Error:', result.error);
}

// Get single post
const post = await BlogAPI.getPost(1);

// Create new post
const newPost = await BlogAPI.createPost({
  title: 'My Post',
  content: 'Post content',
  author: 'Author Name',
  tags: 'tag1,tag2'
});

// Update post
const updated = await BlogAPI.updatePost(1, {
  title: 'Updated Title',
  content: 'Updated content',
  author: 'Author Name'
});

// Delete post
const deleted = await BlogAPI.deletePost(1);
```

### Error Handling

```javascript
import BlogAPI, { formatErrorMessage } from './services/api';

const result = await BlogAPI.createPost(invalidData);
if (!result.success) {
  const errorMessage = formatErrorMessage(result.error);
  console.error('Validation failed:', errorMessage);
}
```

### Configuration

The API service uses environment variables for configuration:

- `REACT_APP_API_URL` - Backend API base URL (default: http://localhost:8000)

## Response Format

All API methods return a consistent response format:

```javascript
// Success response
{
  success: true,
  data: {...}, // Response data
  status: 200  // HTTP status code
}

// Error response
{
  success: false,
  error: {
    type: 'VALIDATION_ERROR',
    message: 'Invalid data provided',
    details: {...},
    status: 400
  },
  status: 400
}
```

## Error Types

- `VALIDATION_ERROR` - 400 Bad Request with validation details
- `NOT_FOUND` - 404 Resource not found
- `SERVER_ERROR` - 500 Internal server error
- `NETWORK_ERROR` - Network connectivity issues
- `API_ERROR` - Other HTTP errors
- `UNKNOWN_ERROR` - Unexpected errors

## Testing

Run unit tests:
```bash
npm test -- --testPathPattern=api.test.js --watchAll=false
```

Run integration tests (requires backend):
```bash
RUN_INTEGRATION_TESTS=true npm test -- --testPathPattern=api.integration.test.js --watchAll=false
```

## Features

- ✅ Axios HTTP client with interceptors
- ✅ Consistent error handling
- ✅ Request/response logging
- ✅ Configurable base URL and timeout
- ✅ Comprehensive error types and formatting
- ✅ Unit tests for error handling utilities
- ✅ Integration tests for full CRUD operations
- ✅ TypeScript-ready with JSDoc comments