"""
Management command to set up default roles and permissions for RBAC system.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from accounts.models import Role


class Command(BaseCommand):
    help = 'Set up default roles and permissions for RBAC system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset existing roles and recreate them',
        )
    
    def handle(self, *args, **options):
        """
        Set up default roles and permissions.
        """
        self.stdout.write(self.style.SUCCESS('Setting up RBAC roles and permissions...'))
        
        try:
            with transaction.atomic():
                if options['reset']:
                    self.stdout.write('Resetting existing roles...')
                    Role.objects.all().delete()
                
                # Create default roles
                self._create_roles()
                
                # Assign permissions to roles
                self._assign_permissions()
                
                self.stdout.write(
                    self.style.SUCCESS('Successfully set up RBAC roles and permissions!')
                )
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error setting up roles: {str(e)}')
            )
    
    def _create_roles(self):
        """
        Create default roles.
        """
        roles_data = [
            {
                'name': 'admin',
                'display_name': 'Administrator',
                'description': 'Full system access with user and role management capabilities. Can manage all content, users, and system settings.'
            },
            {
                'name': 'editor',
                'display_name': 'Editor',
                'description': 'Content moderation and writer management. Can review, edit, and moderate all content, manage writers, and handle content flags.'
            },
            {
                'name': 'writer',
                'display_name': 'Writer',
                'description': 'Content creation and management. Can create, edit, and publish articles, manage drafts, and schedule posts.'
            },
            {
                'name': 'reader',
                'display_name': 'Reader',
                'description': 'Content consumption and interaction. Can read articles, save posts, follow writers, and participate in discussions.'
            },
            {
                'name': 'guest',
                'display_name': 'Guest',
                'description': 'Limited read-only access. Can view published articles without interaction features.'
            }
        ]
        
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={
                    'display_name': role_data['display_name'],
                    'description': role_data['description']
                }
            )
            
            if created:
                self.stdout.write(f'Created role: {role.display_name}')
            else:
                self.stdout.write(f'Role already exists: {role.display_name}')
    
    def _assign_permissions(self):
        """
        Assign permissions to roles based on role hierarchy.
        """
        # Get all roles
        admin_role = Role.objects.get(name='admin')
        editor_role = Role.objects.get(name='editor')
        writer_role = Role.objects.get(name='writer')
        reader_role = Role.objects.get(name='reader')
        guest_role = Role.objects.get(name='guest')
        
        # Get content types
        user_ct = ContentType.objects.get_for_model(User)
        role_ct = ContentType.objects.get_for_model(Role)
        
        # Create custom permissions if they don't exist
        custom_permissions = [
            # Role management permissions
            ('can_manage_roles', 'Can manage user roles', role_ct),
            ('can_assign_roles', 'Can assign roles to users', role_ct),
            ('can_view_role_management', 'Can view role management interface', role_ct),
            
            # User management permissions
            ('can_manage_users', 'Can manage user accounts', user_ct),
            ('can_view_user_list', 'Can view user list', user_ct),
            ('can_moderate_users', 'Can moderate user accounts', user_ct),
            
            # Content permissions (will be added when posts app is extended)
            # These will be created by the posts app
        ]
        
        for codename, name, content_type in custom_permissions:
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                content_type=content_type,
                defaults={'name': name}
            )
            if created:
                self.stdout.write(f'Created permission: {name}')
        
        # Assign permissions to roles
        self._assign_admin_permissions(admin_role)
        self._assign_editor_permissions(editor_role)
        self._assign_writer_permissions(writer_role)
        self._assign_reader_permissions(reader_role)
        self._assign_guest_permissions(guest_role)
    
    def _assign_admin_permissions(self, role):
        """
        Assign all permissions to admin role.
        """
        # Admins get all permissions
        all_permissions = Permission.objects.all()
        role.permissions.set(all_permissions)
        self.stdout.write(f'Assigned {all_permissions.count()} permissions to {role.display_name}')
    
    def _assign_editor_permissions(self, role):
        """
        Assign editor-specific permissions.
        """
        permission_codenames = [
            # Role management (limited)
            'can_assign_roles',
            'can_view_role_management',
            
            # User management
            'can_view_user_list',
            'can_moderate_users',
            
            # Auth permissions
            'view_user',
            
            # Content permissions (to be added by posts app)
            # 'can_moderate_posts',
            # 'can_review_flags',
            # 'can_manage_writers',
        ]
        
        permissions = Permission.objects.filter(codename__in=permission_codenames)
        role.permissions.set(permissions)
        self.stdout.write(f'Assigned {permissions.count()} permissions to {role.display_name}')
    
    def _assign_writer_permissions(self, role):
        """
        Assign writer-specific permissions.
        """
        permission_codenames = [
            # Basic user permissions
            'view_user',
            
            # Content permissions (to be added by posts app)
            # 'add_post',
            # 'change_post',
            # 'can_create_drafts',
            # 'can_schedule_posts',
        ]
        
        permissions = Permission.objects.filter(codename__in=permission_codenames)
        role.permissions.set(permissions)
        self.stdout.write(f'Assigned {permissions.count()} permissions to {role.display_name}')
    
    def _assign_reader_permissions(self, role):
        """
        Assign reader-specific permissions.
        """
        permission_codenames = [
            # Basic view permissions
            'view_user',
            
            # Content permissions (to be added by posts app)
            # 'view_post',
            # 'can_save_posts',
            # 'can_follow_users',
            # 'can_subscribe_email',
        ]
        
        permissions = Permission.objects.filter(codename__in=permission_codenames)
        role.permissions.set(permissions)
        self.stdout.write(f'Assigned {permissions.count()} permissions to {role.display_name}')
    
    def _assign_guest_permissions(self, role):
        """
        Assign guest-specific permissions (minimal).
        """
        permission_codenames = [
            # Very limited permissions
            # 'view_post',  # Will be added by posts app
        ]
        
        permissions = Permission.objects.filter(codename__in=permission_codenames)
        role.permissions.set(permissions)
        self.stdout.write(f'Assigned {permissions.count()} permissions to {role.display_name}')