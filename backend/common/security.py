"""
Security utilities for input sanitization and validation.
"""

import re
import html
from django.utils.html import strip_tags
from django.core.exceptions import ValidationError


class InputSanitizer:
    """
    Utility class for sanitizing user input to prevent XSS and other attacks.
    """
    
    # Patterns for potentially dangerous content
    SCRIPT_PATTERN = re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL)
    JAVASCRIPT_PATTERN = re.compile(r'javascript:', re.IGNORECASE)
    ON_EVENT_PATTERN = re.compile(r'\bon\w+\s*=', re.IGNORECASE)
    
    @classmethod
    def sanitize_html_content(cls, content):
        """
        Sanitize HTML content by removing dangerous tags and attributes.
        
        Args:
            content (str): The content to sanitize
            
        Returns:
            str: Sanitized content
        """
        if not content:
            return content
        
        # Remove script tags
        content = cls.SCRIPT_PATTERN.sub('', content)
        
        # Remove javascript: URLs
        content = cls.JAVASCRIPT_PATTERN.sub('', content)
        
        # Remove on* event handlers
        content = cls.ON_EVENT_PATTERN.sub('', content)
        
        # HTML escape the content
        content = html.escape(content)
        
        return content
    
    @classmethod
    def sanitize_plain_text(cls, text):
        """
        Sanitize plain text by stripping HTML tags and escaping special characters.
        
        Args:
            text (str): The text to sanitize
            
        Returns:
            str: Sanitized text
        """
        if not text:
            return text
        
        # Strip HTML tags
        text = strip_tags(text)
        
        # HTML escape
        text = html.escape(text)
        
        return text.strip()
    
    @classmethod
    def validate_no_html(cls, value):
        """
        Validate that a value contains no HTML tags.
        
        Args:
            value (str): The value to validate
            
        Raises:
            ValidationError: If HTML tags are found
        """
        if not value:
            return
        
        if '<' in value and '>' in value:
            # Check if it looks like HTML
            if re.search(r'<[^>]+>', value):
                raise ValidationError("HTML tags are not allowed in this field.")
    
    @classmethod
    def validate_safe_url(cls, url):
        """
        Validate that a URL is safe (no javascript: or data: schemes).
        
        Args:
            url (str): The URL to validate
            
        Raises:
            ValidationError: If the URL is potentially dangerous
        """
        if not url:
            return
        
        url_lower = url.lower().strip()
        
        # Check for dangerous schemes
        dangerous_schemes = ['javascript:', 'data:', 'vbscript:', 'file:']
        for scheme in dangerous_schemes:
            if url_lower.startswith(scheme):
                raise ValidationError(f"URLs with '{scheme}' scheme are not allowed.")
    
    @classmethod
    def sanitize_filename(cls, filename):
        """
        Sanitize a filename by removing dangerous characters.
        
        Args:
            filename (str): The filename to sanitize
            
        Returns:
            str: Sanitized filename
        """
        if not filename:
            return filename
        
        # Remove path traversal attempts
        filename = filename.replace('..', '')
        filename = filename.replace('/', '')
        filename = filename.replace('\\', '')
        
        # Remove potentially dangerous characters
        filename = re.sub(r'[<>:"|?*]', '', filename)
        
        return filename.strip()


class SecurityValidator:
    """
    Additional security validation utilities.
    """
    
    @staticmethod
    def validate_content_length(content, max_length=10000):
        """
        Validate content length to prevent DoS attacks.
        
        Args:
            content (str): Content to validate
            max_length (int): Maximum allowed length
            
        Raises:
            ValidationError: If content is too long
        """
        if content and len(content) > max_length:
            raise ValidationError(f"Content exceeds maximum length of {max_length} characters.")
    
    @staticmethod
    def validate_no_sql_injection_patterns(value):
        """
        Basic validation to detect potential SQL injection patterns.
        
        Args:
            value (str): Value to validate
            
        Raises:
            ValidationError: If suspicious patterns are found
        """
        if not value:
            return
        
        # Common SQL injection patterns
        suspicious_patterns = [
            r'\bunion\s+select\b',
            r'\bselect\s+.*\bfrom\b',
            r'\binsert\s+into\b',
            r'\bdelete\s+from\b',
            r'\bdrop\s+table\b',
            r'\bupdate\s+.*\bset\b',
            r'--',
            r'/\*.*\*/',
            r'\bor\s+1\s*=\s*1\b',
            r'\band\s+1\s*=\s*1\b',
        ]
        
        value_lower = value.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, value_lower, re.IGNORECASE):
                raise ValidationError("Suspicious content detected. Please review your input.")
    
    @staticmethod
    def validate_rate_limit_safe(value):
        """
        Validate that input doesn't contain patterns that might bypass rate limiting.
        
        Args:
            value (str): Value to validate
            
        Raises:
            ValidationError: If suspicious patterns are found
        """
        if not value:
            return
        
        # Check for excessive repetition that might indicate automated input
        if len(set(value)) < len(value) * 0.1 and len(value) > 50:
            raise ValidationError("Input appears to be automated or repetitive.")
    
    @staticmethod
    def validate_file_upload(file):
        """
        Validate uploaded file for security issues.
        
        Args:
            file: Django UploadedFile instance
            
        Raises:
            ValidationError: If file is potentially dangerous
        """
        if not file:
            return
        
        # Check file size (basic check, more specific limits in serializers)
        max_size = 100 * 1024 * 1024  # 100MB absolute maximum
        if file.size > max_size:
            raise ValidationError(f"File size exceeds maximum allowed size of {max_size / (1024 * 1024):.0f}MB.")
        
        # Check for null bytes in filename (potential security issue)
        if '\x00' in file.name:
            raise ValidationError("Invalid filename detected.")
        
        # Sanitize filename
        file.name = InputSanitizer.sanitize_filename(file.name)
        
        # Basic content type validation
        if file.content_type:
            allowed_types = [
                'image/jpeg', 'image/png', 'image/gif', 'image/webp',
                'video/mp4', 'video/webm', 'video/ogg', 'video/quicktime', 'video/x-msvideo'
            ]
            if file.content_type not in allowed_types:
                raise ValidationError(f"File type '{file.content_type}' is not allowed.")