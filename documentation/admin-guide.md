# FinTalk Enhanced Blog Platform - Administrator Guide

## Overview

This guide provides comprehensive information for administrators and moderators managing the FinTalk Enhanced Blog Platform. It covers user management, content moderation, system monitoring, and platform administration.

## Administrator Dashboard

### Accessing Admin Features

1. **Django Admin Panel**: `http://localhost:8000/admin/`
2. **Moderation Dashboard**: Available through the main application
3. **System Monitoring**: Built-in monitoring tools and external integrations

### Admin User Setup

```bash
# Create superuser account
docker-compose exec backend python manage.py createsuperuser

# Or in development
cd backend
python manage.py createsuperuser
```

## User Management

### User Roles and Permissions

#### Role Hierarchy

1. **Admin**: Full system access
   - User management
   - Content moderation
   - System configuration
   - Role assignment

2. **Editor**: Content and user moderation
   - Content moderation
   - Writer management
   - Flag resolution
   - User role assignment (limited)

3. **Writer**: Content creation
   - Create and publish articles
   - Manage own content
   - Access to media uploads

4. **Reader**: Basic user features
   - Save articles
   - Follow authors
   - Comment on posts
   - Email subscriptions

5. **Guest**: Public access only
   - Read published content
   - No account features

### Managing User Accounts

#### User Registration Monitoring

```python
# View recent registrations
from django.contrib.auth.models import User
from accounts.models import UserProfile

# Recent users (last 7 days)
recent_users = User.objects.filter(
    date_joined__gte=timezone.now() - timedelta(days=7)
).select_related('userprofile')

# Unverified accounts
unverified = UserProfile.objects.filter(is_email_verified=False)
```

#### Role Assignment

1. **Through Django Admin**:
   - Navigate to Users → User roles
   - Select user and assign role
   - Add assignment notes

2. **Through API**:
   ```bash
   curl -X POST http://localhost:8000/api/auth/role-assignment/ \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": 123,
       "role_name": "writer",
       "notes": "Promoted based on quality content"
     }'
   ```

#### User Account Actions

- **Suspend Account**: Temporarily disable user access
- **Verify Email**: Manually verify user email addresses
- **Reset Password**: Generate password reset links
- **Merge Accounts**: Combine duplicate user accounts
- **Export User Data**: Generate user data exports for GDPR compliance

### Bulk User Operations

```python
# Bulk role assignment
from accounts.services import UserManagementService

# Promote multiple users to writer role
user_ids = [123, 456, 789]
UserManagementService.bulk_role_assignment(
    user_ids=user_ids,
    role_name='writer',
    assigned_by=admin_user
)

# Bulk email verification
UserManagementService.bulk_verify_emails(user_ids)
```

## Content Moderation

### Moderation Dashboard

Access the moderation dashboard to:
- Review flagged content
- Monitor user reports
- Track moderation actions
- View system statistics

### Content Flag Management

#### Flag Categories

- **Spam**: Promotional or irrelevant content
- **Harassment**: Abusive or threatening content
- **Inappropriate**: Content violating community guidelines
- **Copyright**: Potential copyright infringement
- **Misinformation**: False or misleading information

#### Flag Resolution Process

1. **Review Flagged Content**
   ```bash
   # View pending flags
   curl -X GET http://localhost:8000/api/moderation/flags/?status=pending
   ```

2. **Investigate Report**
   - Review the flagged content
   - Check user history
   - Assess community guidelines violation

3. **Take Action**
   - **Dismiss**: Flag is invalid
   - **Edit Content**: Make necessary corrections
   - **Remove Content**: Delete violating content
   - **Suspend User**: Temporary account suspension
   - **Ban User**: Permanent account removal

4. **Document Decision**
   ```bash
   curl -X PUT http://localhost:8000/api/moderation/flags/123/ \
     -H "Content-Type: application/json" \
     -d '{
       "status": "resolved_valid",
       "resolution_notes": "Content removed for spam violation",
       "action_taken": "content_removed"
     }'
   ```

### Automated Moderation

#### Content Filters

The system includes automated filters for:
- **Spam Detection**: Keyword-based spam filtering
- **Link Validation**: Malicious URL detection
- **Content Length**: Minimum/maximum content requirements
- **Rate Limiting**: Prevents automated posting

#### Configuration

```python
# settings/moderation.py
MODERATION_SETTINGS = {
    'AUTO_FLAG_THRESHOLD': 3,  # Auto-flag after 3 reports
    'SPAM_KEYWORDS': ['buy now', 'click here', 'limited time'],
    'MAX_LINKS_PER_POST': 5,
    'MIN_CONTENT_LENGTH': 100,
    'MAX_CONTENT_LENGTH': 50000,
}
```

### Content Quality Guidelines

#### Editorial Standards

