# CORS and Security Configuration Guide

This document describes the CORS (Cross-Origin Resource Sharing) and security configuration implemented for the FinTalk  application.

## Overview

The application implements comprehensive security measures including:
- CORS configuration for cross-origin requests
- CSRF protection
- Input sanitization and validation
- Security headers
- Rate limiting
- Request logging and monitoring

## CORS Configuration

### Development Environment

**Allowed Origins:**
- `http://localhost:3000` (React development server)
- `http://127.0.0.1:3000`
- `http://0.0.0.0:3000`
- Additional origins from `CORS_ALLOWED_ORIGINS` environment variable

**Settings:**
- `CORS_ALLOW_CREDENTIALS = True` - Enables sending cookies for CSRF
- `CORS_ALLOW_ALL_ORIGINS = False` - Restricts to specific origins only
- Custom headers allowed: `Content-Type`, `Authorization`, `X-CSRFToken`, etc.

### Production Environment

**Configuration:**
- Origins must be explicitly configured via `CORS_ALLOWED_ORIGINS` environment variable
- Stricter security settings with HTTPS enforcement
- Enhanced rate limiting

## CSRF Protection

### Configuration
- `CSRF_COOKIE_HTTPONLY = True` - Prevents JavaScript access to CSRF cookie
- `CSRF_COOKIE_SAMESITE = 'Lax'` - Provides CSRF protection while allowing legitimate cross-site requests
- `CSRF_TRUSTED_ORIGINS` - List of trusted origins for CSRF validation

### Frontend Integration
- CSRF token automatically extracted from cookies
- Token included in `X-CSRFToken` header for non-GET requests
- `withCredentials: true` enabled in Axios configuration

## Security Headers

The following security headers are automatically added to all responses:

### Standard Headers
- `X-Content-Type-Options: nosniff` - Prevents MIME type sniffing
- `X-Frame-Options: DENY` - Prevents clickjacking attacks
- `X-XSS-Protection: 1; mode=block` - Enables XSS filtering
- `Referrer-Policy: strict-origin-when-cross-origin` - Controls referrer information

### Production-Only Headers
- `Strict-Transport-Security` - Enforces HTTPS connections
- `Content-Security-Policy` - Prevents code injection attacks
- `X-Cross-Origin-Opener-Policy: same-origin` - Isolates browsing contexts

## Input Sanitization

### Security Validators

**InputSanitizer Class:**
- `sanitize_html_content()` - Removes dangerous HTML tags and attributes
- `sanitize_plain_text()` - Strips HTML and escapes special characters
- `validate_no_html()` - Ensures no HTML tags in plain text fields
- `validate_safe_url()` - Prevents dangerous URL schemes (javascript:, data:, etc.)

**SecurityValidator Class:**
- `validate_content_length()` - Prevents DoS attacks via large content
- `validate_no_sql_injection_patterns()` - Detects potential SQL injection attempts
- `validate_rate_limit_safe()` - Identifies automated/repetitive input

### Applied to Post Model
All Post model fields are validated and sanitized:
- **Title**: HTML stripped, length validated, XSS prevention
- **Content**: HTML sanitized (safe tags allowed), length limited
- **Author**: Plain text only, no HTML allowed
- **Tags**: Plain text, comma-separated validation
- **Image URL**: URL scheme validation, dangerous schemes blocked

## Rate Limiting

### Development
- Anonymous users: 100 requests/hour
- Authenticated users: 1000 requests/hour

### Production
- Anonymous users: 50 requests/hour
- Authenticated users: 500 requests/hour

## Middleware Stack

The security middleware is applied in the following order:

1. `CorsMiddleware` - Handles CORS headers
2. `SecurityHeadersMiddleware` - Adds custom security headers
3. `SecurityMiddleware` - Django's built-in security middleware
4. `SessionMiddleware` - Session handling
5. `CommonMiddleware` - Common functionality
6. `CsrfViewMiddleware` - CSRF protection
7. `CSRFFailureLoggingMiddleware` - Logs CSRF failures
8. `AuthenticationMiddleware` - User authentication
9. `MessageMiddleware` - Django messages framework
10. `XFrameOptionsMiddleware` - X-Frame-Options header
11. `RequestLoggingMiddleware` - Security monitoring and logging

## Environment Variables

### Required for Production
```bash
# CORS Configuration
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Security Settings
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### Optional for Development
```bash
# Additional CORS origins
CORS_ALLOWED_ORIGINS=http://localhost:3001,http://localhost:3002
CSRF_TRUSTED_ORIGINS=http://localhost:3001,http://localhost:3002

# Security overrides
SECURE_SSL_REDIRECT=False
SECURE_HSTS_SECONDS=0
```

## Testing

### Automated Tests
Run the security test suite:
```bash
python test_cors_security.py
```

### Manual Testing
1. Open `frontend/public/cors-test.html` in a browser
2. Ensure backend is running on `http://localhost:8000`
3. Click "Run All Tests" to verify CORS and security configuration

### Frontend Integration Tests
```bash
cd frontend
npm test -- cors-security.test.js
```

## Security Monitoring

### Logging
All security-related events are logged:
- Suspicious request patterns
- CSRF failures
- Cross-origin requests
- Input validation failures

### Log Files
- `blog_manager.log` - General application logs
- `blog_manager_errors.log` - Error-specific logs
- `blog_manager_debug.log` - Debug logs (development only)

## Common Issues and Solutions

### CORS Errors
**Problem:** `Access to fetch at 'http://localhost:8000/api/posts/' from origin 'http://localhost:3000' has been blocked by CORS policy`

**Solution:**
1. Verify `CORS_ALLOWED_ORIGINS` includes the frontend origin
2. Check that `django-cors-headers` is installed and in `INSTALLED_APPS`
3. Ensure `CorsMiddleware` is first in the middleware stack

### CSRF Errors
**Problem:** `CSRF verification failed. Request aborted.`

**Solution:**
1. Verify CSRF token is included in requests
2. Check `CSRF_TRUSTED_ORIGINS` configuration
3. Ensure `withCredentials: true` in frontend requests

### Security Header Issues
**Problem:** Security headers not appearing in responses

**Solution:**
1. Verify `SecurityHeadersMiddleware` is in middleware stack
2. Check middleware order
3. Ensure settings are properly configured for the environment

## Best Practices

1. **Always use HTTPS in production** - Configure SSL/TLS properly
2. **Regularly update dependencies** - Keep security packages up to date
3. **Monitor logs** - Watch for suspicious patterns
4. **Test security configuration** - Use automated and manual tests
5. **Validate all input** - Never trust user input
6. **Use environment-specific settings** - Different security levels for dev/prod
7. **Implement proper error handling** - Don't expose sensitive information

## Security Checklist

- [ ] CORS origins properly configured
- [ ] CSRF protection enabled and tested
- [ ] Security headers present in responses
- [ ] Input sanitization working for all fields
- [ ] Rate limiting configured appropriately
- [ ] HTTPS enforced in production
- [ ] Security monitoring and logging active
- [ ] Environment variables properly set
- [ ] Dependencies up to date
- [ ] Security tests passing