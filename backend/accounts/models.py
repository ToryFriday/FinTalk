"""
User authentication and profile models for the enhanced blog platform.
"""

from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid
import os


def avatar_upload_path(instance, filename):
    """
    Generate upload path for user avatars.
    """
    ext = filename.split('.')[-1]
    filename = f"{instance.user.id}_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join('avatars', filename)


class UserProfile(models.Model):
    """
    Extended user profile model with additional fields for bio, avatar, and verification.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True, help_text="Brief description about the user")
    avatar = models.ImageField(
        upload_to=avatar_upload_path, 
        blank=True, 
        null=True,
        help_text="User profile picture"
    )
    website = models.URLField(blank=True, help_text="User's personal website")
    location = models.CharField(max_length=100, blank=True, help_text="User's location")
    birth_date = models.DateField(null=True, blank=True, help_text="User's birth date")
    
    # Email verification fields
    is_email_verified = models.BooleanField(default=False, help_text="Whether user's email is verified")
    email_verification_token = models.CharField(
        max_length=100, 
        blank=True, 
        help_text="Token for email verification"
    )
    email_verification_sent_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the verification email was last sent"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        indexes = [
            models.Index(fields=['user'], name='profile_user_idx'),
            models.Index(fields=['is_email_verified'], name='profile_verified_idx'),
            models.Index(fields=['email_verification_token'], name='profile_token_idx'),
            models.Index(fields=['-created_at'], name='profile_created_idx'),
        ]
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def clean(self):
        """
        Custom validation for UserProfile model.
        """
        errors = {}
        
        # Validate bio length
        if self.bio and len(self.bio.strip()) > 500:
            errors['bio'] = 'Bio cannot exceed 500 characters'
        
        # Validate location length
        if self.location and len(self.location.strip()) > 100:
            errors['location'] = 'Location cannot exceed 100 characters'
        
        # Validate birth date (must be in the past)
        if self.birth_date and self.birth_date >= timezone.now().date():
            errors['birth_date'] = 'Birth date must be in the past'
        
        # Validate website URL format
        if self.website and not self.website.startswith(('http://', 'https://')):
            errors['website'] = 'Website URL must start with http:// or https://'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """
        Override save method to ensure validation and clean data.
        """
        # Clean whitespace from text fields
        if self.bio:
            self.bio = self.bio.strip()
        if self.location:
            self.location = self.location.strip()
        if self.website:
            self.website = self.website.strip()
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def generate_verification_token(self):
        """
        Generate a new email verification token.
        """
        self.email_verification_token = uuid.uuid4().hex
        self.email_verification_sent_at = timezone.now()
        return self.email_verification_token
    
    def is_verification_token_expired(self, expiry_hours=24):
        """
        Check if the verification token has expired.
        """
        if not self.email_verification_sent_at:
            return True
        
        expiry_time = self.email_verification_sent_at + timezone.timedelta(hours=expiry_hours)
        return timezone.now() > expiry_time
    
    def get_full_name(self):
        """
        Get user's full name or username if full name is not available.
        """
        if self.user.first_name and self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}"
        elif self.user.first_name:
            return self.user.first_name
        else:
            return self.user.username
    
    def get_avatar_url(self):
        """
        Get avatar URL or return None if no avatar is set.
        """
        if self.avatar:
            return self.avatar.url
        return None
    
    @property
    def age(self):
        """
        Calculate user's age from birth date.
        """
        if not self.birth_date:
            return None
        
        today = timezone.now().date()
        age = today.year - self.birth_date.year
        
        # Adjust if birthday hasn't occurred this year
        if today.month < self.birth_date.month or \
           (today.month == self.birth_date.month and today.day < self.birth_date.day):
            age -= 1
        
        return age


class Role(models.Model):
    """
    Role model for role-based access control (RBAC).
    Defines different user roles with associated permissions.
    """
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('editor', 'Editor'),
        ('writer', 'Writer'),
        ('reader', 'Reader'),
        ('guest', 'Guest'),
    ]
    
    name = models.CharField(
        max_length=50, 
        unique=True, 
        choices=ROLE_CHOICES,
        help_text="Role name"
    )
    display_name = models.CharField(
        max_length=100,
        help_text="Human-readable role name"
    )
    description = models.TextField(
        help_text="Description of the role and its permissions"
    )
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        help_text="Permissions associated with this role"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this role is active and can be assigned"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'roles'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name'], name='role_name_idx'),
            models.Index(fields=['is_active'], name='role_active_idx'),
            models.Index(fields=['-created_at'], name='role_created_idx'),
        ]
        permissions = [
            ('can_manage_roles', 'Can manage user roles'),
            ('can_assign_roles', 'Can assign roles to users'),
            ('can_view_role_management', 'Can view role management interface'),
        ]
    
    def __str__(self):
        return self.display_name
    
    def clean(self):
        """
        Custom validation for Role model.
        """
        errors = {}
        
        if not self.name:
            errors['name'] = 'Role name is required'
        
        if not self.display_name:
            errors['display_name'] = 'Display name is required'
        
        if not self.description:
            errors['description'] = 'Description is required'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """
        Override save method to ensure validation and set display_name.
        """
        if not self.display_name and self.name:
            self.display_name = dict(self.ROLE_CHOICES).get(self.name, self.name.title())
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_permission_names(self):
        """
        Get list of permission names for this role.
        """
        return list(self.permissions.values_list('codename', flat=True))
    
    def has_permission(self, permission_codename):
        """
        Check if this role has a specific permission.
        """
        return self.permissions.filter(codename=permission_codename).exists()


class UserRole(models.Model):
    """
    Junction model for User-Role relationship with assignment tracking.
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='user_roles',
        help_text="User assigned to this role"
    )
    role = models.ForeignKey(
        Role, 
        on_delete=models.CASCADE,
        related_name='user_assignments',
        help_text="Role assigned to the user"
    )
    assigned_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_roles',
        help_text="User who assigned this role"
    )
    assigned_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this role was assigned"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this role assignment is active"
    )
    expires_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When this role assignment expires (optional)"
    )
    notes = models.TextField(
        blank=True,
        help_text="Notes about this role assignment"
    )
    
    class Meta:
        db_table = 'user_roles'
        unique_together = ['user', 'role']
        indexes = [
            models.Index(fields=['user'], name='user_role_user_idx'),
            models.Index(fields=['role'], name='user_role_role_idx'),
            models.Index(fields=['assigned_by'], name='user_role_assigned_by_idx'),
            models.Index(fields=['is_active'], name='user_role_active_idx'),
            models.Index(fields=['expires_at'], name='user_role_expires_idx'),
            models.Index(fields=['-assigned_at'], name='user_role_assigned_idx'),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.role.display_name}"
    
    def clean(self):
        """
        Custom validation for UserRole model.
        """
        errors = {}
        
        # Check if expires_at is in the future
        if self.expires_at and self.expires_at <= timezone.now():
            errors['expires_at'] = 'Expiration date must be in the future'
        
        # Prevent self-assignment for certain roles
        if self.assigned_by and self.assigned_by == self.user:
            if self.role.name in ['admin', 'editor']:
                errors['assigned_by'] = 'Users cannot assign admin or editor roles to themselves'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """
        Override save method to ensure validation.
        """
        self.full_clean()
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """
        Check if this role assignment has expired.
        """
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """
        Check if this role assignment is valid (active and not expired).
        """
        return self.is_active and not self.is_expired()


