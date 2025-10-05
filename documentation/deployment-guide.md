# FinTalk Enhanced Blog Platform - AWS EC2 Deployment Guide

## Overview

This comprehensive guide provides step-by-step instructions for deploying the FinTalk Enhanced Blog Platform on AWS EC2, from instance creation to full production deployment. This guide is specifically designed for deployment from a Windows laptop.

## Prerequisites

### Windows Laptop Requirements

- **Windows 10/11** with PowerShell or Command Prompt
- **Git for Windows** installed
- **SSH Client** (built into Windows 10/11 or PuTTY)
- **AWS CLI** (optional but recommended)
- **Text Editor** (VS Code, Notepad++, or similar)

### AWS Account Requirements

- **AWS Account** with billing enabled
- **IAM User** with EC2 permissions (recommended over root account)
- **Key Pair** for SSH access
- **Basic understanding** of AWS services

## Step 1: AWS EC2 Instance Setup

### 1.1 Create EC2 Instance

1. **Log into AWS Console**
   - Navigate to [AWS Console](https://console.aws.amazon.com/)
   - Sign in with your AWS account

2. **Navigate to EC2**
   - Search for "EC2" in the services search bar
   - Click on "EC2" to open the EC2 Dashboard

3. **Launch Instance**
   - Click "Launch Instance" button
   - Choose "Launch Instance" from dropdown

### 1.2 Configure Instance Settings

#### Instance Name and Tags
- **Name**: `fintalk-production`
- **Environment**: `production`
- **Project**: `fintalk-blog`

#### Application and OS Images (Amazon Machine Image)
- **Operating System**: Ubuntu
- **Version**: Ubuntu Server 22.04 LTS (HVM), SSD Volume Type
- **Architecture**: 64-bit (x86)
- **AMI ID**: ami-0c7217cdde317cfec (or latest Ubuntu 22.04 LTS)

#### Instance Type
**Recommended Options:**

**For Development/Testing:**
- **t3.micro** (1 vCPU, 1 GB RAM) - Free tier eligible
- **t3.small** (1 vCPU, 2 GB RAM) - Minimum recommended

**For Production:**
- **t3.medium** (2 vCPU, 4 GB RAM) - Recommended for small to medium traffic
- **t3.large** (2 vCPU, 8 GB RAM) - For higher traffic
- **t3.xlarge** (4 vCPU, 16 GB RAM) - For high traffic sites

**Select**: `t3.medium` for production deployment

#### Key Pair (Login)
1. **Create New Key Pair**:
   - Click "Create new key pair"
   - **Key pair name**: `fintalk-production-key`
   - **Key pair type**: RSA
   - **Private key file format**: `.pem` (for OpenSSH)
   - Click "Create key pair"
   - **Important**: Save the `.pem` file securely - you cannot download it again

2. **Store Key Securely**:
   - Save to: `C:\Users\YourUsername\.ssh\fintalk-production-key.pem`
   - Create the `.ssh` folder if it doesn't exist

#### Network Settings
1. **VPC**: Use default VPC (or create custom VPC if needed)
2. **Subnet**: Use default subnet (public subnet)
3. **Auto-assign public IP**: Enable
4. **Firewall (Security Groups)**:
   - **Create security group**: Yes
   - **Security group name**: `fintalk-production-sg`
   - **Description**: Security group for FinTalk production server

**Security Group Rules:**
```
Type            Protocol    Port Range    Source          Description
SSH             TCP         22           0.0.0.0/0       SSH access
HTTP            TCP         80           0.0.0.0/0       HTTP web traffic
HTTPS           TCP         443          0.0.0.0/0       HTTPS web traffic
Custom TCP      TCP         8000         0.0.0.0/0       Django development (temporary)
```

**Security Note**: For production, restrict SSH access to your IP address instead of 0.0.0.0/0

#### Configure Storage
- **Root Volume**:
  - **Size**: 20 GB (minimum) - 50 GB recommended for production
  - **Volume Type**: gp3 (General Purpose SSD)
  - **IOPS**: 3000
  - **Throughput**: 125 MB/s
  - **Encrypted**: Yes (recommended)

#### Advanced Details (Optional)
- **IAM instance profile**: None (can be added later if needed)
- **User data**: Leave empty (we'll configure manually)

### 1.3 Launch Instance

1. **Review Summary**
   - Verify all settings are correct
   - Check estimated monthly cost

2. **Launch Instance**
   - Click "Launch instance"
   - Wait for instance to launch (2-3 minutes)

3. **Note Instance Details**
   - **Instance ID**: `i-1234567890abcdef0`
   - **Public IPv4 address**: `54.123.45.67` (example)
   - **Public IPv4 DNS**: `ec2-54-123-45-67.compute-1.amazonaws.com`

## Step 2: SSH Connection from Windows

### 2.1 Using Windows Built-in SSH (Recommended)

#### Set Key Permissions
1. **Open PowerShell as Administrator**
   ```powershell
   # Navigate to your .ssh directory
   cd C:\Users\YourUsername\.ssh
   
   # Set proper permissions on the key file
   icacls fintalk-production-key.pem /inheritance:r
   icacls fintalk-production-key.pem /grant:r "%username%:R"
   ```

#### Connect to Instance
```powershell
# Replace with your actual public IP or DNS name
ssh -i "C:\Users\YourUsername\.ssh\fintalk-production-key.pem" ubuntu@54.123.45.67

# Or using DNS name
ssh -i "C:\Users\YourUsername\.ssh\fintalk-production-key.pem" ubuntu@ec2-54-123-45-67.compute-1.amazonaws.com
```

### 2.2 Using PuTTY (Alternative Method)

#### Convert PEM to PPK
1. **Download PuTTYgen**
   - Download from [PuTTY website](https://www.putty.org/)
   - Install PuTTY suite

2. **Convert Key**
   - Open PuTTYgen
   - Click "Load" and select your `.pem` file
   - Click "Save private key" and save as `.ppk` file

#### Connect with PuTTY
1. **Open PuTTY**
2. **Session Settings**:
   - **Host Name**: `ubuntu@54.123.45.67`
   - **Port**: 22
   - **Connection type**: SSH

3. **Auth Settings**:
   - Navigate to Connection → SSH → Auth
   - Browse and select your `.ppk` file

4. **Save Session**:
   - Return to Session category
   - **Saved Sessions**: `FinTalk Production`
   - Click "Save"

5. **Connect**:
   - Click "Open"
   - Accept the security alert

### 2.3 Verify Connection

Once connected, you should see:
```bash
Welcome to Ubuntu 22.04.3 LTS (GNU/Linux 6.2.0-1009-aws x86_64)

ubuntu@ip-172-31-32-123:~$
```

## Step 3: Server Initial Setup

### 3.1 Update System

```bash
# Update package list
sudo apt update

# Upgrade all packages
sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl wget git unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release
```

### 3.2 Configure Firewall

```bash
# Enable UFW firewall
sudo ufw enable

# Allow SSH (important - do this first!)
sudo ufw allow ssh

# Allow HTTP and HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Allow Django development port (temporary)
sudo ufw allow 8000

# Check firewall status
sudo ufw status
```

### 3.3 Create Application User

```bash
# Create application user
sudo adduser fintalk

# Add to sudo group
sudo usermod -aG sudo fintalk

# Switch to application user
sudo su - fintalk
```

## Step 4: Install Docker and Docker Compose

### 4.1 Install Docker

```bash
# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update package list
sudo apt update

# Install Docker
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Add user to docker group
sudo usermod -aG docker $USER
sudo usermod -aG docker fintalk

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker
```

### 4.2 Install Docker Compose

```bash
# Download Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make executable
sudo chmod +x /usr/local/bin/docker-compose

# Create symlink for easier access
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

# Verify installation
docker-compose --version
```

### 4.3 Verify Docker Installation

```bash
# Log out and back in to refresh group membership
exit
sudo su - fintalk

# Test Docker
docker run hello-world

# Test Docker Compose
docker-compose --version
```

## Step 5: Deploy Application

### 5.1 Clone Repository

```bash
# Navigate to home directory
cd /home/fintalk

# Clone the repository (replace with your actual repository URL)
git clone https://github.com/yourusername/fintalk-enhanced-blog.git

# Navigate to project directory
cd fintalk-enhanced-blog

# Check project structure
ls -la
```

### 5.2 Configure Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Edit environment file
nano .env
```

**Production Environment Configuration:**
```bash
# Database Configuration
DB_NAME=fintalk_prod
DB_USER=fintalk_user
DB_PASSWORD=your_very_secure_database_password_here
DB_HOST=db
DB_PORT=5432

# Django Configuration
SECRET_KEY=your_very_long_and_secure_secret_key_here_at_least_50_characters
DEBUG=False
DJANGO_SETTINGS_MODULE=blog_manager.settings.production

# Domain Configuration (replace with your actual domain)
ALLOWED_HOSTS=54.123.45.67,yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Frontend Configuration
REACT_APP_API_URL=https://yourdomain.com

# Email Configuration (configure with your SMTP provider)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Security Settings
SECURE_SSL_REDIRECT=False  # Set to True when SSL is configured
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# File Upload Settings
MAX_UPLOAD_SIZE=5242880  # 5MB
MEDIA_ROOT=/app/media
STATIC_ROOT=/app/staticfiles

# Disqus Configuration (optional)
REACT_APP_DISQUS_SHORTNAME=your-disqus-shortname
```

**Generate Secure Keys:**
```bash
# Generate Django secret key
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Generate database password
openssl rand -base64 32
```

### 5.3 Configure Production Docker Compose

Create or verify `docker-compose.prod.yml`:

```bash
# Check if production compose file exists
ls -la docker-compose.prod.yml

# If it doesn't exist, create it
nano docker-compose.prod.yml
```

**Production Docker Compose Configuration:**
```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - fintalk_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    networks:
      - fintalk_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_HOST=db
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=${DEBUG}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - CORS_ALLOWED_ORIGINS=${CORS_ALLOWED_ORIGINS}
      - EMAIL_HOST=${EMAIL_HOST}
      - EMAIL_PORT=${EMAIL_PORT}
      - EMAIL_USE_TLS=${EMAIL_USE_TLS}
      - EMAIL_HOST_USER=${EMAIL_HOST_USER}
      - EMAIL_HOST_PASSWORD=${EMAIL_HOST_PASSWORD}
      - REDIS_URL=${REDIS_URL}
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
      - CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND}
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    networks:
      - fintalk_network
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3

  celery:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A blog_manager worker -l info
    environment:
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_HOST=db
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=${DEBUG}
      - REDIS_URL=${REDIS_URL}
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
      - CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND}
      - EMAIL_HOST=${EMAIL_HOST}
      - EMAIL_PORT=${EMAIL_PORT}
      - EMAIL_USE_TLS=${EMAIL_USE_TLS}
      - EMAIL_HOST_USER=${EMAIL_HOST_USER}
      - EMAIL_HOST_PASSWORD=${EMAIL_HOST_PASSWORD}
    volumes:
      - media_volume:/app/media
    networks:
      - fintalk_network
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A blog_manager beat -l info
    environment:
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_HOST=db
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=${DEBUG}
      - REDIS_URL=${REDIS_URL}
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
      - CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND}
    networks:
      - fintalk_network
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
      args:
        - REACT_APP_API_URL=${REACT_APP_API_URL}
        - REACT_APP_DISQUS_SHORTNAME=${REACT_APP_DISQUS_SHORTNAME}
    networks:
      - fintalk_network
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.prod.conf:/etc/nginx/nginx.conf
      - static_volume:/var/www/static
      - media_volume:/var/www/media
      - ./ssl:/etc/nginx/ssl  # For SSL certificates
    networks:
      - fintalk_network
    depends_on:
      - backend
      - frontend
    restart: unless-stopped