- **Accuracy**: Verify financial information and data
- **Originality**: Ensure content is original or properly attributed
- **Relevance**: Content should be relevant to financial topics
- **Professional Tone**: Maintain professional communication standards
- **Legal Compliance**: Ensure compliance with financial regulations

#### Content Review Checklist

- [ ] Content is original and properly sourced
- [ ] Financial data is accurate and current
- [ ] No promotional or spam content
- [ ] Appropriate language and tone
- [ ] Proper formatting and structure
- [ ] Images have appropriate alt text
- [ ] Links are relevant and functional

## Email and Notification Management

### Email Subscription Management

#### Subscription Types

- **All Posts**: Notifications for all new articles
- **Author Following**: Notifications from followed authors
- **Weekly Digest**: Weekly summary of top content
- **System Updates**: Important platform announcements

#### Managing Subscriptions

```python
# View subscription statistics
from notifications.models import EmailSubscription

# Active subscriptions by type
subscription_stats = EmailSubscription.objects.filter(
    is_active=True
).values('subscription_type').annotate(
    count=Count('id')
)

# Recent unsubscribes
recent_unsubscribes = EmailSubscription.objects.filter(
    is_active=False,
    updated_at__gte=timezone.now() - timedelta(days=7)
)
```

### Email Template Management

#### Template Types

- **Welcome Email**: New user registration
- **Email Verification**: Account verification
- **New Post Notification**: Article publication alerts
- **Weekly Digest**: Content summary emails
- **Password Reset**: Password recovery emails

#### Customizing Templates

1. **Edit Templates**: Located in `backend/templates/emails/`
2. **Test Templates**: Use Django's email testing tools
3. **Preview Templates**: Built-in template preview system

### Notification Monitoring

```bash
# Check email delivery status
docker-compose exec backend python manage.py shell
>>> from notifications.services import EmailService
>>> EmailService.get_delivery_stats()
```

## System Monitoring and Analytics

### Performance Monitoring

#### Key Metrics

- **User Activity**: Daily/weekly active users
- **Content Creation**: Posts published per day/week
- **Engagement**: Comments, saves, follows
- **System Performance**: Response times, error rates

#### Monitoring Dashboard

```python
# Generate system statistics
from common.monitoring import SystemMonitor

stats = SystemMonitor.get_system_stats()
print(f"Active users today: {stats['users']['active_today']}")
print(f"Posts published this week: {stats['posts']['published_this_week']}")
print(f"System CPU usage: {stats['system']['cpu_usage']}%")
```

### Database Management

#### Regular Maintenance Tasks

```bash
# Database optimization
docker-compose exec backend python manage.py optimize_db

# Clean up old sessions
docker-compose exec backend python manage.py clearsessions

# Update search indexes
docker-compose exec backend python manage.py update_index
```

#### Backup Procedures

```bash
# Create database backup
docker-compose exec db pg_dump -U postgres fintalk_prod > backup_$(date +%Y%m%d).sql

# Restore from backup
docker-compose exec -T db psql -U postgres fintalk_prod < backup_20240115.sql
```

### Log Management

#### Log Files

- **Application Logs**: `backend/logs/blog_manager.log`
- **Error Logs**: `backend/logs/blog_manager_errors.log`
- **Debug Logs**: `backend/logs/blog_manager_debug.log`
- **Access Logs**: Nginx access logs

#### Log Analysis

```bash
# View recent errors
tail -f backend/logs/blog_manager_errors.log

# Search for specific issues
grep "CSRF" backend/logs/blog_manager.log

# Monitor real-time activity
tail -f backend/logs/blog_manager.log | grep "POST"
```

## Security Management

### Security Monitoring

#### Security Alerts

Monitor for:
- **Failed Login Attempts**: Potential brute force attacks
- **CSRF Failures**: Cross-site request forgery attempts
- **Suspicious User Activity**: Unusual posting patterns
- **File Upload Issues**: Malicious file upload attempts

#### Security Logs

```bash
# View security-related logs
grep "SECURITY" backend/logs/blog_manager.log

# Monitor failed authentication
grep "authentication failed" backend/logs/blog_manager.log
```

### User Security Management

#### Account Security

- **Password Policies**: Enforce strong password requirements
- **Session Management**: Monitor and manage user sessions
- **Two-Factor Authentication**: (Future enhancement)
- **Account Lockout**: Temporary lockout after failed attempts

#### Suspicious Activity Response

1. **Identify Threat**: Analyze logs and user behavior
2. **Immediate Action**: Suspend account if necessary
3. **Investigation**: Gather evidence and assess impact
4. **Resolution**: Take appropriate corrective action
5. **Documentation**: Record incident and response

## Content Management

### Article Management

#### Bulk Operations

```python
# Bulk publish scheduled posts
from posts.services import PostService

# Publish all scheduled posts
PostService.publish_scheduled_posts()

# Bulk update post status
PostService.bulk_update_status(
    post_ids=[1, 2, 3],
    status='published'
)
```