# Extend User model with role-related methods
def get_user_roles(self):
    """
    Get all active roles for this user.
    """
    # Handle anonymous users and non-User instances
    if not hasattr(self, 'is_authenticated') or not self.is_authenticated:
        return Role.objects.none()
    
    from django.db.models import Q
    
    return Role.objects.filter(
        user_assignments__user=self,
        user_assignments__is_active=True
    ).filter(
        Q(user_assignments__expires_at__isnull=True) |
        Q(user_assignments__expires_at__gt=timezone.now())
    ).distinct()

def has_role(self, role_name):
    """
    Check if user has a specific role.
    """
    # Handle anonymous users and non-User instances
    if not hasattr(self, 'is_authenticated') or not self.is_authenticated:
        return False
    
    return self.get_user_roles().filter(name=role_name).exists()

def has_any_role(self, role_names):
    """
    Check if user has any of the specified roles.
    """
    # Handle anonymous users and non-User instances
    if not hasattr(self, 'is_authenticated') or not self.is_authenticated:
        return False
    
    return self.get_user_roles().filter(name__in=role_names).exists()

def get_role_permissions(self):
    """
    Get all permissions from user's roles.
    """
    # Handle anonymous users and non-User instances
    if not hasattr(self, 'is_authenticated') or not self.is_authenticated:
        return Permission.objects.none()
    
    user_roles = self.get_user_roles()
    permissions = Permission.objects.filter(role__in=user_roles).distinct()
    return permissions

