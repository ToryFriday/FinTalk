# FinTalk Enhanced Blog Platform - Development Guide

## Overview

This guide provides comprehensive instructions for setting up and developing the FinTalk Enhanced Blog Platform locally. It covers both Docker-based development (recommended) and native development setups.

## Prerequisites

### System Requirements

**Minimum Requirements:**
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 10GB free space
- **OS**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 20.04+)

**Recommended for Development:**
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 20GB+ SSD
- **OS**: Latest stable versions

### Required Software

**For Docker Development (Recommended):**
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+
- **Git**: Latest version
- **Code Editor**: VS Code, PyCharm, or similar

**For Native Development:**
- **Node.js**: Version 18+
- **Python**: Version 3.11+
- **PostgreSQL**: Version 15+
- **Redis**: Version 7+
- **Git**: Latest version

## Quick Start with Docker

### 1. Clone Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/fintalk-enhanced-blog.git
cd fintalk-enhanced-blog

# Check project structure
ls -la
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit environment variables (optional for development)
# The default values work for Docker development
```

**Default Development Environment (`.env`):**
```bash
# Database Configuration
DB_NAME=fintalk_dev
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

# Django Configuration
SECRET_KEY=dev-secret-key-change-in-production
DEBUG=True
DJANGO_SETTINGS_MODULE=blog_manager.settings.development

# CORS Configuration
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_DISQUS_SHORTNAME=your-disqus-shortname

# Email Configuration (for development)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Redis Configuration
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### 3. Start Development Environment

```bash
# Start all services
docker-compose up

# Or start in background
docker-compose up -d

# View logs
docker-compose logs -f
```

### 4. Initialize Database

```bash
# Run database migrations
docker-compose exec backend python manage.py migrate

# Create superuser account
docker-compose exec backend python manage.py createsuperuser

# Load sample data (optional)
docker-compose exec backend python manage.py loaddata sample_data.json
```

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/
- **Django Admin**: http://localhost:8000/admin/
- **Database**: localhost:5432 (postgres/postgres)

## Native Development Setup

### Backend Setup

#### 1. Python Environment

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

#### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

#### 3. Database Setup

```bash
# Install PostgreSQL (if not already installed)
# On Ubuntu:
sudo apt install postgresql postgresql-contrib
# On macOS:
brew install postgresql
# On Windows: Download from postgresql.org

# Create database
sudo -u postgres createdb fintalk_dev

# Create database user
sudo -u postgres psql
CREATE USER fintalk_user WITH PASSWORD 'fintalk_password';
GRANT ALL PRIVILEGES ON DATABASE fintalk_dev TO fintalk_user;
\q
```

#### 4. Redis Setup

```bash
# Install Redis
# On Ubuntu:
sudo apt install redis-server
# On macOS:
brew install redis
# On Windows: Use Docker or WSL

# Start Redis
redis-server
```

#### 5. Environment Configuration

```bash
# Create local environment file
cp .env.example .env

# Edit for native development
nano .env
```

**Native Development Environment:**
```bash
# Database Configuration
DB_NAME=fintalk_dev
DB_USER=fintalk_user
DB_PASSWORD=fintalk_password
DB_HOST=localhost
DB_PORT=5432

# Django Configuration
SECRET_KEY=your-development-secret-key
DEBUG=True
DJANGO_SETTINGS_MODULE=blog_manager.settings.development

# CORS Configuration
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8000

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

#### 6. Database Migration

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data
python manage.py loaddata fixtures/sample_data.json
```

#### 7. Start Backend Services

```bash
# Terminal 1: Django development server
python manage.py runserver

# Terminal 2: Celery worker
celery -A blog_manager worker -l info

# Terminal 3: Celery beat scheduler
celery -A blog_manager beat -l info
```

### Frontend Setup

#### 1. Node.js Environment

```bash
# Navigate to frontend directory
cd frontend

# Check Node.js version
node --version  # Should be 18+
npm --version
```

#### 2. Install Dependencies