volumes:
  postgres_data:
  static_volume:
  media_volume:

networks:
  fintalk_network:
    driver: bridge
```

### 5.4 Configure Nginx

Create production Nginx configuration:

```bash
nano nginx.prod.conf
```

**Nginx Production Configuration:**
```nginx
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;

    # Basic settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 10M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

    # Upstream servers
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:80;
    }

    # HTTP server (redirects to HTTPS in production)
    server {
        listen 80;
        server_name _;

        # For Let's Encrypt certificate verification
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        # Redirect all HTTP traffic to HTTPS (uncomment for production with SSL)
        # return 301 https://$server_name$request_uri;

        # Temporary: serve content over HTTP (remove when SSL is configured)
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /admin/ {
            limit_req zone=login burst=5 nodelay;
            proxy_pass http://backend;
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

        location /media/ {
            alias /var/www/media/;
            expires 1y;
            add_header Cache-Control "public";
        }
    }

    # HTTPS server (uncomment and configure when SSL certificates are ready)
    # server {
    #     listen 443 ssl http2;
    #     server_name yourdomain.com www.yourdomain.com;
    #
    #     ssl_certificate /etc/nginx/ssl/fullchain.pem;
    #     ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    #
    #     # SSL configuration
    #     ssl_protocols TLSv1.2 TLSv1.3;
    #     ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    #     ssl_prefer_server_ciphers off;
    #     ssl_session_cache shared:SSL:10m;
    #     ssl_session_timeout 10m;
    #
    #     # Security headers
    #     add_header Strict-Transport-Security "max-age=63072000" always;
    #     add_header X-Frame-Options DENY;
    #     add_header X-Content-Type-Options nosniff;
    #     add_header X-XSS-Protection "1; mode=block";
    #     add_header Referrer-Policy "strict-origin-when-cross-origin";
    #
    #     location / {
    #         proxy_pass http://frontend;
    #         proxy_set_header Host $host;
    #         proxy_set_header X-Real-IP $remote_addr;
    #         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    #         proxy_set_header X-Forwarded-Proto $scheme;
    #     }
    #
    #     location /api/ {
    #         limit_req zone=api burst=20 nodelay;
    #         proxy_pass http://backend;
    #         proxy_set_header Host $host;
    #         proxy_set_header X-Real-IP $remote_addr;
    #         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    #         proxy_set_header X-Forwarded-Proto $scheme;
    #     }
    #
    #     location /admin/ {
    #         limit_req zone=login burst=5 nodelay;
    #         proxy_pass http://backend;
    #         proxy_set_header Host $host;
    #         proxy_set_header X-Real-IP $remote_addr;
    #         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    #         proxy_set_header X-Forwarded-Proto $scheme;
    #     }
    #
    #     location /static/ {
    #         alias /var/www/static/;
    #         expires 1y;
    #         add_header Cache-Control "public, immutable";
    #     }
    #
    #     location /media/ {
    #         alias /var/www/media/;
    #         expires 1y;
    #         add_header Cache-Control "public";
    #     }
    # }
}
```

## Step 6: Build and Deploy Application

### 6.1 Build Docker Images

```bash
# Build all services
docker-compose -f docker-compose.prod.yml build

