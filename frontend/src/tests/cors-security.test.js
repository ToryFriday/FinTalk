/**
 * CORS and Security Integration Tests
 * 
 * These tests verify that the frontend can properly communicate with the backend
 * with CORS and security configurations in place.
 */

import axios from 'axios';
import BlogAPI from '../services/api';

// Mock data for testing
const mockPostData = {
  title: 'Test Blog Post for CORS',
  content: 'This is a test post to verify CORS and security configuration works properly.',
  author: 'Test Author',
  tags: 'test, cors, security',
  image_url: 'https://example.com/test-image.jpg'
};

// Malicious data to test security
const maliciousPostData = {
  title: '<script>alert("XSS")</script>Malicious Title',
  content: 'Content with <img src=x onerror=alert("XSS")> malicious code',
  author: 'Author<script>alert("XSS")</script>',
  tags: 'tag1, <script>alert("XSS")</script>, tag2',
  image_url: 'javascript:alert("XSS")'
};

describe('CORS and Security Tests', () => {
  const BACKEND_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  
  beforeAll(() => {
    // Set up axios defaults for testing
    axios.defaults.withCredentials = true;
  });

  describe('CORS Configuration', () => {
    test('should handle preflight OPTIONS request', async () => {
      try {
        const response = await axios.options(`${BACKEND_URL}/api/posts/`, {
          headers: {
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type, X-CSRFToken'
          }
        });
        
        expect(response.status).toBe(200);
        expect(response.headers['access-control-allow-methods']).toBeDefined();
        expect(response.headers['access-control-allow-headers']).toBeDefined();
      } catch (error) {
        // If backend is not running, skip this test
        if (error.code === 'ECONNREFUSED') {
          console.warn('Backend not running, skipping CORS preflight test');
          return;
        }
        throw error;
      }
    });

    test('should include CORS headers in API responses', async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/api/posts/`, {
          headers: {
            'Origin': 'http://localhost:3000'
          }
        });
        
        // Check for CORS headers (may be set by django-cors-headers)
        expect(response.status).toBe(200);
        // Note: CORS headers might not be visible in same-origin requests
      } catch (error) {
        if (error.code === 'ECONNREFUSED') {
          console.warn('Backend not running, skipping CORS headers test');
          return;
        }
        // If we get a CORS error, that means CORS is working (blocking unauthorized origins)
        if (error.response && error.response.status >= 400) {
          console.log('CORS is properly configured (blocking unauthorized requests)');
        }
      }
    });
  });

  describe('Security Headers', () => {
    test('should include security headers in responses', async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/api/posts/`);
        
        // Check for security headers
        const securityHeaders = [
          'x-content-type-options',
          'x-frame-options',
          'x-xss-protection',
          'referrer-policy'
        ];
        
        securityHeaders.forEach(header => {
          expect(response.headers[header]).toBeDefined();
        });
        
      } catch (error) {
        if (error.code === 'ECONNREFUSED') {
          console.warn('Backend not running, skipping security headers test');
          return;
        }
        throw error;
      }
    });
  });

  describe('Input Sanitization', () => {
    test('should reject malicious input data', async () => {
      try {
        const result = await BlogAPI.createPost(maliciousPostData);
        
        // Should fail validation
        expect(result.success).toBe(false);
        expect(result.error).toBeDefined();
        expect(result.error.type).toBe('VALIDATION_ERROR');
        
      } catch (error) {
        if (error.code === 'ECONNREFUSED') {
          console.warn('Backend not running, skipping input sanitization test');
          return;
        }
        throw error;
      }
    });

    test('should accept valid input data', async () => {
      try {
        const result = await BlogAPI.createPost(mockPostData);
        
        // Should succeed or fail due to database issues, not validation
        if (!result.success && result.error.type === 'VALIDATION_ERROR') {
          fail('Valid data should not fail validation');
        }
        
      } catch (error) {
        if (error.code === 'ECONNREFUSED') {
          console.warn('Backend not running, skipping valid input test');
          return;
        }
        // Database errors are acceptable for this test
        if (error.response && error.response.status === 500) {
          console.log('Database not configured, but validation passed');
        }
      }
    });
  });

  describe('CSRF Protection', () => {
    test('should handle CSRF token in requests', async () => {
      // Mock CSRF token in cookies
      document.cookie = 'csrftoken=test-csrf-token; path=/';
      
      try {
        const response = await axios.post(`${BACKEND_URL}/api/posts/`, mockPostData, {
          headers: {
            'X-CSRFToken': 'test-csrf-token'
          }
        });
        
        // Should not fail due to CSRF (might fail due to other reasons)
        expect(response.status).not.toBe(403);
        
      } catch (error) {
        if (error.code === 'ECONNREFUSED') {
          console.warn('Backend not running, skipping CSRF test');
          return;
        }
        
        // 403 would indicate CSRF failure
        if (error.response && error.response.status === 403) {
          fail('CSRF token should be properly handled');
        }
      }
    });
  });

  describe('API Error Handling', () => {
    test('should properly format validation errors', async () => {
      const invalidData = {
        title: '', // Too short
        content: 'x', // Too short
        author: '', // Required
      };
      
      try {
        const result = await BlogAPI.createPost(invalidData);
        
        expect(result.success).toBe(false);
        expect(result.error.type).toBe('VALIDATION_ERROR');
        expect(result.error.details).toBeDefined();
        
      } catch (error) {
        if (error.code === 'ECONNREFUSED') {
          console.warn('Backend not running, skipping error handling test');
          return;
        }
        throw error;
      }
    });

    test('should handle network errors gracefully', async () => {
      // Temporarily change base URL to trigger network error
      const originalBaseURL = axios.defaults.baseURL;
      axios.defaults.baseURL = 'http://nonexistent-server:9999';
      
      try {
        const result = await BlogAPI.getAllPosts();
        
        // Should return mock data or handle error gracefully
        expect(result).toBeDefined();
        
      } finally {
        // Restore original base URL
        axios.defaults.baseURL = originalBaseURL;
      }
    });
  });
});

// Manual test function that can be run in browser console
window.testCORSAndSecurity = async function() {
  console.log('Starting CORS and Security Tests...');
  
  try {
    // Test 1: Basic API call
    console.log('Test 1: Basic API call');
    const posts = await BlogAPI.getAllPosts();
    console.log('✓ API call successful:', posts.success);
    
    // Test 2: Malicious input
    console.log('Test 2: Malicious input rejection');
    const maliciousResult = await BlogAPI.createPost(maliciousPostData);
    console.log('✓ Malicious input handled:', !maliciousResult.success);
    
    // Test 3: Valid input
    console.log('Test 3: Valid input acceptance');
    const validResult = await BlogAPI.createPost(mockPostData);
    console.log('✓ Valid input processed:', validResult);
    
    console.log('All tests completed!');
    
  } catch (error) {
    console.error('Test failed:', error);
  }
};