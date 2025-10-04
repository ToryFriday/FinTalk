// Test utility functions for API error handling
// These functions are critical for proper error handling in the frontend

// Mock the axios import to avoid ES module issues
jest.mock('axios', () => ({
  create: jest.fn(() => ({
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() }
    }
  }))
}));

// Import the utility functions after mocking
const { handleApiError, formatErrorMessage } = require('./api');

describe('API Service Layer - Error Handling Utilities', () => {
  describe('BlogAPI Class Structure', () => {
    it('should export BlogAPI class with all required methods', () => {
      const BlogAPI = require('./api').default;
      expect(BlogAPI).toBeDefined();
      expect(typeof BlogAPI.getAllPosts).toBe('function');
      expect(typeof BlogAPI.getPost).toBe('function');
      expect(typeof BlogAPI.createPost).toBe('function');
      expect(typeof BlogAPI.updatePost).toBe('function');
      expect(typeof BlogAPI.deletePost).toBe('function');
      expect(typeof BlogAPI.patchPost).toBe('function');
    });
  });
});

describe('handleApiError', () => {
  it('should handle validation errors (400)', () => {
    const error = {
      response: {
        status: 400,
        data: { title: ['This field is required.'] }
      }
    };

    const result = handleApiError(error);

    expect(result).toEqual({
      type: 'VALIDATION_ERROR',
      message: 'Invalid data provided',
      details: { title: ['This field is required.'] },
      status: 400
    });
  });

  it('should handle not found errors (404)', () => {
    const error = {
      response: {
        status: 404,
        data: { detail: 'Not found' }
      }
    };

    const result = handleApiError(error);

    expect(result).toEqual({
      type: 'NOT_FOUND',
      message: 'Resource not found',
      details: { detail: 'Not found' },
      status: 404
    });
  });

  it('should handle server errors (500)', () => {
    const error = {
      response: {
        status: 500,
        data: { error: 'Internal server error' }
      }
    };

    const result = handleApiError(error);

    expect(result).toEqual({
      type: 'SERVER_ERROR',
      message: 'Internal server error occurred',
      details: { error: 'Internal server error' },
      status: 500
    });
  });

  it('should handle network errors', () => {
    const error = {
      request: {},
      message: 'Network Error'
    };

    const result = handleApiError(error);

    expect(result).toEqual({
      type: 'NETWORK_ERROR',
      message: 'Network error - please check your connection',
      details: null,
      status: null
    });
  });

  it('should handle unknown errors', () => {
    const error = {
      message: 'Something went wrong'
    };

    const result = handleApiError(error);

    expect(result).toEqual({
      type: 'UNKNOWN_ERROR',
      message: 'Something went wrong',
      details: null,
      status: null
    });
  });
});

describe('formatErrorMessage', () => {
  it('should format validation errors with field details', () => {
    const error = {
      type: 'VALIDATION_ERROR',
      message: 'Invalid data provided',
      details: {
        title: ['This field is required.'],
        content: ['This field may not be blank.', 'Ensure this field has at least 10 characters.']
      }
    };

    const result = formatErrorMessage(error);

    expect(result).toBe('title: This field is required., content: This field may not be blank., content: Ensure this field has at least 10 characters.');
  });

  it('should format validation errors with string details', () => {
    const error = {
      type: 'VALIDATION_ERROR',
      message: 'Invalid data provided',
      details: {
        title: 'This field is required.'
      }
    };

    const result = formatErrorMessage(error);

    expect(result).toBe('title: This field is required.');
  });

  it('should return original message for non-validation errors', () => {
    const error = {
      type: 'NOT_FOUND',
      message: 'Resource not found'
    };

    const result = formatErrorMessage(error);

    expect(result).toBe('Resource not found');
  });

  it('should return original message when validation error has no details', () => {
    const error = {
      type: 'VALIDATION_ERROR',
      message: 'Invalid data provided',
      details: null
    };

    const result = formatErrorMessage(error);

    expect(result).toBe('Invalid data provided');
  });
});