```bash
# Install npm dependencies
npm install

# Or using yarn
yarn install
```

#### 3. Environment Configuration

```bash
# Create environment file
echo "REACT_APP_API_URL=http://localhost:8000" > .env
echo "REACT_APP_DISQUS_SHORTNAME=your-disqus-shortname" >> .env
```

#### 4. Start Development Server

```bash
# Start React development server
npm start

# Or using yarn
yarn start
```

The frontend will be available at http://localhost:3000 with hot reloading.

## Development Workflow

### Project Structure

```
fintalk-enhanced-blog/
├── backend/                    # Django application
│   ├── blog_manager/          # Django project settings
│   │   ├── settings/          # Environment-specific settings
│   │   │   ├── base.py       # Base settings
│   │   │   ├── development.py # Development settings
│   │   │   └── production.py  # Production settings
│   │   ├── urls.py           # Main URL configuration
│   │   └── wsgi.py           # WSGI application
│   ├── accounts/             # User authentication app
│   │   ├── models.py         # User profile models
│   │   ├── serializers.py    # API serializers
│   │   ├── views.py          # API views
│   │   └── services.py       # Business logic
│   ├── posts/                # Blog posts app
│   │   ├── models.py         # Post models
│   │   ├── serializers.py    # API serializers
│   │   ├── views.py          # API views
│   │   └── services.py       # Business logic
│   ├── notifications/        # Email notifications app
│   ├── moderation/          # Content moderation app
│   ├── common/              # Shared utilities
│   │   ├── exceptions.py    # Custom exceptions
│   │   ├── permissions.py   # Custom permissions
│   │   ├── pagination.py    # Pagination utilities
│   │   └── security.py      # Security utilities
│   ├── requirements.txt     # Python dependencies
│   └── manage.py           # Django management script
├── frontend/               # React application
│   ├── src/
│   │   ├── components/     # React components
│   │   │   ├── auth/      # Authentication components
│   │   │   ├── posts/     # Post-related components
│   │   │   ├── social/    # Social feature components
│   │   │   └── common/    # Shared components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API service layer
│   │   ├── hooks/         # Custom React hooks
│   │   ├── utils/         # Utility functions
│   │   └── styles/        # CSS and styling
│   ├── public/            # Static assets
│   └── package.json       # Node.js dependencies
├── documentation/         # Project documentation
├── docker-compose.yml     # Development Docker configuration
├── docker-compose.prod.yml # Production Docker configuration
└── .env.example          # Environment variables template
```

### Git Workflow

#### Branch Strategy

```bash
# Main branches
main                    # Production-ready code
develop                # Integration branch for features

# Feature branches
feature/user-auth      # New feature development
feature/social-features
bugfix/login-issue     # Bug fixes
hotfix/security-patch  # Critical fixes
```

#### Development Process

1. **Create Feature Branch**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/new-feature-name
   ```

2. **Make Changes**
   ```bash
   # Make your changes
   git add .
   git commit -m "Add new feature: description"
   ```

3. **Push and Create PR**
   ```bash
   git push origin feature/new-feature-name
   # Create pull request on GitHub/GitLab
   ```

4. **Code Review and Merge**
   ```bash
   # After approval, merge to develop
   git checkout develop
   git pull origin develop
   git branch -d feature/new-feature-name
   ```

### Code Style and Standards

#### Backend (Python/Django)

**Code Formatting:**
```bash
# Install development tools
pip install black isort flake8 mypy

# Format code
black .

# Sort imports
isort .

# Check code style
flake8 .

# Type checking
mypy .
```

**Style Guidelines:**
- Follow PEP 8 style guide
- Use Black for code formatting
- Maximum line length: 88 characters
- Use type hints where appropriate
- Write docstrings for all functions and classes

**Example Code Style:**
```python
from typing import List, Optional
from django.db import models
from django.contrib.auth.models import User