def has_role_permission(self, permission_codename):
    """
    Check if user has a specific permission through their roles.
    """
    # Handle anonymous users and non-User instances
    if not hasattr(self, 'is_authenticated') or not self.is_authenticated:
        return False
    
    return self.get_role_permissions().filter(codename=permission_codename).exists()

def is_admin(self):
    """
    Check if user has admin role.
    """
    return self.has_role('admin')

def is_editor(self):
    """
    Check if user has editor role.
    """
    return self.has_role('editor')

def is_writer(self):
    """
    Check if user has writer role.
    """
    return self.has_role('writer')

def is_reader(self):
    """
    Check if user has reader role.
    """
    return self.has_role('reader')

def get_highest_role(self):
    """
    Get the highest priority role for this user.
    Role hierarchy: admin > editor > writer > reader > guest
    """
    # Handle anonymous users and non-User instances
    if not hasattr(self, 'is_authenticated') or not self.is_authenticated:
        return 'guest'
    
    role_hierarchy = ['admin', 'editor', 'writer', 'reader', 'guest']
    user_roles = self.get_user_roles().values_list('name', flat=True)
    
    for role_name in role_hierarchy:
        if role_name in user_roles:
            return role_name
    
    return 'guest'  # Default role

# Add methods to User model
User.add_to_class('get_user_roles', get_user_roles)
User.add_to_class('has_role', has_role)
User.add_to_class('has_any_role', has_any_role)
User.add_to_class('get_role_permissions', get_role_permissions)
User.add_to_class('has_role_permission', has_role_permission)
User.add_to_class('is_admin', is_admin)
User.add_to_class('is_editor', is_editor)
User.add_to_class('is_writer', is_writer)
User.add_to_class('is_reader', is_reader)
User.add_to_class('get_highest_role', get_highest_role)


