# Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Blog Post Manager application in various environments, from development to production. The application is designed to be deployed using Docker containers for consistency and scalability.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Development Deployment](#development-deployment)
- [Production Deployment](#production-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)

## Prerequisites

### System Requirements

**Minimum Requirements:**
- CPU: 2 cores
- RAM: 4GB
- Storage: 10GB free space
- OS: Linux (Ubuntu 20.04+), macOS 10.15+, or Windows 10+

**Recommended for Production:**
- CPU: 4+ cores
- RAM: 8GB+
- Storage: 50GB+ SSD
- OS: Linux (Ubuntu 22.04 LTS)

### Software Dependencies

**Required:**
- Docker 20.10+
- Docker Compose 2.0+
- Git

**Optional (for local development):**
- Node.js 18+
- Python 3.11+
- PostgreSQL 15+

### Network Requirements

**Ports:**
- 80 (HTTP)
- 443 (HTTPS)
- 3000 (Frontend development)
- 8000 (Backend development)
- 5432 (PostgreSQL)

## Environment Configuration

### Environment Variables

Create environment configuration files based on your deployment target:

#### Development Environment (.env)
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
```

#### Production Environment (.env)
```bash
# Database Configuration
DB_NAME=fintalk_prod
DB_USER=your_db_user
DB_PASSWORD=your_secure_db_password
DB_HOST=db
DB_PORT=5432

# Django Configuration
SECRET_KEY=your-very-secure-secret-key-here
DEBUG=False
DJANGO_SETTINGS_MODULE=blog_manager.settings.production

# Domain Configuration
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Frontend Configuration
REACT_APP_API_URL=https://yourdomain.com

# SSL Configuration (if using HTTPS)
SECURE_SSL_REDIRECT=True
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
```

### Security Configuration

#### Generate Secret Key
```bash
# Generate Django secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

#### Database Password
```bash
# Generate secure database password
openssl rand -base64 32
```

## Development Deployment

### Quick Start

1. **Clone Repository:**
   ```bash
   git clone <repository-url>
   cd blog-post-manager
   ```

2. **Configure Environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your development settings
   ```

3. **Start Services:**
   ```bash
   docker-compose up --build
   ```

4. **Verify Deployment:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/api/posts/
   - Admin Panel: http://localhost:8000/admin/

### Development Commands

```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# Rebuild containers
docker-compose up --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Reset database
docker-compose down -v
docker-compose up --build
```

### Database Management

```bash
# Access database container
docker-compose exec db psql -U postgres -d fintalk_dev

# Create database backup
docker-compose exec db pg_dump -U postgres fintalk_dev > backup.sql

# Restore database
docker-compose exec -T db psql -U postgres fintalk_dev < backup.sql

# Run Django migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser
```

## Production Deployment

### Pre-deployment Checklist

- [ ] Domain name configured and DNS pointing to server
- [ ] SSL certificate obtained (Let's Encrypt recommended)
- [ ] Environment variables configured
- [ ] Database backup strategy implemented
- [ ] Monitoring tools configured
- [ ] Log rotation configured
- [ ] Firewall rules configured

### Server Setup

#### Ubuntu 22.04 LTS Setup

1. **Update System:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install Docker:**
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   
   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   
   # Add user to docker group
   sudo usermod -aG docker $USER
   newgrp docker
   ```

3. **Configure Firewall:**
   ```bash
   sudo ufw allow ssh
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw enable
   ```

### Production Deployment Steps

1. **Clone and Configure:**
   ```bash
   git clone <repository-url>
   cd blog-post-manager
   cp .env.example .env
   # Edit .env with production values
   ```

2. **Deploy Application:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

3. **Initialize Database:**
   ```bash
   # Run migrations
   docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate
   
   # Collect static files
   docker-compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
   
   # Create superuser
   docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
   ```

4. **Verify Deployment:**
   ```bash
   # Check service status
   docker-compose -f docker-compose.prod.yml ps
   
   # Check logs
   docker-compose -f docker-compose.prod.yml logs
   
   # Test endpoints
   curl -I http://yourdomain.com
   curl http://yourdomain.com/api/posts/
   ```

### SSL/HTTPS Configuration

#### Using Let's Encrypt with Certbot

1. **Install Certbot:**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   ```

2. **Obtain Certificate:**
   ```bash
   sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
   ```

3. **Update Nginx Configuration:**
   ```nginx
   # nginx.conf
   server {
       listen 80;
       server_name yourdomain.com www.yourdomain.com;
       return 301 https://$server_name$request_uri;
   }
   
   server {
       listen 443 ssl http2;
       server_name yourdomain.com www.yourdomain.com;
       
       ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
       
       # SSL configuration
       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
       ssl_prefer_server_ciphers off;
       
       # Security headers
       add_header Strict-Transport-Security "max-age=63072000" always;
       add_header X-Frame-Options DENY;
       add_header X-Content-Type-Options nosniff;
       
       # Application configuration
       location / {
           proxy_pass http://frontend:80;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
       
       location /api/ {
           proxy_pass http://backend:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
       
       location /static/ {
           alias /var/www/static/;
           expires 1y;
           add_header Cache-Control "public, immutable";
       }
   }
   ```

4. **Auto-renewal Setup:**
   ```bash
   # Test renewal
   sudo certbot renew --dry-run
   
   # Add to crontab
   echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
   ```

### Production Optimization

#### Docker Optimization

1. **Multi-stage Builds:**
   ```dockerfile
   # Already implemented in Dockerfile.prod
   FROM node:18-alpine AS build
   # Build stage
   
   FROM nginx:alpine AS production
   # Production stage
   ```

2. **Resource Limits:**
   ```yaml
   # docker-compose.prod.yml
   services:
     backend:
       deploy:
         resources:
           limits:
             memory: 1G
             cpus: '0.5'
           reservations:
             memory: 512M
             cpus: '0.25'
   ```

#### Database Optimization

1. **PostgreSQL Configuration:**
   ```bash
   # Create custom postgresql.conf
   cat > postgresql.conf << EOF
   shared_buffers = 256MB
   effective_cache_size = 1GB
   maintenance_work_mem = 64MB
   checkpoint_completion_target = 0.9
   wal_buffers = 16MB
   default_statistics_target = 100
   random_page_cost = 1.1
   effective_io_concurrency = 200
   EOF
   ```

2. **Connection Pooling:**
   ```python
   # settings/production.py
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'CONN_MAX_AGE': 600,
           'OPTIONS': {
               'MAX_CONNS': 20,
           }
       }
   }
   ```

## Cloud Deployment

### AWS Deployment

#### Using AWS ECS with Fargate

1. **Create ECR Repositories:**
   ```bash
   aws ecr create-repository --repository-name blog-manager-frontend
   aws ecr create-repository --repository-name blog-manager-backend
   ```

2. **Build and Push Images:**
   ```bash
   # Get login token
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
   
   # Build and tag images
   docker build -f frontend/Dockerfile.prod -t blog-manager-frontend frontend/
   docker tag blog-manager-frontend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/blog-manager-frontend:latest
   
   # Push images
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/blog-manager-frontend:latest
   ```

3. **Create ECS Task Definition:**
   ```json
   {
     "family": "blog-manager",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "512",
     "memory": "1024",
     "containerDefinitions": [
       {
         "name": "frontend",
         "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/blog-manager-frontend:latest",
         "portMappings": [
           {
             "containerPort": 80,
             "protocol": "tcp"
           }
         ]
       }
     ]
   }
   ```

#### Using AWS RDS for Database

1. **Create RDS Instance:**
   ```bash
   aws rds create-db-instance \
     --db-instance-identifier blog-manager-db \
     --db-instance-class db.t3.micro \
     --engine postgres \
     --master-username postgres \
     --master-user-password <secure-password> \
     --allocated-storage 20 \
     --vpc-security-group-ids sg-xxxxxxxx
   ```

### Google Cloud Platform

#### Using Cloud Run

1. **Build and Deploy:**
   ```bash
   # Build with Cloud Build
   gcloud builds submit --tag gcr.io/PROJECT-ID/blog-manager-frontend frontend/
   
   # Deploy to Cloud Run
   gcloud run deploy blog-manager-frontend \
     --image gcr.io/PROJECT-ID/blog-manager-frontend \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

### Digital Ocean

#### Using App Platform

1. **Create App Spec:**
   ```yaml
   name: blog-manager
   services:
   - name: frontend
     source_dir: /frontend
     github:
       repo: your-username/blog-post-manager
       branch: main
     run_command: npm start
     environment_slug: node-js
     instance_count: 1
     instance_size_slug: basic-xxs
   - name: backend
     source_dir: /backend
     github:
       repo: your-username/blog-post-manager
       branch: main
     run_command: gunicorn blog_manager.wsgi:application
     environment_slug: python
     instance_count: 1
     instance_size_slug: basic-xxs
   databases:
   - name: db
     engine: PG
     version: "15"
   ```

## Monitoring and Maintenance

### Health Checks

#### Application Health Endpoints

```python
# backend/blog_manager/urls.py
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0'
    })

urlpatterns = [
    path('health/', health_check, name='health-check'),
    # ... other patterns
]
```

#### Docker Health Checks

```yaml
# docker-compose.prod.yml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
```

### Logging

#### Centralized Logging with ELK Stack

1. **Add Logging Configuration:**
   ```yaml
   # docker-compose.prod.yml
   services:
     elasticsearch:
       image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
       environment:
         - discovery.type=single-node
         - xpack.security.enabled=false
       
     logstash:
       image: docker.elastic.co/logstash/logstash:8.5.0
       volumes:
         - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
       
     kibana:
       image: docker.elastic.co/kibana/kibana:8.5.0
       ports:
         - "5601:5601"
   ```

#### Log Rotation

```bash
# /etc/logrotate.d/blog-manager
/var/log/blog-manager/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        docker-compose -f /path/to/docker-compose.prod.yml restart backend
    endscript
}
```

### Backup Strategy

#### Database Backups

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_NAME="fintalk_prod"

# Create backup
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U postgres $DB_NAME > $BACKUP_DIR/backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/backup_$DATE.sql

# Remove backups older than 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/backup_$DATE.sql.gz s3://your-backup-bucket/
```

#### Automated Backup Cron Job

```bash
# Add to crontab
0 2 * * * /path/to/backup.sh >> /var/log/backup.log 2>&1
```

### Performance Monitoring

#### Application Performance Monitoring

```python
# Install APM tools
pip install newrelic
pip install sentry-sdk[django]

# settings/production.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="YOUR_SENTRY_DSN",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True
)
```

#### System Monitoring

```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Monitor Docker containers
docker stats

