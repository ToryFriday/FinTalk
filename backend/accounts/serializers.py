"""
Serializers for user authentication and profile management.
"""

from rest_framework import serializers
from django.contrib.auth.models import User, Permission
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from .models import UserProfile, Role, UserRole, SavedArticle, UserFollow


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with email verification.
    """
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=30)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=30)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm', 'first_name', 'last_name')
    
    def validate_username(self, value):
        """
        Validate username uniqueness and format.
        """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters long.")
        
        if not value.replace('_', '').replace('-', '').isalnum():
            raise serializers.ValidationError("Username can only contain letters, numbers, underscores, and hyphens.")
        
        return value
    
    def validate_email(self, value):
        """
        Validate email uniqueness.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_password(self, value):
        """
        Validate password using Django's password validators.
        """
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value
    
    def validate(self, attrs):
        """
        Validate that passwords match.
        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Password confirmation does not match password.'
            })
        return attrs
    
    def create(self, validated_data):
        """
        Create user with validated data.
        """
        # Remove password_confirm as it's not needed for user creation
        validated_data.pop('password_confirm')
        
        # Create user with is_active=False until email verification
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            is_active=False  # User must verify email first
        )
        
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information with avatar upload.
    """
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    avatar_url = serializers.CharField(source='get_avatar_url', read_only=True)
    age = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = (
            'user_id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'bio', 'avatar', 'avatar_url', 'website', 'location', 'birth_date', 'age',
            'is_email_verified', 'created_at', 'updated_at'
        )
        read_only_fields = ('is_email_verified', 'created_at', 'updated_at')
    
    def validate_avatar(self, value):
        """
        Validate avatar file size and type.
        """
        if value:
            # Check file size (max 5MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Avatar file size cannot exceed 5MB.")
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
            if value.content_type not in allowed_types:
                raise serializers.ValidationError(
                    "Avatar must be a JPEG, PNG, or GIF image."
                )
        
        return value


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile information.
    """
    first_name = serializers.CharField(source='user.first_name', max_length=30, required=False)
    last_name = serializers.CharField(source='user.last_name', max_length=30, required=False)
    
    class Meta:
        model = UserProfile
        fields = ('bio', 'avatar', 'website', 'location', 'birth_date', 'first_name', 'last_name')
    
    def validate_avatar(self, value):
        """
        Validate avatar file size and type.
        """
        if value:
            # Check file size (max 5MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Avatar file size cannot exceed 5MB.")
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
            if value.content_type not in allowed_types:
                raise serializers.ValidationError(
                    "Avatar must be a JPEG, PNG, or GIF image."
                )
        
        return value
    
    def update(self, instance, validated_data):
        """
        Update user profile and related user fields.
        """
        # Extract user fields
        user_data = {}
        if 'user' in validated_data:
            user_data = validated_data.pop('user')
        
        # Update user fields if provided
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()
        
        # Update profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializer for email verification token.
    """
    token = serializers.CharField(max_length=100)
    
    def validate_token(self, value):
        """
        Validate that the token exists and is not expired.
        """
        try:
            profile = UserProfile.objects.get(email_verification_token=value)
            if profile.is_verification_token_expired():
                raise serializers.ValidationError("Verification token has expired.")
            return value
        except UserProfile.DoesNotExist:
            raise serializers.ValidationError("Invalid verification token.")


class ResendVerificationSerializer(serializers.Serializer):
    """
    Serializer for resending email verification.
    """
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """
        Validate that the email exists and is not already verified.
        """
        try:
            user = User.objects.get(email=value)
            if user.profile.is_email_verified:
                raise serializers.ValidationError("Email is already verified.")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address.")


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})
    
    def validate(self, attrs):
        """
        Validate login credentials.
        """
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            # Try to authenticate with username or email
            from django.contrib.auth import authenticate
            
            # First try with username
            user = authenticate(username=username, password=password)
            
            # If that fails, try with email
            if not user:
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass
            
            if not user:
                raise serializers.ValidationError("Invalid username/email or password.")
            
            if not user.is_active:
                raise serializers.ValidationError("User account is not active. Please verify your email.")
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError("Must include username and password.")