class SavedArticle(models.Model):
    """
    Model for tracking articles saved by users for later reading.
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='saved_articles',
        help_text="User who saved the article"
    )
    post = models.ForeignKey(
        'posts.Post',  # Use string reference to avoid circular import
        on_delete=models.CASCADE,
        related_name='saved_by_users',
        help_text="Post that was saved"
    )
    saved_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the article was saved"
    )
    notes = models.TextField(
        blank=True,
        max_length=500,
        help_text="Optional notes about why the article was saved"
    )
    
    class Meta:
        db_table = 'saved_articles'
        unique_together = ['user', 'post']
        ordering = ['-saved_at']
        indexes = [
            models.Index(fields=['user'], name='saved_articles_user_idx'),
            models.Index(fields=['post'], name='saved_articles_post_idx'),
            models.Index(fields=['-saved_at'], name='saved_articles_saved_at_idx'),
            models.Index(fields=['user', '-saved_at'], name='saved_articles_user_saved_idx'),
        ]
    
    def __str__(self):
        return f"{self.user.username} saved '{self.post.title}'"
    
    def clean(self):
        """
        Custom validation for SavedArticle model.
        """
        errors = {}
        
        # Validate notes length
        if self.notes and len(self.notes.strip()) > 500:
            errors['notes'] = 'Notes cannot exceed 500 characters'
        
        # Ensure user cannot save their own posts (optional business rule)
        if hasattr(self.post, 'author_user') and self.post.author_user == self.user:
            # Allow users to save their own posts - this might be useful for bookmarking
            pass
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """
        Override save method to ensure validation and clean data.
        """
        if self.notes:
            self.notes = self.notes.strip()
        
        self.full_clean()
        super().save(*args, **kwargs)


class UserFollow(models.Model):
    """
    Model for tracking user following relationships.
    Allows users to follow other users to get notifications about their new posts.
    """
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        help_text="User who is following"
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        help_text="User being followed"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the follow relationship was created"
    )
    
    class Meta:
        db_table = 'user_follows'
        unique_together = ['follower', 'following']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['follower'], name='user_follow_follower_idx'),
            models.Index(fields=['following'], name='user_follow_following_idx'),
            models.Index(fields=['-created_at'], name='user_follow_created_idx'),
            models.Index(fields=['follower', '-created_at'], name='user_follow_fol_created_idx'),
            models.Index(fields=['following', '-created_at'], name='user_follow_ing_created_idx'),
        ]
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"
    
    def clean(self):
        """
        Custom validation for UserFollow model.
        """
        errors = {}
        
        # Prevent users from following themselves
        if self.follower == self.following:
            errors['following'] = 'Users cannot follow themselves'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """
        Override save method to ensure validation.
        """
        self.full_clean()
        super().save(*args, **kwargs)


# Extend User model with social methods
def get_followers(self):
    """
    Get all users who follow this user.
    """
    return User.objects.filter(following__following=self)

def get_following(self):
    """
    Get all users this user is following.
    """
    return User.objects.filter(followers__follower=self)

def get_followers_count(self):
    """
    Get the count of followers for this user.
    """
    return self.followers.count()

def get_following_count(self):
    """
    Get the count of users this user is following.
    """
    return self.following.count()

def is_following(self, user):
    """
    Check if this user is following another user.
    """
    if not user or not hasattr(self, 'is_authenticated') or not self.is_authenticated:
        return False
    return self.following.filter(following=user).exists()

def is_followed_by(self, user):
    """
    Check if this user is followed by another user.
    """
    if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
        return False
    return self.followers.filter(follower=user).exists()

def follow(self, user):
    """
    Follow another user.
    Returns True if successful, False if already following or invalid.
    """
    if not user or user == self:
        return False
    
    follow_relationship, created = UserFollow.objects.get_or_create(
        follower=self,
        following=user
    )
    return created

def unfollow(self, user):
    """
    Unfollow another user.
    Returns True if successful, False if not following.
    """
    if not user or user == self:
        return False
    
    try:
        follow_relationship = UserFollow.objects.get(
            follower=self,
            following=user
        )
        follow_relationship.delete()
        return True
    except UserFollow.DoesNotExist:
        return False

def get_mutual_followers(self, user):
    """
    Get users who follow both this user and another user.
    """
    if not user:
        return User.objects.none()
    
    my_followers = self.get_followers()
    their_followers = user.get_followers()
    return my_followers.intersection(their_followers)

def get_suggested_users_to_follow(self, limit=10):
    """
    Get suggested users to follow based on mutual connections.
    """
    # Get users followed by people I follow
    following_ids = self.following.values_list('following_id', flat=True)
    suggested_user_ids = UserFollow.objects.filter(
        follower_id__in=following_ids
    ).exclude(
        following=self
    ).exclude(
        following_id__in=following_ids
    ).values_list('following_id', flat=True).distinct()
    
    return User.objects.filter(id__in=suggested_user_ids)[:limit]

# Add social methods to User model
User.add_to_class('get_followers', get_followers)
User.add_to_class('get_following', get_following)
User.add_to_class('get_followers_count', get_followers_count)
User.add_to_class('get_following_count', get_following_count)
User.add_to_class('is_following', is_following)
User.add_to_class('is_followed_by', is_followed_by)
User.add_to_class('follow', follow)
User.add_to_class('unfollow', unfollow)
User.add_to_class('get_mutual_followers', get_mutual_followers)
User.add_to_class('get_suggested_users_to_follow', get_suggested_users_to_follow)


# Signal to create UserProfile when User is created
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create UserProfile when a new User is created.
    """
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save UserProfile when User is saved.
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()

@receiver(post_save, sender=User)
def assign_default_role(sender, instance, created, **kwargs):
    """
    Assign default 'reader' role to new users.
    """
    if created:
        try:
            reader_role = Role.objects.get(name='reader')
            UserRole.objects.create(
                user=instance,
                role=reader_role,
                assigned_by=None,  # System assignment
                notes='Default role assigned on registration'
            )
        except Role.DoesNotExist:
            # Role doesn't exist yet, will be handled by management command
            pass