#### Content Analytics

- **Popular Articles**: Most viewed and shared content
- **Author Performance**: Top-performing writers
- **Tag Analysis**: Most popular topics and tags
- **Engagement Metrics**: Comments, saves, and shares

### Media Management

#### File Storage

- **Storage Limits**: Monitor disk usage and set limits
- **File Cleanup**: Remove orphaned media files
- **Image Optimization**: Automatic image compression
- **CDN Integration**: Content delivery network setup

```bash
# Clean up unused media files
docker-compose exec backend python manage.py cleanup_media

# Optimize images
docker-compose exec backend python manage.py optimize_images
```

## API Management

### API Monitoring

#### Usage Statistics

```python
# API usage statistics
from common.monitoring import APIMonitor

api_stats = APIMonitor.get_usage_stats()
print(f"API requests today: {api_stats['requests_today']}")
print(f"Most used endpoint: {api_stats['top_endpoint']}")
```

#### Rate Limiting

- **Anonymous Users**: 100 requests/hour
- **Authenticated Users**: 1000 requests/hour
- **Premium Users**: 5000 requests/hour

### API Security

#### Authentication Monitoring

- **Invalid Tokens**: Monitor for authentication failures
- **Suspicious Patterns**: Detect automated requests
- **Rate Limit Violations**: Track and respond to abuse

## Troubleshooting

### Common Issues

#### User Issues

**Email Verification Problems**
```bash
# Manually verify user email
docker-compose exec backend python manage.py shell
>>> from accounts.models import UserProfile
>>> profile = UserProfile.objects.get(user__email='user@example.com')
>>> profile.is_email_verified = True
>>> profile.save()
```

**Role Assignment Issues**
```bash
# Check user roles
>>> from accounts.models import UserRole
>>> UserRole.objects.filter(user__username='username')
```

#### System Issues

**Database Connection Problems**
```bash
# Check database status
docker-compose exec db pg_isready -U postgres

# Restart database
docker-compose restart db
```

**Email Delivery Issues**
```bash
# Test email configuration
docker-compose exec backend python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
```

### Performance Issues

#### Slow Queries

```python
# Enable query logging
# settings/development.py
LOGGING = {
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['file'],
        }
    }
}
```

#### Memory Usage

```bash
# Monitor container memory usage
docker stats

# Check Python memory usage
docker-compose exec backend python -c "
import psutil
print(f'Memory usage: {psutil.virtual_memory().percent}%')
"
```

## Maintenance Procedures

### Regular Maintenance

#### Daily Tasks

- [ ] Review system logs for errors
- [ ] Check email delivery status
- [ ] Monitor user activity and registrations
- [ ] Review flagged content

#### Weekly Tasks

- [ ] Database backup and verification
- [ ] Performance metrics review
- [ ] User role and permission audit
- [ ] Content quality review

#### Monthly Tasks

- [ ] Security audit and updates
- [ ] System performance optimization
- [ ] User feedback review and response
- [ ] Feature usage analysis

### System Updates

#### Application Updates

```bash
# Update application code
git pull origin main

# Update dependencies
docker-compose build --no-cache

# Run migrations
docker-compose exec backend python manage.py migrate

# Restart services
docker-compose restart
```

#### Security Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Update Docker images
docker-compose pull
docker-compose up -d
```

## Best Practices

### User Management

- **Regular Audits**: Review user roles and permissions regularly
- **Clear Communication**: Provide clear guidelines and feedback
- **Fair Moderation**: Apply rules consistently and fairly
- **User Support**: Respond promptly to user issues and questions

### Content Moderation

- **Consistent Standards**: Apply community guidelines uniformly
- **Transparent Process**: Explain moderation decisions when appropriate
- **Appeal Process**: Provide mechanism for users to appeal decisions
- **Documentation**: Keep detailed records of moderation actions

### System Administration

- **Regular Backups**: Maintain current and tested backups
- **Security Updates**: Keep all systems and dependencies updated
- **Monitoring**: Continuously monitor system health and performance
- **Documentation**: Maintain current documentation and procedures

## Support and Resources

### Getting Help

- **Technical Issues**: Check logs and system status first
- **User Issues**: Review user management procedures
- **Security Concerns**: Follow incident response procedures
- **Performance Problems**: Use monitoring tools and metrics

### Documentation

- **API Documentation**: Complete API reference and examples
- **User Guide**: Comprehensive user instructions
- **Development Guide**: Setup and development procedures
- **Deployment Guide**: Production deployment instructions

### Community

- **Admin Forum**: Connect with other administrators
- **Feature Requests**: Submit and vote on new features
- **Bug Reports**: Report issues and track resolutions
- **Best Practices**: Share experiences and solutions

---

**Need additional support?** Contact the development team or consult the technical documentation for more detailed information about specific features and procedures.