import pytest
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from posts.serializers import PostSerializer
from posts.models import Post


class PostSerializerTestCase(TestCase):
    """
    Test cases for PostSerializer validation and functionality.
    """
    
    def setUp(self):
        """
        Set up test data for serializer tests.
        """
        self.valid_post_data = {
            'title': 'Test Blog Post Title',
            'content': 'This is a test blog post content that is long enough to pass validation.',
            'author': 'Test Author',
            'tags': 'python, django, testing',
            'image_url': 'https://example.com/image.jpg'
        }
        
        self.minimal_valid_data = {
            'title': 'Valid Title',
            'content': 'Valid content that meets minimum length requirements.',
            'author': 'Author'
        }
    
    def test_serializer_with_valid_data(self):
        """
        Test serializer with completely valid data.
        """
        serializer = PostSerializer(data=self.valid_post_data)
        self.assertTrue(serializer.is_valid())
        
        post = serializer.save()
        self.assertIsInstance(post, Post)
        self.assertEqual(post.title, self.valid_post_data['title'])
        self.assertEqual(post.content, self.valid_post_data['content'])
        self.assertEqual(post.author, self.valid_post_data['author'])
        self.assertEqual(post.tags, self.valid_post_data['tags'])
        self.assertEqual(post.image_url, self.valid_post_data['image_url'])
    
    def test_serializer_with_minimal_valid_data(self):
        """
        Test serializer with minimal required fields only.
        """
        serializer = PostSerializer(data=self.minimal_valid_data)
        self.assertTrue(serializer.is_valid())
        
        post = serializer.save()
        self.assertIsInstance(post, Post)
        self.assertEqual(post.title, self.minimal_valid_data['title'])
        self.assertEqual(post.content, self.minimal_valid_data['content'])
        self.assertEqual(post.author, self.minimal_valid_data['author'])
        self.assertEqual(post.tags, '')  # Default empty string
        self.assertIsNone(post.image_url)  # Default None
    
    def test_title_validation_required(self):
        """
        Test that title field is required.
        """
        data = self.valid_post_data.copy()
        del data['title']
        
        serializer = PostSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)
        self.assertEqual(serializer.errors['title'][0], 'Title is required.')
    
    def test_title_validation_empty_string(self):
        """
        Test title validation with empty string.
        """
        data = self.valid_post_data.copy()
        data['title'] = ''
        
        serializer = PostSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)
        self.assertEqual(serializer.errors['title'][0], 'Title must be at least 5 characters long.')
    
    def test_title_validation_whitespace_only(self):
        """
        Test title validation with whitespace only.
        """
        data = self.valid_post_data.copy()
        data['title'] = '   '
        
        serializer = PostSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)
        self.assertEqual(serializer.errors['title'][0], 'Title must be at least 5 characters long.')
    
    def test_title_validation_too_short(self):
        """
        Test title validation with too short title.
        """
        data = self.valid_post_data.copy()
        data['title'] = 'Hi'
        
        serializer = PostSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)
        self.assertEqual(serializer.errors['title'][0], 'Title must be at least 5 characters long.')
    
    def test_title_validation_too_long(self):
        """
        Test title validation with too long title.
        """
        data = self.valid_post_data.copy()
        data['title'] = 'A' * 201  # 201 characters
        
        serializer = PostSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)
        self.assertEqual(serializer.errors['title'][0], 'Title cannot exceed 200 characters.')
    
    def test_title_validation_strips_whitespace(self):
        """
        Test that title validation strips leading/trailing whitespace.
        """
        data = self.valid_post_data.copy()
        data['title'] = '  Valid Title  '
        
        serializer = PostSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        post = serializer.save()
        self.assertEqual(post.title, 'Valid Title')
    
    def test_content_validation_required(self):
        """
        Test that content field is required.
        """
        data = self.valid_post_data.copy()
        del data['content']
        
        serializer = PostSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('content', serializer.errors)
        self.assertEqual(serializer.errors['content'][0], 'Content is required.')
    
    def test_content_validation_empty_string(self):
        """
        Test content validation with empty string.
        """
        data = self.valid_post_data.copy()
        data['content'] = ''
        
        serializer = PostSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('content', serializer.errors)
        self.assertEqual(serializer.errors['content'][0], 'Content must be at least 10 characters long.')
    
    def test_content_validation_too_short(self):
        """
        Test content validation with too short content.
        """
        data = self.valid_post_data.copy()
        data['content'] = 'Short'
        
        serializer = PostSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('content', serializer.errors)
        self.assertEqual(serializer.errors['content'][0], 'Content must be at least 10 characters long.')
    
    def test_content_validation_strips_whitespace(self):
        """
        Test that content validation strips leading/trailing whitespace.
        """
        data = self.valid_post_data.copy()
        data['content'] = '  Valid content that meets minimum requirements.  '
        
        serializer = PostSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        post = serializer.save()
        self.assertEqual(post.content, 'Valid content that meets minimum requirements.')
    
    def test_author_validation_required(self):
        """
        Test that author field is required.
        """
        data = self.valid_post_data.copy()
        del data['author']
        
        serializer = PostSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('author', serializer.errors)
        self.assertEqual(serializer.errors['author'][0], 'Author is required.')
    
    def test_author_validation_empty_string(self):
        """
        Test author validation with empty string.
        """
        data = self.valid_post_data.copy()
        data['author'] = ''
        
        serializer = PostSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('author', serializer.errors)
        self.assertEqual(serializer.errors['author'][0], 'Author name must be at least 2 characters long.')
    
    def test_author_validation_too_short(self):
        """
        Test author validation with too short name.
        """
        data = self.valid_post_data.copy()
        data['author'] = 'A'
        
        serializer = PostSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('author', serializer.errors)
        self.assertEqual(serializer.errors['author'][0], 'Author name must be at least 2 characters long.')
    
    def test_author_validation_too_long(self):
        """
        Test author validation with too long name.
        """
        data = self.valid_post_data.copy()
        data['author'] = 'A' * 101  # 101 characters
        
        serializer = PostSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('author', serializer.errors)
        self.assertEqual(serializer.errors['author'][0], 'Author name cannot exceed 100 characters.')
    
    def test_author_validation_strips_whitespace(self):
        """
        Test that author validation strips leading/trailing whitespace.
        """
        data = self.valid_post_data.copy()
        data['author'] = '  Test Author  '
        
        serializer = PostSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        post = serializer.save()
        self.assertEqual(post.author, 'Test Author')
    
    def test_tags_validation_optional(self):
        """
        Test that tags field is optional.
        """
        data = self.valid_post_data.copy()
        del data['tags']
        
        serializer = PostSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        post = serializer.save()
        self.assertEqual(post.tags, '')
    
    def test_tags_validation_empty_string(self):
        """
        Test tags validation with empty string.
        """
        data = self.valid_post_data.copy()
        data['tags'] = ''
        
        serializer = PostSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        post = serializer.save()
        self.assertEqual(post.tags, '')
    
    def test_tags_validation_too_long(self):
        """
        Test tags validation with too long tags.
        """
        data = self.valid_post_data.copy()
        data['tags'] = 'A' * 501  # 501 characters
        
        serializer = PostSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('tags', serializer.errors)
        self.assertEqual(serializer.errors['tags'][0], 'Tags cannot exceed 500 characters.')
    
    def test_tags_validation_strips_whitespace(self):
        """
        Test that tags validation strips leading/trailing whitespace.
        """
        data = self.valid_post_data.copy()
        data['tags'] = '  python, django  '
        
        serializer = PostSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        post = serializer.save()
        self.assertEqual(post.tags, 'python, django')
    
    def test_image_url_validation_optional(self):
        """
        Test that image_url field is optional.
        """
        data = self.valid_post_data.copy()
        del data['image_url']
        
        serializer = PostSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        post = serializer.save()
        self.assertIsNone(post.image_url)
    
    def test_image_url_validation_empty_string(self):
        """
        Test image_url validation with empty string.
        """
        data = self.valid_post_data.copy()
        data['image_url'] = ''
        
        serializer = PostSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        post = serializer.save()
        self.assertEqual(post.image_url, '')
    
    def test_image_url_validation_invalid_url(self):
        """
        Test image_url validation with invalid URL.
        """
        data = self.valid_post_data.copy()
        data['image_url'] = 'not-a-valid-url'
        
        serializer = PostSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('image_url', serializer.errors)
    
    def test_object_level_validation_title_content_identical(self):
        """
        Test object-level validation when title and content are identical.
        """
        data = self.valid_post_data.copy()
        data['title'] = 'Same Content'
        data['content'] = 'Same Content'
        
        serializer = PostSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('content', serializer.errors)
        self.assertEqual(serializer.errors['content'][0], 'Content cannot be identical to the title.')
    
    def test_multiple_validation_errors(self):
        """
        Test that multiple validation errors are returned.
        """
        data = {
            'title': 'Hi',  # Too short
            'content': 'Short',  # Too short
            'author': 'A',  # Too short
            'tags': 'A' * 501,  # Too long
            'image_url': 'invalid-url'  # Invalid URL
        }
        
        serializer = PostSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        
        # Check that all fields have validation errors
        self.assertIn('title', serializer.errors)
        self.assertIn('content', serializer.errors)
        self.assertIn('author', serializer.errors)
        self.assertIn('tags', serializer.errors)
        self.assertIn('image_url', serializer.errors)
    
    def test_serializer_update_existing_post(self):
        """
        Test updating an existing post through the serializer.
        """
        # Create a post first
        post = Post.objects.create(**self.valid_post_data)
        
        # Update data
        update_data = {
            'title': 'Updated Title',
            'content': 'Updated content that meets all validation requirements.',
            'author': 'Updated Author'
        }
        
        serializer = PostSerializer(post, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_post = serializer.save()
        self.assertEqual(updated_post.title, update_data['title'])
        self.assertEqual(updated_post.content, update_data['content'])
        self.assertEqual(updated_post.author, update_data['author'])
        # Tags and image_url should remain unchanged
        self.assertEqual(updated_post.tags, self.valid_post_data['tags'])
        self.assertEqual(updated_post.image_url, self.valid_post_data['image_url'])
    
    def test_serializer_representation_includes_tags_list(self):
        """
        Test that serializer representation includes tags_list field.
        """
        post = Post.objects.create(**self.valid_post_data)
        serializer = PostSerializer(post)
        
        data = serializer.data
        self.assertIn('tags_list', data)
        self.assertEqual(data['tags_list'], ['python', 'django', 'testing'])
    
    def test_serializer_representation_empty_tags_list(self):
        """
        Test that serializer representation handles empty tags correctly.
        """
        data = self.minimal_valid_data.copy()
        post = Post.objects.create(**data)
        serializer = PostSerializer(post)
        
        serialized_data = serializer.data
        self.assertIn('tags_list', serialized_data)
        self.assertEqual(serialized_data['tags_list'], [])
    
    def test_read_only_fields(self):
        """
        Test that read-only fields cannot be set during creation/update.
        """
        data = self.valid_post_data.copy()
        data['id'] = 999
        data['created_at'] = '2023-01-01T00:00:00Z'
        data['updated_at'] = '2023-01-01T00:00:00Z'
        
        serializer = PostSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        post = serializer.save()
        # ID should be auto-generated, not 999
        self.assertNotEqual(post.id, 999)
        # Timestamps should be auto-generated, not the provided values
        self.assertIsNotNone(post.created_at)
        self.assertIsNotNone(post.updated_at)