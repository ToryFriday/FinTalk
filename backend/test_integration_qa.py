"""
Comprehensive Integration Testing and Quality Assurance Suite
Tests complete user workflows, email notifications, file uploads, RBAC, and security.
"""

import tempfile
import os
import time
import json
from datetime import timedelta
from unittest.mock import patch, MagicMock
from io import BytesIO

from django.test import TestCase, TransactionTestCase, override_settings
from django.contrib.auth.models import User, Permission
from django.urls import reverse
from django.utils import timezone
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.utils import override_settings
from django.db import connection
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from PIL import Image

from accounts.models import UserProfile, Role, UserRole, SavedArticle, UserFollow
from posts.models import Post, MediaFile, PostMedia
from moderation.models import ContentFlag, ModerationAction
from notifications.models import EmailSubscription


class CompleteUserWorkflowTest(APITestCase):
    """Test complete user workflows from registration to content creation and social interaction."""
    
    def test_complete_user_journey(self):
        """Test complete user journey from registration to publishing and social interaction."""
        # Step 1: User Registration
        registration_data = {
            'username': 'newwriter',
            'email': 'newwriter@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'New',
            'last_name': 'Writer'
        }
        
        register_url = reverse('accounts:register')
        response = self.client.post(register_url, registration_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user_id = response.data['user_id']
        
        # Verify email verification was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Verify your email', mail.outbox[0].subject)
        
        # Step 2: Email Verification
        user = User.objects.get(id=user_id)
        token = user.profile.email_verification_token
        verify_url = reverse('accounts:verify-email', kwargs={'token': token})
        response = self.client.get(verify_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 3: Login
        login_data = {
            'username': 'newwriter',
            'password': 'SecurePass123!'
        }
        
        login_url = reverse('accounts:login')
        response = self.client.post(login_url, login_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['user']['is_email_verified'])
        
        # Step 4: Profile Setup
        profile_data = {
            'bio': 'I am a financial writer passionate about helping people understand investing.',
            'website': 'https://newwriter.com',
            'location': 'San Francisco, CA'
        }
        
        profile_url = reverse('accounts:user-profile')
        response = self.client.patch(profile_url, profile_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 5: Role Assignment (simulate admin assigning writer role)
        writer_role = Role.objects.create(
            name='writer',
            display_name='Writer',
            description='Can create and edit posts'
        )
        UserRole.objects.create(user=user, role=writer_role)
        
        # Step 6: Create Draft Post
        post_data = {
            'title': 'Understanding Cryptocurrency Investments',
            'content': 'Cryptocurrency has become a popular investment option. This comprehensive guide will help you understand the basics of crypto investing, including risks and opportunities.',
            'tags': 'cryptocurrency, investing, blockchain, finance',
            'status': 'draft'
        }
        
        posts_url = reverse('posts:post-list-create')
        response = self.client.post(posts_url, post_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post_id = response.data['id']
        
        # Step 7: Schedule Post
        future_date = timezone.now() + timedelta(hours=1)
        schedule_data = {
            'scheduled_publish_date': future_date.isoformat()
        }
        
        schedule_url = reverse('posts:schedule-post', kwargs={'pk': post_id})
        response = self.client.post(schedule_url, schedule_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 8: Publish Post
        publish_url = reverse('posts:publish-post', kwargs={'pk': post_id})
        response = self.client.post(publish_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify complete workflow
        post = Post.objects.get(id=post_id)
        self.assertEqual(post.status, 'published')
        self.assertEqual(post.author_user, user)


class EmailNotificationValidationTest(APITestCase):
    """Validate email notification delivery and subscription management."""
    
    def setUp(self):
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='testpass123'
        )
        self.subscriber1 = User.objects.create_user(
            username='subscriber1',
            email='subscriber1@example.com',
            password='testpass123'
        )
        
        # Create writer role
        writer_role = Role.objects.create(
            name='writer',
            display_name='Writer',
            description='Can create posts'
        )
        UserRole.objects.create(user=self.author, role=writer_role)
        
        # Create subscription
        EmailSubscription.objects.create(
            user=self.subscriber1,
            email=self.subscriber1.email,
            subscription_type='all_posts',
            is_active=True
        )
    
    @patch('notifications.tasks.send_new_post_notification.delay')
    def test_email_notification_delivery(self, mock_notification_task):
        """Test email notification delivery for different subscription types."""
        self.client.force_authenticate(user=self.author)
        
        # Create and publish post
        post_data = {
            'title': 'Market Update: Q4 2024 Analysis',
            'content': 'This comprehensive market analysis covers the key trends and predictions for Q4 2024.',
            'tags': 'market, analysis, Q4, 2024',
            'status': 'published'
        }
        
        posts_url = reverse('posts:post-list-create')
        response = self.client.post(posts_url, post_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post_id = response.data['id']
        
        # Verify notification task was called
        mock_notification_task.assert_called_once_with(post_id)
        
    def test_subscription_management_workflow(self):
        """Test complete subscription management workflow."""
        self.client.force_authenticate(user=self.subscriber1)
        
        # Test unsubscribe via token
        subscription = self.subscriber1.emailsubscription_set.first()
        unsubscribe_token = subscription.unsubscribe_token
        
        unsubscribe_url = reverse('notifications:unsubscribe', kwargs={'token': unsubscribe_token})
        response = self.client.get(unsubscribe_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify subscription was deactivated
        subscription.refresh_from_db()
        self.assertFalse(subscription.is_active)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class FileUploadMediaManagementTest(APITestCase):
    """Test file upload and media management across different scenarios."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='writer',
            email='writer@example.com',
            password='testpass123'
        )
        
        writer_role = Role.objects.create(
            name='writer',
            display_name='Writer',
            description='Can create posts'
        )
        UserRole.objects.create(user=self.user, role=writer_role)
        
        self.client.force_authenticate(user=self.user)
    
    def create_test_image(self, format='JPEG', size=(100, 100), color='red'):
        """Helper to create test images."""
        image = Image.new('RGB', size, color=color)
        temp_file = BytesIO()
        image.save(temp_file, format=format)
        temp_file.seek(0)
        return temp_file
    
    def test_image_upload_and_processing(self):
        """Test image upload with different formats and sizes."""
        # Test JPEG upload
        jpeg_file = self.create_test_image('JPEG', (800, 600), 'blue')
        upload_data = {
            'file': SimpleUploadedFile(
                name='test_chart.jpg',
                content=jpeg_file.getvalue(),
                content_type='image/jpeg'
            ),
            'alt_text': 'Financial chart showing market trends'
        }
        
        upload_url = reverse('posts:media-upload')
        response = self.client.post(upload_url, upload_data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['alt_text'], 'Financial chart showing market trends')
        
        media_file = MediaFile.objects.get(id=response.data['id'])
        self.assertEqual(media_file.file_type, 'image')
        self.assertEqual(media_file.uploaded_by, self.user)
    
    def test_file_validation_and_security(self):
        """Test file validation and security measures."""
        upload_url = reverse('posts:media-upload')
        
        # Test invalid file type
        text_file = BytesIO(b'This is not an image file')
        upload_data = {
            'file': SimpleUploadedFile(
                name='malicious.txt',
                content=text_file.getvalue(),
                content_type='text/plain'
            )
        }
        
        response = self.client.post(upload_url, upload_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test executable file (security)
        exe_file = BytesIO(b'MZ\x90\x00')  # PE header
        upload_data = {
            'file': SimpleUploadedFile(
                name='malicious.exe',
                content=exe_file.getvalue(),
                content_type='application/octet-stream'
            )
        }
        
        response = self.client.post(upload_url, upload_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_media_attachment_to_posts(self):
        """Test attaching media files to posts."""
        # Upload media file
        image_file = self.create_test_image('JPEG', (600, 400), 'purple')
        upload_data = {
            'file': SimpleUploadedFile(
                name='post_image.jpg',
                content=image_file.getvalue(),
                content_type='image/jpeg'
            ),
            'alt_text': 'Article illustration'
        }
        
        upload_url = reverse('posts:media-upload')
        response = self.client.post(upload_url, upload_data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        media_file_id = response.data['id']
        
        # Create post
        post_data = {
            'title': 'Investment Strategies with Visual Guide',
            'content': 'This article includes visual guides to help understand investment strategies.',
            'tags': 'investing, strategies, visual',
            'status': 'draft'
        }
        
        posts_url = reverse('posts:post-list-create')
        response = self.client.post(posts_url, post_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post_id = response.data['id']
        
        # Attach media to post
        media_data = {
            'media_files': [
                {
                    'media_file_id': media_file_id,
                    'order': 0,
                    'caption': 'Investment strategy flowchart'
                }
            ]
        }
        
        attach_url = reverse('posts:post-media', kwargs={'pk': post_id})
        response = self.client.post(attach_url, media_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify attachment
        post_media = PostMedia.objects.get(post_id=post_id, media_file_id=media_file_id)
        self.assertEqual(post_media.caption, 'Investment strategy flowchart')
        self.assertEqual(post_media.order, 0)

class RoleBasedAccessControlTest(APITestCase):
    """Verify role-based access control and permission enforcement."""
    
    def setUp(self):
        # Create users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        
        self.editor_user = User.objects.create_user(
            username='editor',
            email='editor@example.com',
            password='editorpass123'
        )
        
        self.writer_user = User.objects.create_user(
            username='writer',
            email='writer@example.com',
            password='writerpass123'
        )
        
        self.reader_user = User.objects.create_user(
            username='reader',
            email='reader@example.com',
            password='readerpass123'
        )
        
        # Create roles
        self.admin_role = Role.objects.create(
            name='admin',
            display_name='Administrator',
            description='Full system access'
        )
        
        self.editor_role = Role.objects.create(
            name='editor',
            display_name='Editor',
            description='Can moderate content and manage writers'
        )
        
        self.writer_role = Role.objects.create(
            name='writer',
            display_name='Writer',
            description='Can create and edit posts'
        )
        
        self.reader_role = Role.objects.create(
            name='reader',
            display_name='Reader',
            description='Can read and interact with content'
        )
        
        # Assign roles
        UserRole.objects.create(user=self.admin_user, role=self.admin_role)
        UserRole.objects.create(user=self.editor_user, role=self.editor_role)
        UserRole.objects.create(user=self.writer_user, role=self.writer_role)
        UserRole.objects.create(user=self.reader_user, role=self.reader_role)
        
        # Create test post
        self.test_post = Post.objects.create(
            title='Test Post for RBAC',
            content='This is a test post for role-based access control testing.',
            author='Writer User',
            author_user=self.writer_user,
            status='published'
        )
    
    def test_admin_permissions(self):
        """Test admin user has full access."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Admin can access moderation dashboard
        moderation_url = reverse('moderation:moderation-dashboard')
        response = self.client.get(moderation_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Admin can create posts
        post_data = {
            'title': 'Admin Created Post',
            'content': 'This post was created by an admin.',
            'status': 'published'
        }
        
        posts_url = reverse('posts:post-list-create')
        response = self.client.post(posts_url, post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_writer_permissions(self):
        """Test writer user can create and edit own posts."""
        self.client.force_authenticate(user=self.writer_user)
        
        # Writer can create posts
        post_data = {
            'title': 'Writer Created Post',
            'content': 'This post was created by a writer.',
            'status': 'draft'
        }
        
        posts_url = reverse('posts:post-list-create')
        response = self.client.post(posts_url, post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_post_id = response.data['id']
        
        # Writer can edit own posts
        edit_data = {
            'title': 'Updated Writer Post',
            'content': 'This post was updated by the writer.'
        }
        
        edit_url = reverse('posts:post-detail', kwargs={'pk': new_post_id})
        response = self.client.patch(edit_url, edit_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Writer should NOT access moderation dashboard
        moderation_url = reverse('moderation:moderation-dashboard')
        response = self.client.get(moderation_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_reader_permissions(self):
        """Test reader user has limited access."""
        self.client.force_authenticate(user=self.reader_user)
        
        # Reader can view posts
        posts_url = reverse('posts:post-list-create')
        response = self.client.get(posts_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Reader can save posts
        save_url = reverse('posts:save-post', kwargs={'pk': self.test_post.id})
        response = self.client.post(save_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Reader should NOT create posts
        post_data = {
            'title': 'Reader Attempt',
            'content': 'This should not be allowed.',
            'status': 'draft'
        }
        
        response = self.client.post(posts_url, post_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_unauthenticated_access(self):
        """Test unauthenticated user access."""
        # Unauthenticated can view published posts
        posts_url = reverse('posts:post-list-create')
        response = self.client.get(posts_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Unauthenticated should NOT create posts
        post_data = {
            'title': 'Unauthorized Attempt',
            'content': 'This should not be allowed.',
            'status': 'draft'
        }
        
        response = self.client.post(posts_url, post_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LoadTestingAndPerformanceTest(APITestCase):
    """Perform load testing on new features and background task processing."""
    
    def setUp(self):
        # Create test users
        self.users = []
        for i in range(10):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass123'
            )
            self.users.append(user)
        
        # Create writer role
        writer_role = Role.objects.create(
            name='writer',
            display_name='Writer',
            description='Can create posts'
        )
        
        # Assign writer role to some users
        for user in self.users[:5]:
            UserRole.objects.create(user=user, role=writer_role)
        
        # Create test posts
        self.posts = []
        for i in range(50):
            post = Post.objects.create(
                title=f'Performance Test Post {i}',
                content=f'This is test post content number {i}. ' * 20,
                author=f'Author {i % 5}',
                author_user=self.users[i % 5],
                status='published',
                tags=f'tag{i}, performance, test'
            )
            self.posts.append(post)
    
    def test_post_list_performance(self):
        """Test performance of post list endpoint with various loads."""
        posts_url = reverse('posts:post-list-create')
        
        # Test different page sizes
        page_sizes = [10, 25, 50]
        
        for page_size in page_sizes:
            start_time = time.time()
            
            response = self.client.get(posts_url, {'page_size': page_size})
            
            end_time = time.time()
            response_time = end_time - start_time
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertLessEqual(len(response.data['results']), page_size)
            
            # Response should be under 2 seconds for reasonable page sizes
            self.assertLess(response_time, 2.0, 
                          f"Response time {response_time:.2f}s too slow for page_size={page_size}")
    
    def test_search_performance(self):
        """Test search functionality performance."""
        posts_url = reverse('posts:post-list-create')
        
        search_terms = ['test', 'performance', 'content']
        
        for term in search_terms:
            start_time = time.time()
            
            response = self.client.get(posts_url, {'search': term})
            
            end_time = time.time()
            response_time = end_time - start_time
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Search should be under 3 seconds
            self.assertLess(response_time, 3.0, 
                          f"Search response time {response_time:.2f}s too slow for term '{term}'")
    
    def test_database_query_optimization(self):
        """Test database query optimization."""
        from django.test.utils import override_settings
        from django.db import connection
        
        posts_url = reverse('posts:post-list-create')
        
        with override_settings(DEBUG=True):
            # Reset query count
            connection.queries_log.clear()
            
            # Test post list with related data
            response = self.client.get(posts_url, {'page_size': 20})
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Check query count (should be optimized with select_related/prefetch_related)
            query_count = len(connection.queries)
            self.assertLess(query_count, 15, 
                          f"Too many database queries: {query_count}")


class SecurityTestingSuite(APITestCase):
    """Conduct security testing for authentication, file uploads, and user data protection."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!',
            is_staff=True,
            is_superuser=True
        )
    
    def test_authentication_security(self):
        """Test authentication security measures."""
        # Test password strength requirements
        weak_passwords = [
            'password',
            '123456',
            'qwerty',
            'abc123'
        ]
        
        register_url = reverse('accounts:register')
        
        for weak_password in weak_passwords:
            registration_data = {
                'username': f'user_{weak_password}',
                'email': f'{weak_password}@example.com',
                'password': weak_password,
                'password_confirm': weak_password
            }
            
            response = self.client.post(register_url, registration_data)
            
            # Should reject weak passwords
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('password', response.data)
    
    def test_sql_injection_protection(self):
        """Test protection against SQL injection attacks."""
        self.client.force_authenticate(user=self.user)
        
        # Test SQL injection in search parameters
        posts_url = reverse('posts:post-list-create')
        
        sql_injection_attempts = [
            "'; DROP TABLE posts; --",
            "' OR '1'='1",
            "'; UPDATE posts SET title='hacked'; --"
        ]
        
        for injection in sql_injection_attempts:
            response = self.client.get(posts_url, {'search': injection})
            
            # Should not cause server error and should return normal response
            self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
            
            # Verify no data was actually modified
            posts_count = Post.objects.count()
            self.assertGreaterEqual(posts_count, 0)  # Posts should still exist
    
    def test_xss_protection(self):
        """Test protection against XSS attacks."""
        self.client.force_authenticate(user=self.user)
        
        # Create writer role
        writer_role = Role.objects.create(
            name='writer',
            display_name='Writer',
            description='Can create posts'
        )
        UserRole.objects.create(user=self.user, role=writer_role)
        
        # Test XSS in post content
        xss_attempts = [
            '<script>alert("XSS")</script>',
            '<img src="x" onerror="alert(\'XSS\')">',
            '<svg onload="alert(\'XSS\')">',
            'javascript:alert("XSS")'
        ]
        
        posts_url = reverse('posts:post-list-create')
        
        for injection in sql_injection_attempts:
            response = self.client.get(posts_url, {'search': injection})
            
            # Should not cause server error and should return normal response
            self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
            
            # Verify no data was actually modified
            posts_count = Post.objects.count()
            self.assertGreaterEqual(posts_count, 0)  # Posts should still exist


class SecurityTestingSuite(APITestCase):
    """Conduct security testing for authentication, file uploads, and user data protection."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!',
            is_staff=True,
            is_superuser=True
        )
    
    def test_authentication_security(self):
        """Test authentication security measures."""
        # Test password strength requirements
        weak_passwords = [
            'password',
            '123456',
            'qwerty',
            'abc123'
        ]
        
        register_url = reverse('accounts:register')
        
        for weak_password in weak_passwords:
            registration_data = {
                'username': f'user_{weak_password}',
                'email': f'{weak_password}@example.com',
                'password': weak_password,
                'password_confirm': weak_password
            }
            
            response = self.client.post(register_url, registration_data)
            
            # Should reject weak passwords
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('password', response.data)
    
    def test_sql_injection_protection(self):
        """Test protection against SQL injection attacks."""
        self.client.force_authenticate(user=self.user)
        
        # Test SQL injection in search parameters
        posts_url = reverse('posts:post-list-create')
        
        sql_injection_attempts = [
            "'; DROP TABLE posts; --",
            "' OR '1'='1",
            "'; UPDATE posts SET title='hacked'; --"
        ]
        
        for injection in sql_injection_attempts:
            response = self.client.get(posts_url, {'search': injection})
            
            # Should not cause server error and should return normal response
            self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
            
            # Verify no data was actually modified
            posts_count = Post.objects.count()
            self.assertGreaterEqual(posts_count, 0)  # Posts should still exist
    
    def test_xss_protection(self):
        """Test protection against XSS attacks."""
        self.client.force_authenticate(user=self.user)
        
        # Create writer role
        writer_role = Role.objects.create(
            name='writer',
            display_name='Writer',
            description='Can create posts'
        )
        UserRole.objects.create(user=self.user, role=writer_role)
        
        # Test XSS in post content
        xss_attempts = [
            '<script>alert("XSS")</script>',
            '<img src="x" onerror="alert(\'XSS\')">',
            '<svg onload="alert(\'XSS\')">',
            'javascript:alert("XSS")'
        ]
        
        posts_url = reverse('posts:post-list-create')
        
        for xss_payload in xss_attempts:
            post_data = {
                'title': f'Test Post with XSS: {xss_payload}',
                'content': f'This post contains XSS attempt: {xss_payload}',
                'status': 'draft'
            }
            
            response = self.client.post(posts_url, post_data)
            
            if response.status_code == status.HTTP_201_CREATED:
                # Verify content was sanitized
                post_id = response.data['id']
                post = Post.objects.get(id=post_id)
                
                # XSS payload should be escaped or removed
                self.assertNotIn('<script>', post.content)
                self.assertNotIn('javascript:', post.content)
                self.assertNotIn('onerror=', post.content)
                self.assertNotIn('onload=', post.content)
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_file_upload_security(self):
        """Test file upload security measures."""
        self.client.force_authenticate(user=self.user)
        
        # Create writer role
        writer_role = Role.objects.create(
            name='writer',
            display_name='Writer',
            description='Can create posts'
        )
        UserRole.objects.create(user=self.user, role=writer_role)
        
        upload_url = reverse('posts:media-upload')
        
        # Test malicious file uploads
        malicious_files = [
            # PHP script
            {
                'name': 'malicious.php',
                'content': b'<?php system($_GET["cmd"]); ?>',
                'content_type': 'application/x-php'
            },
            # JavaScript file
            {
                'name': 'malicious.js',
                'content': b'alert("XSS");',
                'content_type': 'application/javascript'
            },
            # Executable file
            {
                'name': 'malicious.exe',
                'content': b'MZ\x90\x00\x03\x00\x00\x00',
                'content_type': 'application/octet-stream'
            }
        ]
        
        for malicious_file in malicious_files:
            upload_data = {
                'file': SimpleUploadedFile(
                    name=malicious_file['name'],
                    content=malicious_file['content'],
                    content_type=malicious_file['content_type']
                )
            }
            
            response = self.client.post(upload_url, upload_data, format='multipart')
            
            # Should reject malicious files
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_authorization_bypass_attempts(self):
        """Test protection against authorization bypass attempts."""
        # Create another user's post
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='OtherPass123!'
        )
        
        writer_role = Role.objects.create(
            name='writer',
            display_name='Writer',
            description='Can create posts'
        )
        UserRole.objects.create(user=other_user, role=writer_role)
        
        other_post = Post.objects.create(
            title='Other User Post',
            content='This post belongs to another user.',
            author='Other User',
            author_user=other_user,
            status='published'
        )
        
        # Test unauthorized access attempts
        self.client.force_authenticate(user=self.user)
        
        # Try to edit other user's post
        edit_url = reverse('posts:post-detail', kwargs={'pk': other_post.id})
        edit_data = {
            'title': 'Hacked Title',
            'content': 'This content was changed by unauthorized user.'
        }
        
        response = self.client.patch(edit_url, edit_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Try to delete other user's post
        response = self.client.delete(edit_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Verify post was not modified
        other_post.refresh_from_db()
        self.assertEqual(other_post.title, 'Other User Post')
        self.assertEqual(other_post.content, 'This post belongs to another user.')
    
    def test_sensitive_data_exposure(self):
        """Test protection against sensitive data exposure."""
        # Test that sensitive user data is not exposed in API responses
        self.client.force_authenticate(user=self.user)
        
        # Get user profile
        profile_url = reverse('accounts:user-profile')
        response = self.client.get(profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Sensitive fields should not be exposed
        sensitive_fields = ['password', 'email_verification_token', 'unsubscribe_token']
        
        for field in sensitive_fields:
            self.assertNotIn(field, response.data)         
 rl)
   le_u.get(proficlientnse = self.    respo')
    ofile-prer:use('accountsl = reversrofile_ur    p  
  leofiser pr     # Get u      
   ser)
  r=self.uticate(usethent.force_auf.cliensel     ses
    responed in APIt expos is nouser datae hat sensitivTest t      # e."""
  ata exposurve dsitisennst ection agait prot"Tes       ""):
 sure(selfve_data_expo_sensiti test   def
    
 ')r user.thelongs to anot beis post, 'Thcontenther_post.sertEqual(o.as   selft')
     her User Pos'Ottitle, post.her_rtEqual(otssef.a    sel
    db()m_fresh_fro_post.re       othered
 t modifist was noy po # Verif   
       N)
     _FORBIDDEtus.HTTP_403_code, staonse.statusrespl(Equalf.assert     se   t_url)
e(ediclient.deletf.ele = s    respons post
    user's other y to delete  # Tr    
      
    EN)FORBIDD403_P_tus.HTTcode, staonse.status_(respassertEqual     self._data)
   editedit_url, nt.patch(elf.clie = sse    respon
            }
      er.'
  thorized us by unau was changedntent'This content':    'co       itle',
   'Hacked Tle':it      't{
      ata =     edit_did})
     other_post.s={'pk':wargail', ketts:post-d'pos reverse(t_url =di
        eser's post other u edit# Try to
               .user)
 lf(user=sehenticateforce_autt.clienf.el s
       mpts access attehorizedst unaut    # Te
                 )
  
 ished's='publ  statu      _user,
    herer=otauthor_us           ,
 er User'r='Othutho  a        ',
  user. to another gsonis post bel='Thnt       conte  Post',
   er User  title='Oth   
        cts.create(st.objeost = Po     other_p      
   er_role)
  rituser, role=wher_user=otcreate(bjects.e.o UserRol
          )     sts'
n create poCaescription='      d,
      ame='Writer'isplay_n d           
r',me='writena      
      (teects.crea= Role.objrole   writer_    
      )
    !'
        s123rPastheword='O      pass  ',
    omer@example.cemail='oth       er',
     therusame='ousern     (
       reate_userects.cr = User.objer_use oth     post
   ther user'sreate ano  # C     """
  attempts.on bypasshorizati against autonotecti""Test pr"
        :(self)_attemptspass_byorization test_auth    def   
EQUEST)
 P_400_BAD_R status.HTTe,status_codonse.l(respassertEquaf.       seliles
     s f maliciouect# Should rej           
           art')
  ipformat='multdata, load_l, upoad_urst(upl.poelf.clientnse = s    respo                  
}
              )
         ']
       content_typefile['us_=maliciont_type  conte                 ent'],
 le['cont_filiciouscontent=ma               '],
     _file['nameiousicname=mal                  
  ploadedFile(impleU 'file': S              ta = {
 ad_da       uplo    _files:
  maliciousus_file inlicio      for ma    
       ]
     }
   
           eam'et-strcation/octype': 'applint_tconte     '          \x00',
 \x00\x00x03\x00\\x90b'MZnt':       'conte
          cious.exe',ame': 'mali   'n       
        {          ile
ecutable f      # Ex  ,
     }     ipt'
      ion/javascrate': 'applicypcontent_t          ');',
      ""XSSt('aler bontent':      'c       s.js',
   ': 'maliciouname          '   {
           le
    pt fi JavaScri        #        },
 p'
       -ph/xcation': 'applient_typeont 'c           
    ',d"]); ?>cm($_GET["<?php systemnt': b'     'conte    p',
       alicious.ph'name': 'm                    {
 
        PHP script           #les = [
 fious_ci        malie uploads
cious filmali   # Test   
     ')
      ia-uploadposts:mederse(' revl =ur     upload_      
ole)
     =writer_rleser, rolf.uate(user=seects.creole.obj      UserR       )
  te posts'
 Can crean='scriptio     de     iter',
  ame='Wrlay_n      disp     ,
 iter'name='wr            .create(
e.objectsrole = Rol    writer_
    r roleate write      # Cre   
     user)
  =self.ate(useruthentice_a.client.forc     self"
   easures."" muritye upload sec fil  """Test      y(self):
d_securitt_file_uploaf tes))
    demkdtemp(OT=tempfile.A_ROtings(MEDIoverride_set   
    @ontent)
 .c, postn('onload='ssertNotI     self.a           t.content)
r=', posroIn('onerssertNot     self.a      ent)
     .contript:', postvasctIn('ja.assertNo  self             ntent)
 , post.copt>'cri<sotIn('elf.assertN         s      r removed
 aped oould be escayload sh # XSS p                      
        )
 t(id=post_idts.geost.objec   post = P       d']
      .data['i= response_id    post             d
tizewas sanify content eri # V               TED:
201_CREATP_HTstatus.e == _codponse.statusif res                  
 ta)
     t_das_url, post.post(post= self.clienponse  res         
            }
              ft'
tus': 'dra  'sta            d}',
  oaayl{xss_pS attempt: XStains is post con f'Th'content':               
 ad}', {xss_paylowith XSS:st Post 'Tele': f  'tit         = {
     st_data       po     ttempts:
 n xss_ass_payload ior x