class Post(models.Model):
    """Blog post model with enhanced features."""
    
    title: str = models.CharField(max_length=200)
    content: str = models.TextField()
    author: User = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self) -> str:
        return self.title
    
    def get_excerpt(self, length: int = 150) -> str:
        """Get post excerpt with specified length."""
        if len(self.content) <= length:
            return self.content
        return f"{self.content[:length]}..."
```

#### Frontend (JavaScript/React)

**Code Formatting:**
```bash
# Install Prettier and ESLint
npm install --save-dev prettier eslint

# Format code
npm run format

# Check code style
npm run lint
```

**Style Guidelines:**
- Use ES6+ features
- Follow Airbnb JavaScript style guide
- Use functional components with hooks
- Use TypeScript for type safety (optional)
- Use meaningful component and variable names

**Example Code Style:**
```javascript
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { postService } from '../services/api';

const PostCard = ({ post, onSave, onLike }) => {
  const [isLiked, setIsLiked] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    setIsLiked(post.is_liked);
  }, [post.is_liked]);

  const handleLike = async () => {
    if (isLoading) return;
    
    setIsLoading(true);
    try {
      await postService.toggleLike(post.id);
      setIsLiked(!isLiked);
      onLike?.(post.id, !isLiked);
    } catch (error) {
      console.error('Failed to like post:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <article className="post-card">
      <h2 
        className="post-title"
        onClick={() => navigate(`/posts/${post.id}`)}
      >
        {post.title}
      </h2>
      <p className="post-excerpt">{post.excerpt}</p>
      <div className="post-actions">
        <button 
          onClick={handleLike}
          disabled={isLoading}
          className={`like-button ${isLiked ? 'liked' : ''}`}
        >
          {isLiked ? '❤️' : '🤍'} {post.like_count}
        </button>
      </div>
    </article>
  );
};

export default PostCard;
```

### Testing

#### Backend Testing

**Run Tests:**
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=. --cov-report=html

# Run specific test file
python -m pytest posts/tests/test_models.py

# Run tests with specific markers
python -m pytest -m "not slow"
```

**Test Structure:**
```python
import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from posts.models import Post


@pytest.mark.django_db
class TestPostModel:
    def test_create_post(self):
        """Test creating a new post."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        post = Post.objects.create(
            title='Test Post',
            content='This is test content.',
            author=user
        )
        
        assert post.title == 'Test Post'
        assert post.author == user
        assert str(post) == 'Test Post'
    
    def test_post_excerpt(self):
        """Test post excerpt generation."""
        user = User.objects.create_user(username='testuser')
        post = Post.objects.create(
            title='Test Post',
            content='A' * 200,
            author=user
        )
        
        excerpt = post.get_excerpt(50)
        assert len(excerpt) == 53  # 50 + '...'
        assert excerpt.endswith('...')
```

#### Frontend Testing

**Run Tests:**
```bash
# Run all tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run tests without watch mode
npm test -- --watchAll=false
```

**Test Structure:**
```javascript
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import PostCard from '../PostCard';

const renderWithRouter = (component) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('PostCard Component', () => {
  const mockPost = {
    id: 1,
    title: 'Test Post',
    excerpt: 'This is a test post excerpt.',
    like_count: 5,
    is_liked: false,
  };

  const mockOnLike = jest.fn();
  const mockOnSave = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders post information correctly', () => {
    renderWithRouter(
      <PostCard 
        post={mockPost} 
        onLike={mockOnLike} 
        onSave={mockOnSave} 
      />
    );

    expect(screen.getByText('Test Post')).toBeInTheDocument();
    expect(screen.getByText('This is a test post excerpt.')).toBeInTheDocument();
    expect(screen.getByText('🤍 5')).toBeInTheDocument();
  });

  test('handles like button click', async () => {
    renderWithRouter(
      <PostCard 
        post={mockPost} 
        onLike={mockOnLike} 
        onSave={mockOnSave} 
      />
    );

    const likeButton = screen.getByRole('button', { name: /🤍 5/ });
    fireEvent.click(likeButton);

    await waitFor(() => {
      expect(mockOnLike).toHaveBeenCalledWith(1, true);
    });
  });
});
```

### Database Management

#### Migrations

```bash
# Create new migration
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations

# Rollback migration
python manage.py migrate posts 0001

# Create empty migration
python manage.py makemigrations --empty posts
```

#### Database Operations

```bash
# Access database shell
python manage.py dbshell

# Django shell
python manage.py shell

# Create database backup
pg_dump fintalk_dev > backup.sql

# Restore database
psql fintalk_dev < backup.sql

# Reset database (development only)
python manage.py flush
```

### API Development

#### Creating New Endpoints

1. **Define Model** (if needed):
```python
# models.py
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
```

2. **Create Serializer**:
```python
# serializers.py
class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'content', 'author_name', 'created_at']
        read_only_fields = ['author']
```

3. **Implement View**:
```python
# views.py
class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        post_id = self.kwargs['post_id']
        return Comment.objects.filter(post_id=post_id)
    
    def perform_create(self, serializer):
        post_id = self.kwargs['post_id']
        serializer.save(
            author=self.request.user,
            post_id=post_id
        )
```

4. **Add URL Pattern**:
```python
# urls.py
urlpatterns = [
    path('posts/<int:post_id>/comments/', CommentListCreateView.as_view()),
]
```

5. **Write Tests**:
```python
# tests.py
def test_create_comment(self):
    response = self.client.post(
        f'/api/posts/{self.post.id}/comments/',
        {'content': 'Test comment'},
        format='json'
    )
    assert response.status_code == 201
```

### Frontend Development

#### Creating New Components

1. **Component Structure**:
```javascript
// components/comments/CommentList.jsx
import React, { useState, useEffect } from 'react';
import { commentService } from '../../services/api';
import CommentCard from './CommentCard';
import CommentForm from './CommentForm';

const CommentList = ({ postId }) => {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadComments();
  }, [postId]);

  const loadComments = async () => {
    try {
      const data = await commentService.getComments(postId);
      setComments(data.results);
    } catch (error) {
      console.error('Failed to load comments:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCommentAdded = (newComment) => {
    setComments([newComment, ...comments]);
  };

  if (loading) return <div>Loading comments...</div>;

  return (
    <div className="comment-list">
      <CommentForm postId={postId} onCommentAdded={handleCommentAdded} />
      {comments.map(comment => (
        <CommentCard key={comment.id} comment={comment} />
      ))}
    </div>
  );
};

export default CommentList;
```

2. **API Service**:
```javascript
// services/api.js
export const commentService = {
  getComments: async (postId) => {
    const response = await api.get(`/posts/${postId}/comments/`);
    return response.data;
  },

  createComment: async (postId, content) => {
    const response = await api.post(`/posts/${postId}/comments/`, {
      content
    });
    return response.data;
  },
};
```

3. **Styling**:
```css
/* styles/components/CommentList.css */
.comment-list {
  margin-top: 2rem;
}

.comment-card {
  border: 1px solid #e1e5e9;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.comment-author {
  font-weight: bold;
  color: #2c3e50;
}

.comment-content {
  margin: 0.5rem 0;
  line-height: 1.6;
}

.comment-date {
  font-size: 0.875rem;
  color: #6c757d;
}
```

### Performance Optimization

#### Backend Optimization

**Database Queries:**
```python
# Use select_related for foreign keys
posts = Post.objects.select_related('author').all()

# Use prefetch_related for many-to-many
posts = Post.objects.prefetch_related('tags').all()

# Use only() to limit fields
posts = Post.objects.only('title', 'created_at').all()

# Use defer() to exclude fields
posts = Post.objects.defer('content').all()
```

**Caching:**
```python
from django.core.cache import cache

def get_popular_posts():
    cache_key = 'popular_posts'
    posts = cache.get(cache_key)
    
    if posts is None:
        posts = Post.objects.filter(
            view_count__gte=100
        ).order_by('-view_count')[:10]
        cache.set(cache_key, posts, 300)  # 5 minutes
    
    return posts
```

#### Frontend Optimization

**Code Splitting:**
```javascript
import { lazy, Suspense } from 'react';

const PostEditor = lazy(() => import('./components/posts/PostEditor'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <PostEditor />
    </Suspense>
  );
}
```

**Memoization:**
```javascript
import { useMemo, useCallback } from 'react';

const PostList = ({ posts, searchTerm }) => {
  const filteredPosts = useMemo(() => {
    return posts.filter(post => 
      post.title.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [posts, searchTerm]);

  const handlePostClick = useCallback((postId) => {
    navigate(`/posts/${postId}`);
  }, [navigate]);

  return (
    <div>
      {filteredPosts.map(post => (
        <PostCard 
          key={post.id} 
          post={post} 
          onClick={handlePostClick}
        />
      ))}
    </div>
  );
};
```

### Debugging

#### Backend Debugging

**Django Debug Toolbar:**
```bash
pip install django-debug-toolbar
```

```python
# settings/development.py
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']
```

**Logging:**
```python
import logging

logger = logging.getLogger(__name__)

def my_view(request):
    logger.debug('Processing request for user: %s', request.user)
    logger.info('User %s accessed view', request.user.username)
    logger.warning('Potential issue detected')
    logger.error('Error occurred: %s', str(error))
```

#### Frontend Debugging

**React Developer Tools:**
- Install browser extension
- Inspect component state and props
- Profile component performance

**Console Debugging:**
```javascript
// Debug API calls
console.log('API request:', requestData);
console.log('API response:', responseData);

// Debug component state
console.log('Component state:', state);
console.log('Props:', props);

// Performance debugging
console.time('Component render');
// ... component logic
console.timeEnd('Component render');
```

### Deployment Preparation

#### Environment Configuration

```bash
# Create production environment file
cp .env.example .env.production

# Update production values
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

#### Build Process

```bash
# Backend: Collect static files
python manage.py collectstatic --noinput

# Frontend: Build production bundle
npm run build

# Docker: Build production images
docker-compose -f docker-compose.prod.yml build
```

#### Pre-deployment Checklist

- [ ] All tests passing
- [ ] Code reviewed and approved
- [ ] Environment variables configured
- [ ] Database migrations ready
- [ ] Static files collected
- [ ] Security settings verified
- [ ] Performance optimizations applied
- [ ] Monitoring configured
- [ ] Backup procedures tested

### Troubleshooting

#### Common Development Issues

**Docker Issues:**
```bash
# Container won't start
docker-compose logs backend

# Port conflicts
docker-compose down
sudo lsof -i :8000
kill -9 <PID>

# Volume issues
docker-compose down -v
docker-compose up --build
```

**Database Issues:**
```bash
# Connection refused
docker-compose exec db pg_isready -U postgres

# Migration conflicts
python manage.py migrate --fake-initial
python manage.py migrate
```

**Frontend Issues:**
```bash
# Module not found
rm -rf node_modules package-lock.json
npm install

# CORS errors
# Check CORS_ALLOWED_ORIGINS in backend settings
```

### Resources and Documentation

#### Official Documentation
- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [React Documentation](https://reactjs.org/docs/)
- [Docker Documentation](https://docs.docker.com/)

#### Development Tools
- [Django Debug Toolbar](https://django-debug-toolbar.readthedocs.io/)
- [React Developer Tools](https://react.dev/learn/react-developer-tools)
- [Postman](https://www.postman.com/) for API testing
- [pgAdmin](https://www.pgadmin.org/) for database management

#### Community Resources
- [Django Community](https://www.djangoproject.com/community/)
- [React Community](https://reactjs.org/community/support.html)
- [Stack Overflow](https://stackoverflow.com/) for troubleshooting
- [GitHub Issues](https://github.com/yourusername/fintalk-enhanced-blog/issues) for project-specific issues

---

This development guide provides a comprehensive foundation for working with the FinTalk Enhanced Blog Platform. For additional help or questions, please refer to the other documentation files or create an issue in the project repository.