# This may take 10-15 minutes for the first build
# Monitor progress and check for any errors
```

### 6.2 Start Services

```bash
# Start all services in detached mode
docker-compose -f docker-compose.prod.yml up -d

# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 6.3 Initialize Database

```bash
# Run database migrations
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput

# Create superuser account
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

### 6.4 Verify Deployment

```bash
# Check all services are running
docker-compose -f docker-compose.prod.yml ps

# Test backend API
curl http://localhost:8000/api/posts/

# Test frontend (from your Windows laptop)
# Open browser and navigate to: http://54.123.45.67
```

## Step 7: Domain and SSL Configuration

### 7.1 Domain Setup

#### Configure DNS Records

1. **A Record**: Point your domain to your EC2 instance IP
   ```
   Type: A
   Name: @
   Value: 54.123.45.67
   TTL: 300
   ```

2. **CNAME Record**: For www subdomain
   ```
   Type: CNAME
   Name: www
   Value: yourdomain.com
   TTL: 300
   ```

#### Update Environment Variables

```bash
# Edit environment file
nano .env

# Update domain settings
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,54.123.45.67
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
REACT_APP_API_URL=https://yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 7.2 SSL Certificate with Let's Encrypt

#### Install Certbot

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Stop nginx temporarily
docker-compose -f docker-compose.prod.yml stop nginx
```

#### Obtain SSL Certificate

```bash
# Get certificate for your domain
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Certificate files will be saved to:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

