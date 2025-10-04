"""
Management command to create test posts for performance testing.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from posts.models import Post
import random


class Command(BaseCommand):
    help = 'Create test posts for performance testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Number of test posts to create (default: 100)'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Sample data for generating posts
        titles = [
            "Understanding Django Performance",
            "React Optimization Techniques",
            "Database Indexing Best Practices",
            "Frontend Caching Strategies",
            "Docker Container Optimization",
            "API Response Time Improvement",
            "Memory Management in Python",
            "JavaScript Performance Tips",
            "PostgreSQL Query Optimization",
            "Web Application Scaling"
        ]
        
        authors = [
            "John Doe",
            "Jane Smith",
            "Bob Johnson",
            "Alice Brown",
            "Charlie Wilson",
            "Diana Davis",
            "Eve Miller",
            "Frank Garcia",
            "Grace Lee",
            "Henry Taylor"
        ]
        
        tags_options = [
            "performance, optimization",
            "django, python, backend",
            "react, frontend, javascript",
            "database, postgresql, sql",
            "docker, containers, devops",
            "api, rest, web services",
            "caching, redis, memcached",
            "testing, automation, ci/cd",
            "security, authentication, authorization",
            "monitoring, logging, debugging"
        ]
        
        content_templates = [
            "This is a comprehensive guide about {}. It covers various aspects including implementation details, best practices, and common pitfalls to avoid. The content is designed to help developers understand the concepts better and apply them in real-world scenarios.",
            "In this article, we explore {}. We'll discuss the fundamental principles, provide practical examples, and share insights from industry experts. This knowledge will help you make informed decisions in your development projects.",
            "Learn about {} in this detailed tutorial. We'll walk through step-by-step instructions, explain the underlying concepts, and provide code examples that you can use in your own projects. This guide is suitable for both beginners and experienced developers.",
            "This post discusses the importance of {} in modern web development. We'll examine current trends, analyze different approaches, and provide recommendations based on real-world experience. The information presented here will help you stay up-to-date with industry standards.",
            "Discover the secrets of {} with this in-depth analysis. We'll cover advanced techniques, performance considerations, and scalability factors that are crucial for building robust applications. This content is based on extensive research and practical experience."
        ]
        
        self.stdout.write(f'Creating {count} test posts...')
        
        posts_created = 0
        for i in range(count):
            title_base = random.choice(titles)
            title = f"{title_base} - Part {i + 1}"
            author = random.choice(authors)
            tags = random.choice(tags_options)
            content_template = random.choice(content_templates)
            content = content_template.format(title_base.lower())
            
            # Add some variation to content length
            if random.random() > 0.5:
                content += f"\n\nAdditional insights: {content[:100]}..."
            
            try:
                post = Post.objects.create(
                    title=title,
                    content=content,
                    author=author,
                    tags=tags,
                    image_url=f"https://picsum.photos/400/300?random={i}" if random.random() > 0.7 else ""
                )
                posts_created += 1
                
                if posts_created % 10 == 0:
                    self.stdout.write(f'Created {posts_created} posts...')
                    
            except Exception as e:
                self.stderr.write(f'Error creating post {i + 1}: {e}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {posts_created} test posts')
        )