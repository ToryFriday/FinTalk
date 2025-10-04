from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from posts.models import Post


class PostModelTestCase(TestCase):
    """
    Test cases for the Post model validation and constraints.
    """
    
    def setUp(self):
        """
        Set up test data for each test method.
        """
        self.valid_post_data = {
            'title': 'Test Blog Post Title',
            'content': 'This is a test blog post content that is long enough to pass validation.',
            'author': 'Test Author',
            'tags': 'django, python, testing',
            'image_url': 'https://example.com/image.jpg'
        }
    
    def test_create_valid_post(self):
        """
        Test creating a post with valid data.
        """
        post = Post.objects.create(**self.valid_post_data)
        
        self.assertEqual(post.title, self.valid_post_data['title'])
        self.assertEqual(post.content, self.valid_post_data['content'])
        self.assertEqual(post.author, self.valid_post_data['author'])
        self.assertEqual(post.tags, self.valid_post_data['tags'])
        self.assertEqual(post.image_url, self.valid_post_data['image_url'])
        self.assertIsNotNone(post.created_at)
        self.assertIsNotNone(post.updated_at)
        self.assertEqual(str(post), post.title)
    
    def test_create_post_minimal_data(self):
        """
        Test creating a post with only required fields.
        """
        minimal_data = {
            'title': 'Minimal Post',
            'content': 'This is minimal content for testing.',
            'author': 'Author'
        }
        post = Post.objects.create(**minimal_data)
        
        self.assertEqual(post.title, minimal_data['title'])
        self.assertEqual(post.content, minimal_data['content'])
        self.assertEqual(post.author, minimal_data['author'])
        self.assertEqual(post.tags, '')
        self.assertIsNone(post.image_url)
    
    def test_title_validation_too_short(self):
        """
        Test that title validation fails for titles that are too short.
        """
        invalid_data = self.valid_post_data.copy()
        invalid_data['title'] = 'Hi'  # Only 2 characters
        
        with self.assertRaises(ValidationError) as context:
            post = Post(**invalid_data)
            post.full_clean()
        
        self.assertIn('title', context.exception.error_dict)
        self.assertIn('Title must be at least 5 characters long', str(context.exception))
    
    def test_title_validation_too_long(self):
        """
        Test that title validation fails for titles that are too long.
        """
        invalid_data = self.valid_post_data.copy()
        invalid_data['title'] = 'A' * 201  # 201 characters
        
        with self.assertRaises(ValidationError) as context:
            post = Post(**invalid_data)
            post.full_clean()
        
        self.assertIn('title', context.exception.error_dict)
        self.assertIn('Title cannot exceed 200 characters', str(context.exception))
    
    def test_title_validation_empty(self):
        """
        Test that title validation fails for empty titles.
        """
        invalid_data = self.valid_post_data.copy()
        invalid_data['title'] = ''
        
        with self.assertRaises(ValidationError) as context:
            post = Post(**invalid_data)
            post.full_clean()
        
        self.assertIn('title', context.exception.error_dict)
        self.assertIn('Title is required', str(context.exception))
    
    def test_title_validation_whitespace_stripped(self):
        """
        Test that title whitespace is properly stripped.
        """
        data = self.valid_post_data.copy()
        data['title'] = '  Test Title  '
        
        post = Post(**data)
        post.full_clean()
        
        self.assertEqual(post.title, 'Test Title')
    
    def test_content_validation_too_short(self):
        """
        Test that content validation fails for content that is too short.
        """
        invalid_data = self.valid_post_data.copy()
        invalid_data['content'] = 'Short'  # Only 5 characters
        
        with self.assertRaises(ValidationError) as context:
            post = Post(**invalid_data)
            post.full_clean()
        
        self.assertIn('content', context.exception.error_dict)
        self.assertIn('Content must be at least 10 characters long', str(context.exception))
    
    def test_content_validation_empty(self):
        """
        Test that content validation fails for empty content.
        """
        invalid_data = self.valid_post_data.copy()
        invalid_data['content'] = ''
        
        with self.assertRaises(ValidationError) as context:
            post = Post(**invalid_data)
            post.full_clean()
        
        self.assertIn('content', context.exception.error_dict)
        self.assertIn('Content is required', str(context.exception))
    
    def test_content_validation_whitespace_stripped(self):
        """
        Test that content whitespace is properly stripped.
        """
        data = self.valid_post_data.copy()
        data['content'] = '  This is test content with whitespace.  '
        
        post = Post(**data)
        post.full_clean()
        
        self.assertEqual(post.content, 'This is test content with whitespace.')
    
    def test_author_validation_too_short(self):
        """
        Test that author validation fails for names that are too short.
        """
        invalid_data = self.valid_post_data.copy()
        invalid_data['author'] = 'A'  # Only 1 character
        
        with self.assertRaises(ValidationError) as context:
            post = Post(**invalid_data)
            post.full_clean()
        
        self.assertIn('author', context.exception.error_dict)
        self.assertIn('Author name must be at least 2 characters long', str(context.exception))
    
    def test_author_validation_too_long(self):
        """
        Test that author validation fails for names that are too long.
        """
        invalid_data = self.valid_post_data.copy()
        invalid_data['author'] = 'A' * 101  # 101 characters
        
        with self.assertRaises(ValidationError) as context:
            post = Post(**invalid_data)
            post.full_clean()
        
        self.assertIn('author', context.exception.error_dict)
        self.assertIn('Author name cannot exceed 100 characters', str(context.exception))
    
    def test_author_validation_empty(self):
        """
        Test that author validation fails for empty author.
        """
        invalid_data = self.valid_post_data.copy()
        invalid_data['author'] = ''
        
        with self.assertRaises(ValidationError) as context:
            post = Post(**invalid_data)
            post.full_clean()
        
        self.assertIn('author', context.exception.error_dict)
        self.assertIn('Author is required', str(context.exception))
    
    def test_author_validation_whitespace_stripped(self):
        """
        Test that author whitespace is properly stripped.
        """
        data = self.valid_post_data.copy()
        data['author'] = '  Test Author  '
        
        post = Post(**data)
        post.full_clean()
        
        self.assertEqual(post.author, 'Test Author')
    
    def test_tags_validation_too_long(self):
        """
        Test that tags validation fails for tags that are too long.
        """
        invalid_data = self.valid_post_data.copy()
        invalid_data['tags'] = 'A' * 501  # 501 characters
        
        with self.assertRaises(ValidationError) as context:
            post = Post(**invalid_data)
            post.full_clean()
        
        self.assertIn('tags', context.exception.error_dict)
        self.assertIn('Tags cannot exceed 500 characters', str(context.exception))
    
    def test_tags_validation_empty_allowed(self):
        """
        Test that empty tags are allowed.
        """
        data = self.valid_post_data.copy()
        data['tags'] = ''
        
        post = Post(**data)
        post.full_clean()  # Should not raise ValidationError
        
        self.assertEqual(post.tags, '')
    
    def test_tags_validation_whitespace_stripped(self):
        """
        Test that tags whitespace is properly stripped.
        """
        data = self.valid_post_data.copy()
        data['tags'] = '  django, python, testing  '
        
        post = Post(**data)
        post.full_clean()
        
        self.assertEqual(post.tags, 'django, python, testing')
    
    def test_get_tags_list_method(self):
        """
        Test the get_tags_list method returns proper list.
        """
        post = Post(**self.valid_post_data)
        tags_list = post.get_tags_list()
        
        expected_tags = ['django', 'python', 'testing']
        self.assertEqual(tags_list, expected_tags)
    
    def test_get_tags_list_empty(self):
        """
        Test the get_tags_list method with empty tags.
        """
        data = self.valid_post_data.copy()
        data['tags'] = ''
        post = Post(**data)
        
        tags_list = post.get_tags_list()
        self.assertEqual(tags_list, [])
    
    def test_set_tags_from_list_method(self):
        """
        Test the set_tags_from_list method.
        """
        post = Post(**self.valid_post_data)
        new_tags = ['react', 'javascript', 'frontend']
        post.set_tags_from_list(new_tags)
        
        self.assertEqual(post.tags, 'react, javascript, frontend')
    
    def test_set_tags_from_list_empty(self):
        """
        Test the set_tags_from_list method with empty list.
        """
        post = Post(**self.valid_post_data)
        post.set_tags_from_list([])
        
        self.assertEqual(post.tags, '')
    
    def test_model_ordering(self):
        """
        Test that posts are ordered by created_at descending.
        """
        # Create multiple posts
        post1 = Post.objects.create(
            title='First Post',
            content='First post content for testing.',
            author='Author 1'
        )
        post2 = Post.objects.create(
            title='Second Post',
            content='Second post content for testing.',
            author='Author 2'
        )
        
        posts = Post.objects.all()
        self.assertEqual(posts[0], post2)  # Most recent first
        self.assertEqual(posts[1], post1)
    
    def test_model_string_representation(self):
        """
        Test the __str__ method returns the title.
        """
        post = Post(**self.valid_post_data)
        self.assertEqual(str(post), self.valid_post_data['title'])
    
    def test_save_method_calls_validation(self):
        """
        Test that the save method calls full_clean for validation.
        """
        invalid_data = self.valid_post_data.copy()
        invalid_data['title'] = 'Hi'  # Too short
        
        with self.assertRaises(ValidationError):
            post = Post(**invalid_data)
            post.save()
    
    def test_database_constraints(self):
        """
        Test database-level constraints.
        """
        # Test that required fields cannot be null at database level
        with self.assertRaises((IntegrityError, ValidationError)):
            Post.objects.create(
                title=None,
                content='Test content',
                author='Test Author'
            )
    
    def test_image_url_optional(self):
        """
        Test that image_url is optional and can be None.
        """
        data = self.valid_post_data.copy()
        data['image_url'] = None
        
        post = Post.objects.create(**data)
        self.assertIsNone(post.image_url)
    
    def test_timestamps_auto_populated(self):
        """
        Test that created_at and updated_at are automatically populated.
        """
        post = Post.objects.create(**self.valid_post_data)
        
        self.assertIsNotNone(post.created_at)
        self.assertIsNotNone(post.updated_at)
        
        # Test that updated_at changes on save
        original_updated_at = post.updated_at
        post.title = 'Updated Title'
        post.save()
        
        self.assertNotEqual(post.updated_at, original_updated_at)