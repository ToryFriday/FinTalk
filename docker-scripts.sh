#!/bin/bash

# Docker management scripts for Blog Post Manager

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Development environment functions
dev_start() {
    print_status "Starting development environment..."
    docker-compose up -d
    print_status "Services started. Frontend: http://localhost:3000, Backend: http://localhost:8000"
}

dev_stop() {
    print_status "Stopping development environment..."
    docker-compose down
}

dev_restart() {
    print_status "Restarting development environment..."
    docker-compose restart
}

dev_logs() {
    docker-compose logs -f
}

dev_build() {
    print_status "Building development images..."
    docker-compose build --no-cache
}

# Production environment functions
prod_start() {
    if [ ! -f .env ]; then
        print_error ".env file not found. Please copy .env.example to .env and configure it."
        exit 1
    fi
    print_status "Starting production environment..."
    docker-compose -f docker-compose.prod.yml up -d
    print_status "Production services started. Access via http://localhost"
}

prod_stop() {
    print_status "Stopping production environment..."
    docker-compose -f docker-compose.prod.yml down
}

prod_logs() {
    docker-compose -f docker-compose.prod.yml logs -f
}

prod_build() {
    print_status "Building production images..."
    docker-compose -f docker-compose.prod.yml build --no-cache
}

# Database functions
db_migrate() {
    print_status "Running database migrations..."
    docker-compose exec backend python manage.py migrate
}

db_shell() {
    print_status "Opening database shell..."
    docker-compose exec db psql -U postgres -d fintalk_dev
}

db_backup() {
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    print_status "Creating database backup: $BACKUP_FILE"
    docker-compose exec db pg_dump -U postgres fintalk_dev > "$BACKUP_FILE"
    print_status "Backup created: $BACKUP_FILE"
}

# Utility functions
health_check() {
    print_status "Checking service health..."
    
    # Check database
    if docker-compose exec db pg_isready -U postgres > /dev/null 2>&1; then
        print_status "✓ Database is healthy"
    else
        print_error "✗ Database is not healthy"
    fi
    
    # Check backend
    if docker-compose exec backend python manage.py check > /dev/null 2>&1; then
        print_status "✓ Backend is healthy"
    else
        print_error "✗ Backend is not healthy"
    fi
    
    # Show running containers
    print_status "Running containers:"
    docker-compose ps
}

cleanup() {
    print_warning "This will remove all containers, images, and volumes. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_status "Cleaning up Docker resources..."
        docker-compose down -v
        docker system prune -a -f
        print_status "Cleanup completed"
    else
        print_status "Cleanup cancelled"
    fi
}

# Main script logic
case "$1" in
    # Development commands
    "dev:start")
        dev_start
        ;;
    "dev:stop")
        dev_stop
        ;;
    "dev:restart")
        dev_restart
        ;;
    "dev:logs")
        dev_logs
        ;;
    "dev:build")
        dev_build
        ;;
    
    # Production commands
    "prod:start")
        prod_start
        ;;
    "prod:stop")
        prod_stop
        ;;
    "prod:logs")
        prod_logs
        ;;
    "prod:build")
        prod_build
        ;;
    
    # Database commands
    "db:migrate")
        db_migrate
        ;;
    "db:shell")
        db_shell
        ;;
    "db:backup")
        db_backup
        ;;
    
    # Utility commands
    "health")
        health_check
        ;;
    "cleanup")
        cleanup
        ;;
    
    *)
        echo "FinTalk Management Script"
        echo ""
        echo "Usage: $0 <command>"
        echo ""
        echo "Development Commands:"
        echo "  dev:start    - Start development environment"
        echo "  dev:stop     - Stop development environment"
        echo "  dev:restart  - Restart development environment"
        echo "  dev:logs     - View development logs"
        echo "  dev:build    - Build development images"
        echo ""
        echo "Production Commands:"
        echo "  prod:start   - Start production environment"
        echo "  prod:stop    - Stop production environment"
        echo "  prod:logs    - View production logs"
        echo "  prod:build   - Build production images"
        echo ""
        echo "Database Commands:"
        echo "  db:migrate   - Run database migrations"
        echo "  db:shell     - Open database shell"
        echo "  db:backup    - Create database backup"
        echo ""
        echo "Utility Commands:"
        echo "  health       - Check service health"
        echo "  cleanup      - Clean up Docker resources"
        echo ""
        echo "Examples:"
        echo "  $0 dev:start"
        echo "  $0 prod:start"
        echo "  $0 health"
        exit 1
        ;;
esac