class UserBasicSerializer(serializers.ModelSerializer):
    """
    Basic user serializer for public user information.
    """
    full_name = serializers.CharField(source='profile.get_full_name', read_only=True)
    avatar_url = serializers.CharField(source='profile.get_avatar_url', read_only=True)
    bio = serializers.CharField(source='profile.bio', read_only=True)
    location = serializers.CharField(source='profile.location', read_only=True)
    website = serializers.CharField(source='profile.website', read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'full_name', 
                 'avatar_url', 'bio', 'location', 'website', 'date_joined')
        read_only_fields = ('id', 'username', 'date_joined')


# RBAC Serializers

class PermissionSerializer(serializers.ModelSerializer):
    """
    Serializer for Django permissions.
    """
    class Meta:
        model = Permission
        fields = ('id', 'name', 'codename', 'content_type')
        read_only_fields = ('id', 'name', 'codename', 'content_type')


class RoleSerializer(serializers.ModelSerializer):
    """
    Serializer for Role model with permissions.
    """
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of permission IDs to assign to this role"
    )
    permission_count = serializers.SerializerMethodField()
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = (
            'id', 'name', 'display_name', 'description', 'permissions', 
            'permission_ids', 'permission_count', 'user_count', 'is_active',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'permission_count', 'user_count')
    
    def get_permission_count(self, obj):
        """Get the number of permissions assigned to this role."""
        return obj.permissions.count()
    
    def get_user_count(self, obj):
        """Get the number of users assigned to this role."""
        return obj.user_assignments.filter(is_active=True).count()
    
    def validate_name(self, value):
        """Validate role name."""
        if not value:
            raise serializers.ValidationError("Role name is required.")
        
        # Check if role name is in allowed choices
        allowed_names = [choice[0] for choice in Role.ROLE_CHOICES]
        if value not in allowed_names:
            raise serializers.ValidationError(f"Role name must be one of: {', '.join(allowed_names)}")
        
        return value
    
    def validate_permission_ids(self, value):
        """Validate that all permission IDs exist."""
        if value:
            existing_ids = set(Permission.objects.filter(id__in=value).values_list('id', flat=True))
            invalid_ids = set(value) - existing_ids
            if invalid_ids:
                raise serializers.ValidationError(f"Invalid permission IDs: {list(invalid_ids)}")
        return value
    
    def create(self, validated_data):
        """Create role with permissions."""
        permission_ids = validated_data.pop('permission_ids', [])
        role = Role.objects.create(**validated_data)
        
        if permission_ids:
            permissions = Permission.objects.filter(id__in=permission_ids)
            role.permissions.set(permissions)
        
        return role
    
    def update(self, instance, validated_data):
        """Update role with permissions."""
        permission_ids = validated_data.pop('permission_ids', None)
        
        # Update role fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update permissions if provided
        if permission_ids is not None:
            permissions = Permission.objects.filter(id__in=permission_ids)
            instance.permissions.set(permissions)
        
        return instance


