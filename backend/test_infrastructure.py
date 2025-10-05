#!/usr/bin/env python
"""
Simple script to test the enhanced infrastructure setup.
Run this after starting the Docker containers to verify everything is working.
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog_manager.settings.development')
django.setup()

def test_redis_connection():
    """Test Redis connection"""
    try:
        from django.core.cache import cache
        cache.set('test_key', 'test_value', 30)
        value = cache.get('test_key')
        if value == 'test_value':
            print("✅ Redis connection: SUCCESS")
            return True
        else:
            print("❌ Redis connection: FAILED - Value mismatch")
            return False
    except Exception as e:
        print(f"❌ Redis connection: FAILED - {str(e)}")
        return False

def test_celery_connection():
    """Test Celery broker connection"""
    try:
        from celery import current_app
        inspect = current_app.control.inspect()
        stats = inspect.stats()
        if stats:
            print("✅ Celery broker connection: SUCCESS")
            return True
        else:
            print("⚠️  Celery broker connection: No workers found (this is expected if workers aren't running)")
            return True
    except Exception as e:
        print(f"❌ Celery broker connection: FAILED - {str(e)}")
        return False

def test_media_directory():
    """Test media directory setup"""
    try:
        media_root = settings.MEDIA_ROOT
        if os.path.exists(media_root) or os.access(os.path.dirname(media_root), os.W_OK):
            print("✅ Media directory setup: SUCCESS")
            return True
        else:
            print(f"❌ Media directory setup: FAILED - Cannot access {media_root}")
            return False
    except Exception as e:
        print(f"❌ Media directory setup: FAILED - {str(e)}")
        return False

def test_database_connection():
    """Test database connection"""
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result[0] == 1:
                print("✅ Database connection: SUCCESS")
                return True
            else:
                print("❌ Database connection: FAILED - Unexpected result")
                return False
    except Exception as e:
        print(f"❌ Database connection: FAILED - {str(e)}")
        return False

def main():
    print("Testing Enhanced Infrastructure Setup")
    print("=" * 40)
    
    tests = [
        test_database_connection,
        test_redis_connection,
        test_celery_connection,
        test_media_directory,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 40)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All infrastructure tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())