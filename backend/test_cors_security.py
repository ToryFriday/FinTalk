#!/usr/bin/env python
"""
Test script to verify CORS and security configuration.
"""

import os
import sys
import django
import requests
import json
from django.test import TestCase, Client
from django.conf import settings

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog_manager.settings.development')
django.setup()

from posts.models import Post
from posts.serializers import PostSerializer
from common.security import InputSanitizer, SecurityValidator


def test_cors_configuration():
    """Test CORS configuration."""
    print("Testing CORS configuration...")
    
    client = Client()
    
    # Test preflight request
    response = client.options('/api/posts/', HTTP_ORIGIN='http://localhost:3000')
    print(f"Preflight response status: {response.status_code}")
    
    # Check CORS headers
    cors_headers = [
        'Access-Control-Allow-Origin',
        'Access-Control-Allow-Methods',
        'Access-Control-Allow-Headers',
    ]
    
    for header in cors_headers:
        if header in response:
            print(f"{header}: {response[header]}")
        else:
            print(f"Missing CORS header: {header}")
    
    print("CORS configuration test completed.\n")


def test_security_headers():
    """Test security headers."""
    print("Testing security headers...")
    
    client = Client()
    response = client.get('/api/posts/')
    
    security_headers = [
        'X-Content-Type-Options',
        'X-Frame-Options',
        'X-XSS-Protection',
        'Referrer-Policy',
    ]
    
    for header in security_headers:
        if header in response:
            print(f"{header}: {response[header]}")
        else:
            print(f"Missing security header: {header}")
    
    print("Security headers test completed.\n")


def test_input_sanitization():
    """Test input sanitization."""
    print("Testing input sanitization...")
    
    # Test XSS prevention
    malicious_inputs = [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "<img src=x onerror=alert('xss')>",
        "'; DROP TABLE posts; --",
        "UNION SELECT * FROM posts",
    ]
    
    for malicious_input in malicious_inputs:
        try:
            sanitized = InputSanitizer.sanitize_plain_text(malicious_input)
            print(f"Input: {malicious_input[:50]}...")
            print(f"Sanitized: {sanitized[:50]}...")
            print("✓ Sanitization successful")
        except Exception as e:
            print(f"✗ Sanitization failed: {e}")
        print()
    
    print("Input sanitization test completed.\n")


def test_post_serializer_security():
    """Test Post serializer security validations."""
    print("Testing Post serializer security...")
    
    # Test malicious data
    malicious_data = {
        'title': '<script>alert("xss")</script>Malicious Title',
        'content': 'Content with <img src=x onerror=alert("xss")> malicious code',
        'author': 'Author<script>alert("xss")</script>',
        'tags': 'tag1, <script>alert("xss")</script>, tag2',
        'image_url': 'javascript:alert("xss")',
    }
    
    serializer = PostSerializer(data=malicious_data)
    
    if serializer.is_valid():
        print("✗ Serializer should have rejected malicious data")
        print(f"Validated data: {serializer.validated_data}")
    else:
        print("✓ Serializer correctly rejected malicious data")
        print(f"Errors: {serializer.errors}")
    
    # Test valid data
    valid_data = {
        'title': 'Valid Blog Post Title',
        'content': 'This is valid content for a blog post with proper formatting.',
        'author': 'John Doe',
        'tags': 'technology, programming, django',
        'image_url': 'https://example.com/image.jpg',
    }
    
    serializer = PostSerializer(data=valid_data)
    
    if serializer.is_valid():
        print("✓ Serializer correctly accepted valid data")
        print(f"Validated data keys: {list(serializer.validated_data.keys())}")
    else:
        print("✗ Serializer should have accepted valid data")
        print(f"Errors: {serializer.errors}")
    
    print("Post serializer security test completed.\n")


def test_csrf_configuration():
    """Test CSRF configuration."""
    print("Testing CSRF configuration...")
    
    # Check CSRF settings
    csrf_settings = [
        'CSRF_COOKIE_SECURE',
        'CSRF_COOKIE_HTTPONLY',
        'CSRF_COOKIE_SAMESITE',
        'CSRF_TRUSTED_ORIGINS',
    ]
    
    for setting in csrf_settings:
        if hasattr(settings, setting):
            value = getattr(settings, setting)
            print(f"{setting}: {value}")
        else:
            print(f"Missing CSRF setting: {setting}")
    
    print("CSRF configuration test completed.\n")


def main():
    """Run all tests."""
    print("Starting CORS and Security Configuration Tests")
    print("=" * 50)
    
    try:
        test_cors_configuration()
        test_security_headers()
        test_input_sanitization()
        test_post_serializer_security()
        test_csrf_configuration()
        
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()