class UserRoleSerializer(serializers.ModelSerializer):
    """
    Serializer for UserRole model.
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_full_name = serializers.CharField(source='user.profile.get_full_name', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    role_display_name = serializers.CharField(source='role.display_name', read_only=True)
    assigned_by_username = serializers.CharField(source='assigned_by.username', read_only=True)
    is_expired = serializers.SerializerMethodField()
    is_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = UserRole
        fields = (
            'id', 'user', 'user_username', 'user_email', 'user_full_name',
            'role', 'role_name', 'role_display_name', 'assigned_by', 
            'assigned_by_username', 'assigned_at', 'is_active', 'expires_at',
            'notes', 'is_expired', 'is_valid'
        )
        read_only_fields = ('id', 'assigned_at', 'is_expired', 'is_valid')
    
    def get_is_expired(self, obj):
        """Check if the role assignment is expired."""
        return obj.is_expired()
    
    def get_is_valid(self, obj):
        """Check if the role assignment is valid."""
        return obj.is_valid()
    
    def validate(self, attrs):
        """Validate user role assignment."""
        user = attrs.get('user')
        role = attrs.get('role')
        assigned_by = attrs.get('assigned_by')
        expires_at = attrs.get('expires_at')
        
        # Check if user already has this role
        if self.instance is None:  # Creating new assignment
            if UserRole.objects.filter(user=user, role=role, is_active=True).exists():
                raise serializers.ValidationError("User already has this role assigned.")
        
        # Validate expiration date
        if expires_at and expires_at <= timezone.now():
            raise serializers.ValidationError("Expiration date must be in the future.")
        
        # Prevent self-assignment for admin/editor roles
        if assigned_by and assigned_by == user and role.name in ['admin', 'editor']:
            raise serializers.ValidationError("Users cannot assign admin or editor roles to themselves.")
        
        return attrs


class RoleAssignmentSerializer(serializers.Serializer):
    """
    Serializer for assigning roles to users.
    """
    user_id = serializers.IntegerField()
    role_id = serializers.IntegerField()
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)
    
    def validate_user_id(self, value):
        """Validate that user exists."""
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")
        return value
    
    def validate_role_id(self, value):
        """Validate that role exists and is active."""
        try:
            role = Role.objects.get(id=value)
            if not role.is_active:
                raise serializers.ValidationError("Role is not active.")
        except Role.DoesNotExist:
            raise serializers.ValidationError("Role does not exist.")
        return value
    
    def validate(self, attrs):
        """Validate role assignment."""
        user_id = attrs['user_id']
        role_id = attrs['role_id']
        expires_at = attrs.get('expires_at')
        
        # Check if user already has this role
        if UserRole.objects.filter(user_id=user_id, role_id=role_id, is_active=True).exists():
            raise serializers.ValidationError("User already has this role assigned.")
        
        # Validate expiration date
        if expires_at and expires_at <= timezone.now():
            raise serializers.ValidationError("Expiration date must be in the future.")
        
        return attrs


class UserWithRolesSerializer(serializers.ModelSerializer):
    """
    Serializer for User with their roles information.
    """
    profile = UserProfileSerializer(read_only=True)
    roles = serializers.SerializerMethodField()
    active_roles = serializers.SerializerMethodField()
    highest_role = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 
            'is_active', 'is_staff', 'is_superuser', 'date_joined',
            'profile', 'roles', 'active_roles', 'highest_role', 'permissions'
        )
        read_only_fields = ('id', 'date_joined')
    
    def get_roles(self, obj):
        """Get all role assignments for this user."""
        user_roles = UserRole.objects.filter(user=obj).select_related('role', 'assigned_by')
        return UserRoleSerializer(user_roles, many=True).data
    
    def get_active_roles(self, obj):
        """Get active roles for this user."""
        active_roles = obj.get_user_roles()
        return RoleSerializer(active_roles, many=True).data
    
    def get_highest_role(self, obj):
        """Get the highest priority role for this user."""
        return obj.get_highest_role()
    
    def get_permissions(self, obj):
        """Get all permissions from user's roles."""
        permissions = obj.get_role_permissions()
        return PermissionSerializer(permissions, many=True).data


class RoleManagementSerializer(serializers.Serializer):
    """
    Serializer for role management operations.
    """
    action = serializers.ChoiceField(choices=['assign', 'revoke', 'update'])
    user_id = serializers.IntegerField()
    role_id = serializers.IntegerField()
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)
    
    def validate_user_id(self, value):
        """Validate that user exists."""
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")
        return value
    
    def validate_role_id(self, value):
        """Validate that role exists."""
        try:
            Role.objects.get(id=value)
        except Role.DoesNotExist:
            raise serializers.ValidationError("Role does not exist.")
        return value


