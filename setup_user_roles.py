#!/usr/bin/env python3
"""
Script to set up user roles for the blog platform.
"""
import os
import sys
import django

# Add the backend directory to the Python path
sys.path.append('backend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog_manager.settings.development')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Role, UserRole

def setup_roles():
    """Create basic roles for the blog platform."""
    
    print("🔧 Setting up User Roles")
    print("=" * 30)
    
    # Create basic roles
    roles_to_create = [
        {
            'name': 'admin',
            'description': 'Full administrative access to all features',
            'permissions': ['can_manage_users', 'can_moderate_posts', 'can_publish_posts', 'can_delete_posts']
        },
        {
            'name': 'editor',
            'description': 'Can edit, publish, and moderate posts',
            'permissions': ['can_moderate_posts', 'can_publish_posts', 'can_edit_all_posts']
        },
        {
            'name': 'writer',
            'description': 'Can create and edit own posts',
            'permissions': ['can_create_posts', 'can_edit_own_posts']
        }
    ]
    
    print("\n1️⃣ Creating roles...")
    for role_data in roles_to_create:
        role, created = Role.objects.get_or_create(
            name=role_data['name'],
            defaults={
                'description': role_data['description'],
                'permissions': role_data['permissions']
            }
        )
        
        if created:
            print(f"   ✅ Created role: {role.name}")
        else:
            print(f"   ℹ️ Role already exists: {role.name}")
    
    # Assign roles to test users
    print("\n2️⃣ Assigning roles to test users...")
    
    user_role_assignments = [
        ('admin', 'admin'),
        ('testuser', 'writer'),
        ('author', 'writer'),
    ]
    
    for username, role_name in user_role_assignments:
        try:
            user = User.objects.get(username=username)
            role = Role.objects.get(name=role_name)
            
            user_role, created = UserRole.objects.get_or_create(
                user=user,
                role=role
            )
            
            if created:
                print(f"   ✅ Assigned {role_name} role to {username}")
            else:
                print(f"   ℹ️ {username} already has {role_name} role")
                
        except User.DoesNotExist:
            print(f"   ❌ User {username} not found")
        except Role.DoesNotExist:
            print(f"   ❌ Role {role_name} not found")
    
    # Verify assignments
    print("\n3️⃣ Verifying role assignments...")
    for user in User.objects.all():
        roles = [ur.role.name for ur in user.user_roles.all()]
        print(f"   {user.username}: {roles if roles else 'No roles'}")
    
    print("\n✅ Role setup completed!")

if __name__ == "__main__":
    setup_roles()