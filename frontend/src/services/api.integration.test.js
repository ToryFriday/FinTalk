// Integration tests for BlogAPI
// These tests require the backend server to be running
// Run with: npm test -- --testPathPattern=api.integration.test.js --watchAll=false

import BlogAPI from './api';

// Skip these tests by default since they require backend
const runIntegrationTests = process.env.RUN_INTEGRATION_TESTS === 'true';

describe.skip('BlogAPI Integration Tests', () => {
  // Only run if explicitly enabled
  if (!runIntegrationTests) {
    return;
  }

  let createdPostId;

  describe('CRUD Operations', () => {
    it('should create a new post', async () => {
      const postData = {
        title: 'Integration Test Post',
        content: 'This is a test post created during integration testing.',
        author: 'Test Author',
        tags: 'test,integration'
      };

      const result = await BlogAPI.createPost(postData);
      
      expect(result.success).toBe(true);
      expect(result.data).toHaveProperty('id');
      expect(result.data.title).toBe(postData.title);
      expect(result.status).toBe(201);
      
      createdPostId = result.data.id;
    });

    it('should fetch all posts', async () => {
      const result = await BlogAPI.getAllPosts();
      
      expect(result.success).toBe(true);
      expect(Array.isArray(result.data)).toBe(true);
      expect(result.status).toBe(200);
    });

    it('should fetch a single post', async () => {
      if (!createdPostId) {
        throw new Error('No post created to fetch');
      }

      const result = await BlogAPI.getPost(createdPostId);
      
      expect(result.success).toBe(true);
      expect(result.data).toHaveProperty('id', createdPostId);
      expect(result.status).toBe(200);
    });

    it('should update a post', async () => {
      if (!createdPostId) {
        throw new Error('No post created to update');
      }

      const updateData = {
        title: 'Updated Integration Test Post',
        content: 'This post has been updated during integration testing.',
        author: 'Updated Test Author',
        tags: 'test,integration,updated'
      };

      const result = await BlogAPI.updatePost(createdPostId, updateData);
      
      expect(result.success).toBe(true);
      expect(result.data.title).toBe(updateData.title);
      expect(result.status).toBe(200);
    });

    it('should partially update a post', async () => {
      if (!createdPostId) {
        throw new Error('No post created to patch');
      }

      const patchData = {
        title: 'Patched Integration Test Post'
      };

      const result = await BlogAPI.patchPost(createdPostId, patchData);
      
      expect(result.success).toBe(true);
      expect(result.data.title).toBe(patchData.title);
      expect(result.status).toBe(200);
    });

    it('should delete a post', async () => {
      if (!createdPostId) {
        throw new Error('No post created to delete');
      }

      const result = await BlogAPI.deletePost(createdPostId);
      
      expect(result.success).toBe(true);
      expect(result.status).toBe(204);
    });
  });

  describe('Error Handling', () => {
    it('should handle 404 when fetching non-existent post', async () => {
      const result = await BlogAPI.getPost(99999);
      
      expect(result.success).toBe(false);
      expect(result.error.type).toBe('NOT_FOUND');
      expect(result.status).toBe(404);
    });

    it('should handle validation errors when creating invalid post', async () => {
      const invalidData = {
        title: '', // Empty title should cause validation error
        content: 'Test content'
        // Missing required author field
      };

      const result = await BlogAPI.createPost(invalidData);
      
      expect(result.success).toBe(false);
      expect(result.error.type).toBe('VALIDATION_ERROR');
      expect(result.status).toBe(400);
    });
  });
});

// Instructions for running integration tests:
console.log(`
To run integration tests:
1. Start the backend server (python manage.py runserver)
2. Set environment variable: RUN_INTEGRATION_TESTS=true
3. Run: npm test -- --testPathPattern=api.integration.test.js --watchAll=false
`);