class SavedArticleSerializer(serializers.ModelSerializer):
    """
    Serializer for SavedArticle model with post details.
    """
    post_title = serializers.CharField(source='post.title', read_only=True)
    post_content = serializers.CharField(source='post.content', read_only=True)
    post_author = serializers.CharField(source='post.get_author_name', read_only=True)
    post_created_at = serializers.DateTimeField(source='post.created_at', read_only=True)
    post_updated_at = serializers.DateTimeField(source='post.updated_at', read_only=True)
    post_tags = serializers.CharField(source='post.tags', read_only=True)
    post_image_url = serializers.URLField(source='post.image_url', read_only=True)
    post_view_count = serializers.IntegerField(source='post.view_count', read_only=True)
    post_status = serializers.CharField(source='post.status', read_only=True)
    
    class Meta:
        model = SavedArticle
        fields = (
            'id', 'post', 'saved_at', 'notes',
            'post_title', 'post_content', 'post_author', 'post_created_at', 
            'post_updated_at', 'post_tags', 'post_image_url', 'post_view_count',
            'post_status'
        )
        read_only_fields = ('id', 'saved_at')
    
    def validate_post(self, value):
        """
        Validate that the post exists and is published.
        """
        if not value:
            raise serializers.ValidationError("Post is required.")
        
        # Only allow saving published posts
        if value.status != 'published':
            raise serializers.ValidationError("Only published posts can be saved.")
        
        return value
    
    def validate(self, attrs):
        """
        Validate that user is not saving their own post (optional business rule).
        """
        post = attrs.get('post')
        user = self.context['request'].user if 'request' in self.context else None
        
        # Allow users to save their own posts - this might be useful for bookmarking
        # If you want to prevent this, uncomment the following lines:
        # if post and user and hasattr(post, 'author_user') and post.author_user == user:
        #     raise serializers.ValidationError("You cannot save your own posts.")
        
        return attrs
    
    def create(self, validated_data):
        """
        Create a saved article entry.
        """
        # Set the user from the request context
        user = self.context['request'].user
        validated_data['user'] = user
        
        return super().create(validated_data)


class SavedArticleListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing saved articles.
    """
    post_title = serializers.CharField(source='post.title', read_only=True)
    post_author = serializers.CharField(source='post.get_author_name', read_only=True)
    post_created_at = serializers.DateTimeField(source='post.created_at', read_only=True)
    post_tags = serializers.CharField(source='post.tags', read_only=True)
    post_image_url = serializers.URLField(source='post.image_url', read_only=True)
    post_view_count = serializers.IntegerField(source='post.view_count', read_only=True)
    
    class Meta:
        model = SavedArticle
        fields = (
            'id', 'post', 'saved_at', 'notes',
            'post_title', 'post_author', 'post_created_at', 
            'post_tags', 'post_image_url', 'post_view_count'
        )
        read_only_fields = ('id', 'saved_at')


# Social Features Serializers

class UserFollowSerializer(serializers.ModelSerializer):
    """
    Serializer for UserFollow model.
    """
    follower_username = serializers.CharField(source='follower.username', read_only=True)
    follower_full_name = serializers.CharField(source='follower.profile.get_full_name', read_only=True)
    follower_avatar_url = serializers.CharField(source='follower.profile.get_avatar_url', read_only=True)
    following_username = serializers.CharField(source='following.username', read_only=True)
    following_full_name = serializers.CharField(source='following.profile.get_full_name', read_only=True)
    following_avatar_url = serializers.CharField(source='following.profile.get_avatar_url', read_only=True)
    
    class Meta:
        model = UserFollow
        fields = (
            'id', 'follower', 'following', 'created_at',
            'follower_username', 'follower_full_name', 'follower_avatar_url',
            'following_username', 'following_full_name', 'following_avatar_url'
        )
        read_only_fields = ('id', 'created_at')


class UserFollowListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing user follows.
    """
    username = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    bio = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    
    class Meta:
        model = UserFollow
        fields = (
            'id', 'created_at', 'username', 'full_name', 'avatar_url', 
            'bio', 'followers_count', 'following_count', 'is_following'
        )
        read_only_fields = ('id', 'created_at')
    
    def __init__(self, *args, **kwargs):
        self.follow_type = kwargs.pop('follow_type', 'following')  # 'following' or 'followers'
        super().__init__(*args, **kwargs)
    
    def get_username(self, obj):
        """Get username based on follow type."""
        if self.follow_type == 'following':
            return obj.following.username
        return obj.follower.username
    
    def get_full_name(self, obj):
        """Get full name based on follow type."""
        if self.follow_type == 'following':
            return obj.following.profile.get_full_name()
        return obj.follower.profile.get_full_name()
    
    def get_avatar_url(self, obj):
        """Get avatar URL based on follow type."""
        if self.follow_type == 'following':
            return obj.following.profile.get_avatar_url()
        return obj.follower.profile.get_avatar_url()
    
    def get_bio(self, obj):
        """Get bio based on follow type."""
        if self.follow_type == 'following':
            return obj.following.profile.bio
        return obj.follower.profile.bio
    
    def get_followers_count(self, obj):
        """Get followers count based on follow type."""
        if self.follow_type == 'following':
            return obj.following.get_followers_count()
        return obj.follower.get_followers_count()
    
    def get_following_count(self, obj):
        """Get following count based on follow type."""
        if self.follow_type == 'following':
            return obj.following.get_following_count()
        return obj.follower.get_following_count()
    
    def get_is_following(self, obj):
        """Check if current user is following this user."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        target_user = obj.following if self.follow_type == 'following' else obj.follower
        return request.user.is_following(target_user)


class UserSocialProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile with social information.
    """
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    avatar_url = serializers.CharField(source='get_avatar_url', read_only=True)
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    posts_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    is_followed_by = serializers.SerializerMethodField()
    mutual_followers_count = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = (
            'user_id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'bio', 'avatar', 'avatar_url', 'website', 'location', 'birth_date',
            'is_email_verified', 'created_at', 'updated_at',
            'followers_count', 'following_count', 'posts_count',
            'is_following', 'is_followed_by', 'mutual_followers_count'
        )
        read_only_fields = (
            'user_id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'avatar_url', 'is_email_verified', 'created_at', 'updated_at',
            'followers_count', 'following_count', 'posts_count',
            'is_following', 'is_followed_by', 'mutual_followers_count'
        )
    
    def get_followers_count(self, obj):
        """Get followers count for this user."""
        return obj.user.get_followers_count()
    
    def get_following_count(self, obj):
        """Get following count for this user."""
        return obj.user.get_following_count()
    
    def get_posts_count(self, obj):
        """Get published posts count for this user."""
        return obj.user.posts.filter(status='published').count()
    
    def get_is_following(self, obj):
        """Check if current user is following this user."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return request.user.is_following(obj.user)
    
    def get_is_followed_by(self, obj):
        """Check if this user is followed by current user."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.user.is_followed_by(request.user)
    
    def get_mutual_followers_count(self, obj):
        """Get mutual followers count between current user and this user."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        return request.user.get_mutual_followers(obj.user).count()


class FollowActionSerializer(serializers.Serializer):
    """
    Serializer for follow/unfollow actions.
    """
    user_id = serializers.IntegerField()
    action = serializers.ChoiceField(choices=['follow', 'unfollow'])
    
    def validate_user_id(self, value):
        """Validate that the user exists and is active."""
        try:
            user = User.objects.get(id=value, is_active=True)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found or inactive.")
    
    def validate(self, attrs):
        """Validate that user is not trying to follow themselves."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if request.user.id == attrs['user_id']:
                raise serializers.ValidationError("Users cannot follow themselves.")
        return attrs


class SuggestedUsersSerializer(serializers.ModelSerializer):
    """
    Serializer for suggested users to follow.
    """
    user_id = serializers.IntegerField(source='id', read_only=True)
    username = serializers.CharField(read_only=True)
    full_name = serializers.CharField(source='profile.get_full_name', read_only=True)
    avatar_url = serializers.CharField(source='profile.get_avatar_url', read_only=True)
    bio = serializers.CharField(source='profile.bio', read_only=True)
    followers_count = serializers.SerializerMethodField()
    posts_count = serializers.SerializerMethodField()
    mutual_followers_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'user_id', 'username', 'full_name', 'avatar_url', 'bio',
            'followers_count', 'posts_count', 'mutual_followers_count'
        )
    
    def get_followers_count(self, obj):
        """Get followers count for this user."""
        return obj.get_followers_count()
    
    def get_posts_count(self, obj):
        """Get published posts count for this user."""
        return obj.posts.filter(status='published').count()
    
    def get_mutual_followers_count(self, obj):
        """Get mutual followers count between current user and this user."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        return request.user.get_mutual_followers(obj).count()