#### Configure SSL in Docker

```bash
# Create SSL directory
mkdir -p ssl

# Copy certificates to project directory
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/

# Set proper permissions
sudo chown fintalk:fintalk ssl/*
chmod 600 ssl/*
```

#### Update Nginx Configuration

```bash
# Edit nginx configuration
nano nginx.prod.conf

# Uncomment the HTTPS server block
# Comment out the HTTP content serving
# Uncomment the HTTP to HTTPS redirect
```

#### Update Environment for SSL

```bash
# Edit environment file
nano .env

# Enable SSL redirect
SECURE_SSL_REDIRECT=True
```

### 7.3 Restart Services with SSL

```bash
# Rebuild and restart services
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# Verify HTTPS is working
curl -I https://yourdomain.com
```

### 7.4 Setup Certificate Auto-Renewal

```bash
# Create renewal script
sudo nano /etc/cron.d/certbot-renew

# Add the following content:
0 12 * * * root certbot renew --quiet --post-hook "cd /home/fintalk/fintalk-enhanced-blog && docker-compose -f docker-compose.prod.yml restart nginx"
```

## Step 8: Monitoring and Maintenance

### 8.1 Setup Log Rotation

```bash
# Create log rotation configuration
sudo nano /etc/logrotate.d/fintalk

# Add configuration:
/home/fintalk/fintalk-enhanced-blog/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 fintalk fintalk
    postrotate
        cd /home/fintalk/fintalk-enhanced-blog && docker-compose -f docker-compose.prod.yml restart backend
    endscript
}
```

