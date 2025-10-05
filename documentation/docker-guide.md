# Docker Configuration Guide

This project uses Docker and Docker Compose to containerize the full-stack blog post manager application.

## Architecture

The application consists of three main services:
- **Frontend**: React.js application served by nginx in production
- **Backend**: Django REST API with Gunicorn in production
- **Database**: PostgreSQL 15 with persistent storage

## Development Environment

### Prerequisites
- Docker and Docker Compose installed
- Git (to clone the repository)

### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd blog-post-manager

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Service URLs
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Database: localhost:5432

### Development Features
- **Hot Reload**: Frontend and backend code changes are reflected immediately
- **Volume Mounts**: Source code is mounted for live development
- **Debug Mode**: Django runs in debug mode with detailed error pages

## Production Environment

### Prerequisites
- Docker and Docker Compose installed
- Environment variables configured (see `.env.example`)

### Setup
```bash
# Copy and configure environment variables
cp .env.example .env
# Edit .env with your production values

# Start production services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

### Production Features
- **Multi-stage Builds**: Optimized Docker images for production
- **Nginx Reverse Proxy**: Handles routing and static file serving
- **Resource Limits**: Memory limits configured for each service
- **Health Checks**: All services have health monitoring
- **Security**: Non-root users, secure configurations

### Environment Variables
Required environment variables for production:
```bash
SECRET_KEY=your-secret-key-here
DB_NAME=blog_manager_prod
DB_USER=postgres
DB_PASSWORD=your-secure-password
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
REACT_APP_API_URL=https://yourdomain.com
```

## Docker Images

### Frontend Dockerfile
- **Base Stage**: Node.js 18 Alpine with production dependencies
- **Development Stage**: All dependencies for development
- **Build Stage**: Builds React application
- **Production Stage**: Nginx Alpine serving built application

### Backend Dockerfile
- **Base Stage**: Python 3.11 slim with system dependencies
- **Development Stage**: Django development server
- **Production Stage**: Gunicorn WSGI server

## Networking

### Development
- Uses Docker Compose default network
- Services communicate using service names

### Production
- Custom bridge network `blog_network`
- Nginx reverse proxy handles external traffic
- Internal service communication isolated

## Health Checks

All services include health checks:
- **Database**: `pg_isready` command
- **Backend**: HTTP request to `/api/posts/`
- **Nginx**: HTTP request to root path

## Volumes

- **postgres_data**: Persistent database storage
- **Development**: Source code mounted for live editing
- **Production**: Static files and nginx config mounted

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check if ports are in use
   netstat -an | grep :3000
   netstat -an | grep :8000
   netstat -an | grep :5432
   ```

2. **Database Connection Issues**
   ```bash
   # Check database health
   docker-compose exec db pg_isready -U postgres
   
   # View database logs
   docker-compose logs db
   ```

3. **Build Issues**
   ```bash
   # Rebuild images
   docker-compose build --no-cache
   
   # Remove old images
   docker system prune -a
   ```

### Useful Commands

```bash
# View running containers
docker-compose ps

# Execute commands in containers
docker-compose exec backend python manage.py shell
docker-compose exec db psql -U postgres -d fintalk_dev

# View resource usage
docker stats

# Clean up
docker-compose down -v  # Remove volumes
docker system prune -a  # Remove unused images
```

## Security Considerations

### Development
- Debug mode enabled
- Permissive CORS settings
- HTTP connections allowed

### Production
- Debug mode disabled
- Strict CORS configuration
- HTTPS enforcement (configure reverse proxy)
- Non-root container users
- Resource limits applied
- Security headers configured