# Monitor system resources
htop
```

## Troubleshooting

### Common Issues

#### Container Won't Start

```bash
# Check container logs
docker-compose logs backend

# Check container status
docker-compose ps

# Restart specific service
docker-compose restart backend
```

#### Database Connection Issues

```bash
# Check database container
docker-compose exec db pg_isready -U postgres

# Check database logs
docker-compose logs db

# Test connection from backend
docker-compose exec backend python manage.py dbshell
```

#### SSL Certificate Issues

```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Test SSL configuration
openssl s_client -connect yourdomain.com:443
```

### Performance Issues

#### High Memory Usage

```bash
# Check memory usage
docker stats

# Optimize Docker images
docker system prune -a

# Adjust container limits
# Edit docker-compose.prod.yml resource limits
```

#### Slow Database Queries

```python
# Enable query logging
# settings/production.py
LOGGING = {
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['file'],
        }
    }
}
```

### Recovery Procedures

#### Application Recovery

```bash
# Stop all services
docker-compose -f docker-compose.prod.yml down

# Restore from backup
docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres fintalk_prod < backup.sql

# Restart services
docker-compose -f docker-compose.prod.yml up -d
```

#### Disaster Recovery

1. **Backup Verification:**
   ```bash
   # Test backup restoration on staging
   docker-compose -f docker-compose.staging.yml up -d
   # Restore backup and verify data integrity
   ```

2. **Failover Procedures:**
   ```bash
   # Switch DNS to backup server
   # Update load balancer configuration
   # Verify application functionality
   ```

## Security Considerations

### Production Security Checklist

- [ ] Change all default passwords
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS with valid SSL certificates
- [ ] Configure proper CORS settings
- [ ] Set up firewall rules
- [ ] Enable security headers
- [ ] Regular security updates
- [ ] Monitor access logs
- [ ] Implement rate limiting
- [ ] Use secure Docker images

### Security Monitoring

```bash
# Monitor failed login attempts
grep "Failed password" /var/log/auth.log

# Monitor Docker security
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image blog-manager-backend:latest

# Monitor SSL certificate expiration
echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates
```

### Regular Maintenance Tasks

#### Weekly Tasks
- Review application logs
- Check system resource usage
- Verify backup integrity
- Update security patches

#### Monthly Tasks
- Review and rotate logs
- Update dependencies
- Performance optimization review
- Security audit

#### Quarterly Tasks
- Full system backup
- Disaster recovery testing
- Security penetration testing
- Capacity planning review

---

This deployment guide provides comprehensive instructions for deploying the Blog Post Manager application across various environments. Follow the appropriate sections based on your deployment target and requirements.