### 8.2 Setup Automated Backups

```bash
# Create backup script
nano backup.sh

# Add backup script content:
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/fintalk/backups"
PROJECT_DIR="/home/fintalk/fintalk-enhanced-blog"

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
cd $PROJECT_DIR
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U fintalk_user fintalk_prod > $BACKUP_DIR/db_backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/db_backup_$DATE.sql

# Media files backup
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz -C $PROJECT_DIR media/

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

```bash
# Make script executable
chmod +x backup.sh

# Add to crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /home/fintalk/fintalk-enhanced-blog/backup.sh >> /home/fintalk/backup.log 2>&1
```

### 8.3 Setup Monitoring

```bash
# Install monitoring tools
sudo apt install -y htop iotop nethogs

# Create monitoring script
nano monitor.sh

# Add monitoring script:
#!/bin/bash
echo "=== System Status $(date) ==="
echo "CPU Usage:"
top -bn1 | grep "Cpu(s)" | awk '{print $2 $3 $4 $5 $6 $7 $8}'

echo "Memory Usage:"
free -h

echo "Disk Usage:"
df -h

echo "Docker Container Status:"
cd /home/fintalk/fintalk-enhanced-blog
docker-compose -f docker-compose.prod.yml ps

echo "Recent Errors:"
tail -n 10 logs/blog_manager_errors.log 2>/dev/null || echo "No error log found"
```

```bash
# Make executable
chmod +x monitor.sh

# Run monitoring
./monitor.sh
```

## Step 9: Security Hardening

### 9.1 Update Security Groups

```bash
# From AWS Console, update security group:
# Remove port 8000 access (no longer needed)
# Restrict SSH access to your IP only
```

### 9.2 Setup Fail2Ban

```bash
# Install Fail2Ban
sudo apt install -y fail2ban

