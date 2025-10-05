"""
Test factories for generating test data using factory_boy.
Provides consistent and realistic test data for all models.
"""

import factory
from factory.django import DjangoModelFactory
from factory import Faker, SubFactory, LazyAttribute, LazyFunction
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random

from accounts.models import UserProfile, Role, UserRole, SavedArticle, UserFollow
from posts.models import Post, MediaFile, PostMedia
from moderation.models import ContentFlag, ModerationAction, ModerationSettings
from notifications.models import EmailSubscription


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances."""
    
    class Meta:
        model = User
    
    username = Faker('user_name')
    email = Faker('email')
    first_name = Faker('first_name')
    last_name = Faker('last_name')
    is_active = True
    is_staff = False
    is_superuser = False
    date_joined = Faker('date_time_this_year', tzinfo=timezone.get_current_timezone())


class AdminUserFactory(UserFactory):
    """Factory for creating admin users."""
    
    is_staff = True
    is_superuser = True
    username = factory.Sequence(lambda n: f"admin{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")


class UserProfileFactory(DjangoModelFactory):
    """Factory for creating UserProfile instances."""
    
    class Meta:
        model = UserProfile
    
    user = SubFactory(UserFactory)
    bio = Faker('text', max_nb_chars=500)
    website = Faker('url')
    location = Faker('city')
    birth_date = Faker('date_of_birth', minimum_age=18, maximum_age=80)
    is_email_verified = True
    email_verification_token = Faker('uuid4')
    created_at = Faker('date_time_this_year', tzinfo=timezone.get_current_timezone())


class RoleFactory(DjangoModelFactory):
    """Factory for creating Role instances."""
    
    class Meta:
        model = Role
    
    name = factory.Iterator(['admin', 'editor', 'writer', 'reader', 'guest'])
    display_name = LazyAttribute(lambda obj: obj.name.title())
    description = Faker('sentence')
    is_active = True


class UserRoleFactory(DjangoModelFactory):
    """Factory for creating UserRole instances."""
    
    class Meta:
        model = UserRole
    
    user = SubFactory(UserFactory)
    role = SubFactory(RoleFactory)
    assigned_by = SubFactory(AdminUserFactory)
    assigned_at = Faker('date_time_this_month', tzinfo=timezone.get_current_timezone())
    is_active = True
    notes = Faker('sentence')


class PostFactory(DjangoModelFactory):
    """Factory for creating Post instances."""
    
    class Meta:
        model = Post
    
    title = Faker('sentence', nb_words=6)
    content = Faker('text', max_nb_chars=2000)
    author = LazyAttribute(lambda obj: obj.author_user.get_full_name() if obj.author_user else Faker('name').generate())
    author_user = SubFactory(UserFactory)
    tags = factory.LazyFunction(lambda: ', '.join(Faker('words', nb=3).generate()))
    image_url = Faker('image_url')
    status = factory.Iterator(['draft', 'published', 'scheduled'])
    view_count = Faker('random_int', min=0, max=10000)
    created_at = Faker('date_time_this_year', tzinfo=timezone.get_current_timezone())
    updated_at = LazyAttribute(lambda obj: obj.created_at + timedelta(hours=random.randint(0, 24)))


class PublishedPostFactory(PostFactory):
    """Factory for creating published posts."""
    
    status = 'published'
    scheduled_publish_date = None


class DraftPostFactory(PostFactory):
    """Factory for creating draft posts."""
    
    status = 'draft'
    scheduled_publish_date = None


class ScheduledPostFactory(PostFactory):
    """Factory for creating scheduled posts."""
    
    status = 'scheduled'
    scheduled_publish_date = Faker('future_datetime', end_date='+30d', tzinfo=timezone.get_current_timezone())


class MediaFileFactory(DjangoModelFactory):
    """Factory for creating MediaFile instances."""
    
    class Meta:
        model = MediaFile
    
    uploaded_by = SubFactory(UserFactory)
    file = Faker('file_path', depth=3, extension='jpg')
    file_type = factory.Iterator(['image', 'video', 'document'])
    original_name = Faker('file_name', extension='jpg')
    file_size = Faker('random_int', min=1024, max=5242880)  # 1KB to 5MB
    alt_text = Faker('sentence')
    created_at = Faker('date_time_this_month', tzinfo=timezone.get_current_timezone())


class ImageFileFactory(MediaFileFactory):
    """Factory for creating image files."""
    
    file_type = 'image'
    original_name = Faker('file_name', extension='jpg')


class VideoFileFactory(MediaFileFactory):
    """Factory for creating video files."""
    
    file_type = 'video'
    original_name = Faker('file_name', extension='mp4')
    file_size = Faker('random_int', min=5242880, max=104857600)  # 5MB to 100MB


class PostMediaFactory(DjangoModelFactory):
    """Factory for creating PostMedia instances."""
    
    class Meta:
        model = PostMedia
    
    post = SubFactory(PostFactory)
    media_file = SubFactory(MediaFileFactory)
    order = Faker('random_int', min=0, max=10)
    caption = Faker('sentence')
    created_at = Faker('date_time_this_month', tzinfo=timezone.get_current_timezone())


class SavedArticleFactory(DjangoModelFactory):
    """Factory for creating SavedArticle instances."""
    
    class Meta:
        model = SavedArticle
    
    user = SubFactory(UserFactory)
    post = SubFactory(PublishedPostFactory)
    saved_at = Faker('date_time_this_month', tzinfo=timezone.get_current_timezone())
    notes = Faker('sentence')


class UserFollowFactory(DjangoModelFactory):
    """Factory for creating UserFollow instances."""
    
    class Meta:
        model = UserFollow
    
    follower = SubFactory(UserFactory)
    following = SubFactory(UserFactory)
    created_at = Faker('date_time_this_month', tzinfo=timezone.get_current_timezone())


class ContentFlagFactory(DjangoModelFactory):
    """Factory for creating ContentFlag instances."""
    
    class Meta:
        model = ContentFlag
    
    post = SubFactory(PublishedPostFactory)
    flagged_by = SubFactory(UserFactory)
    reason = factory.Iterator(['spam', 'inappropriate', 'harassment', 'misinformation', 'copyright'])
    description = Faker('paragraph')
    status = factory.Iterator(['pending', 'under_review', 'resolved_valid', 'resolved_invalid'])
    created_at = Faker('date_time_this_month', tzinfo=timezone.get_current_timezone())


class PendingFlagFactory(ContentFlagFactory):
    """Factory for creating pending flags."""
    
    status = 'pending'
    reviewed_by = None
    reviewed_at = None


class ResolvedFlagFactory(ContentFlagFactory):
    """Factory for creating resolved flags."""
    
    status = factory.Iterator(['resolved_valid', 'resolved_invalid'])
    reviewed_by = SubFactory(AdminUserFactory)
    reviewed_at = Faker('date_time_this_week', tzinfo=timezone.get_current_timezone())
    resolution_notes = Faker('paragraph')
    action_taken = factory.Iterator(['content_removed', 'warning_issued', 'user_suspended', 'no_action'])


class ModerationActionFactory(DjangoModelFactory):
    """Factory for creating ModerationAction instances."""
    
    class Meta:
        model = ModerationAction
    
    flag = SubFactory(ResolvedFlagFactory)
    post = LazyAttribute(lambda obj: obj.flag.post)
    action_type = factory.Iterator(['content_removed', 'warning_issued', 'user_suspended', 'content_edited'])
    moderator = SubFactory(AdminUserFactory)
    reason = Faker('paragraph')
    affected_user = LazyAttribute(lambda obj: obj.post.author_user)
    severity_level = Faker('random_int', min=1, max=5)
    is_automated = False
    created_at = Faker('date_time_this_week', tzinfo=timezone.get_current_timezone())


class EmailSubscriptionFactory(DjangoModelFactory):
    """Factory for creating EmailSubscription instances."""
    
    class Meta:
        model = EmailSubscription
    
    user = SubFactory(UserFactory)
    email = LazyAttribute(lambda obj: obj.user.email if obj.user else Faker('email').generate())
    subscription_type = factory.Iterator(['all_posts', 'weekly_digest', 'author_posts', 'category_posts'])
    is_active = True
    unsubscribe_token = Faker('uuid4')
    created_at = Faker('date_time_this_month', tzinfo=timezone.get_current_timezone())


class AnonymousSubscriptionFactory(EmailSubscriptionFactory):
    """Factory for creating anonymous email subscriptions."""
    
    user = None
    email = Faker('email')


# Utility functions for creating test scenarios

def create_blog_scenario():
    """Create a complete blog scenario with users, posts, and interactions."""
    # Create users with different roles
    admin = AdminUserFactory()
    
    editor_role = RoleFactory(name='editor')
    editor = UserFactory()
    UserRoleFactory(user=editor, role=editor_role, assigned_by=admin)
    
    writer_role = RoleFactory(name='writer')
    writers = UserFactory.create_batch(3)
    for writer in writers:
        UserRoleFactory(user=writer, role=writer_role, assigned_by=admin)
    
    readers = UserFactory.create_batch(10)
    
    # Create posts by writers
    posts = []
    for writer in writers:
        writer_posts = PublishedPostFactory.create_batch(5, author_user=writer)
        posts.extend(writer_posts)
        
        # Create some drafts
        DraftPostFactory.create_batch(2, author_user=writer)
        
        # Create scheduled posts
        ScheduledPostFactory.create_batch(1, author_user=writer)
    
    # Create media files and attach to posts
    for post in posts[:10]:  # Add media to first 10 posts
        media_file = ImageFileFactory(uploaded_by=post.author_user)
        PostMediaFactory(post=post, media_file=media_file)
    
    # Create social interactions
    for reader in readers:
        # Follow some writers
        followed_writers = random.sample(writers, random.randint(1, 3))
        for writer in followed_writers:
            UserFollowFactory(follower=reader, following=writer)
        
        # Save some posts
        saved_posts = random.sample(posts, random.randint(1, 5))
        for post in saved_posts:
            SavedArticleFactory(user=reader, post=post)
        
        # Subscribe to notifications
        EmailSubscriptionFactory(user=reader)
    
    # Create some content flags
    flagged_posts = random.sample(posts, 5)
    for post in flagged_posts:
        flagger = random.choice(readers)
        ContentFlagFactory(post=post, flagged_by=flagger)
    
    # Resolve some flags
    pending_flags = ContentFlag.objects.filter(status='pending')[:3]
    for flag in pending_flags:
        ResolvedFlagFactory(
            id=flag.id,
            post=flag.post,
            flagged_by=flag.flagged_by,
            reviewed_by=editor
        )
        ModerationActionFactory(flag=flag, moderator=editor)
    
    return {
        'admin': admin,
        'editor': editor,
        'writers': writers,
        'readers': readers,
        'posts': posts
    }


def create_performance_test_data():
    """Create large dataset for performance testing."""
    print("Creating performance test data...")
    
    # Create users
    users = UserFactory.create_batch(100)
    writers = users[:20]  # First 20 are writers
    readers = users[20:]  # Rest are readers
    
    # Assign writer roles
    writer_role = RoleFactory(name='writer')
    for writer in writers:
        UserRoleFactory(user=writer, role=writer_role)
    
    # Create many posts
    posts = []
    for writer in writers:
        writer_posts = PublishedPostFactory.create_batch(25, author_user=writer)
        posts.extend(writer_posts)
    
    print(f"Created {len(posts)} posts")
    
    # Create social interactions
    for reader in readers:
        # Follow random writers
        followed_writers = random.sample(writers, random.randint(1, 5))
        for writer in followed_writers:
            UserFollowFactory(follower=reader, following=writer)
        
        # Save random posts
        saved_posts = random.sample(posts, random.randint(1, 10))
        for post in saved_posts:
            SavedArticleFactory(user=reader, post=post)
    
    print("Performance test data created successfully")
    return len(posts)


# Custom factory traits for specific scenarios

class PostFactory(PostFactory):
    """Enhanced PostFactory with traits."""
    
    class Params:
        # Traits for different post types
        viral = factory.Trait(
            view_count=factory.Faker('random_int', min=10000, max=100000),
            tags='viral, trending, popular'
        )
        
        controversial = factory.Trait(
            tags='controversial, debate, opinion'
        )
        
        technical = factory.Trait(
            tags='technical, analysis, data',
            content=factory.Faker('text', max_nb_chars=5000)  # Longer content
        )
        
        beginner_friendly = factory.Trait(
            tags='beginner, basics, introduction',
            title=factory.LazyFunction(lambda: f"Beginner's Guide to {Faker('word').generate().title()}")
        )


# Usage examples:
# viral_post = PostFactory(viral=True)
# controversial_post = PostFactory(controversial=True)
# technical_post = PostFactory(technical=True)