# Configure Fail2Ban
sudo nano /etc/fail2ban/jail.local

# Add configuration:
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3

# Start and enable Fail2Ban
sudo systemctl start fail2ban
sudo systemctl enable fail2ban
```

### 9.3 Regular Security Updates

```bash
# Create update script
nano update.sh

# Add update script:
#!/bin/bash
echo "Starting system updates..."

# Update system packages
sudo apt update
sudo apt upgrade -y

# Update Docker images
cd /home/fintalk/fintalk-enhanced-blog
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# Clean up old Docker images
docker system prune -f

echo "Updates completed: $(date)"
```

```bash
# Make executable
chmod +x update.sh

# Schedule weekly updates
crontab -e

# Add weekly update on Sunday at 3 AM
0 3 * * 0 /home/fintalk/fintalk-enhanced-blog/update.sh >> /home/fintalk/update.log 2>&1
```

## Step 10: Testing and Verification

### 10.1 Functionality Testing

```bash
# Test API endpoints
curl -I https://yourdomain.com/api/posts/
curl -I https://yourdomain.com/api/health/

# Test admin panel
curl -I https://yourdomain.com/admin/

# Test static files
curl -I https://yourdomain.com/static/admin/css/base.css
```

### 10.2 Performance Testing

```bash
# Install Apache Bench for basic load testing
sudo apt install -y apache2-utils

# Test homepage performance
ab -n 100 -c 10 https://yourdomain.com/

# Test API performance
ab -n 100 -c 10 https://yourdomain.com/api/posts/
```

### 10.3 Security Testing

```bash
# Test SSL configuration
curl -I https://yourdomain.com/

# Check SSL certificate
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Test security headers
curl -I https://yourdomain.com/ | grep -E "(Strict-Transport-Security|X-Frame-Options|X-Content-Type-Options)"
```

## Troubleshooting

### Common Issues

#### Docker Build Failures
```bash
# Check Docker logs
docker-compose -f docker-compose.prod.yml logs backend

# Rebuild without cache
docker-compose -f docker-compose.prod.yml build --no-cache
```

#### Database Connection Issues
```bash
# Check database status
docker-compose -f docker-compose.prod.yml exec db pg_isready -U fintalk_user

# Check database logs
docker-compose -f docker-compose.prod.yml logs db
```

#### SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate manually
sudo certbot renew --dry-run
```

#### Performance Issues
```bash
# Check system resources
htop
docker stats

# Check disk space
df -h

# Check logs for errors
docker-compose -f docker-compose.prod.yml logs --tail=100
```

### Getting Help

- **AWS Support**: Use AWS Support Center for infrastructure issues
- **Application Logs**: Check Docker container logs for application issues
- **System Logs**: Check `/var/log/` for system-level issues
- **Community**: Search for solutions in Django, Docker, and AWS communities

## Maintenance Schedule

### Daily
- [ ] Check system status and logs
- [ ] Monitor application performance
- [ ] Review security alerts

### Weekly
- [ ] Review backup integrity
- [ ] Check SSL certificate status
- [ ] Update system packages
- [ ] Review user activity and content

### Monthly
- [ ] Full security audit
- [ ] Performance optimization review
- [ ] Backup restoration test
- [ ] Capacity planning review

## Cost Optimization

### AWS Cost Management

- **Instance Sizing**: Monitor CPU and memory usage, resize if needed
- **Reserved Instances**: Consider reserved instances for long-term deployments
- **Spot Instances**: Use spot instances for development environments
- **Storage Optimization**: Use appropriate storage types and clean up unused volumes

### Monitoring Costs

```bash
# Check current instance costs in AWS Console
# Set up billing alerts for unexpected charges
# Use AWS Cost Explorer to analyze spending patterns
```

---

**Congratulations!** You have successfully deployed the FinTalk Enhanced Blog Platform on AWS EC2. Your application should now be accessible at your domain with full SSL encryption and production-ready configuration.

For ongoing support and maintenance, refer to the administrator guide and monitoring procedures outlined in this documentation.