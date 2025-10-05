# Disqus Setup Guide

This guide will help you set up Disqus commenting system for your blog.

## Prerequisites

You need a Disqus account to use the commenting system. Disqus is a free third-party service.

## Step-by-Step Setup

### 1. Create Disqus Account

1. Visit [https://disqus.com/](https://disqus.com/)
2. Click "Get Started"
3. Choose "I want to install Disqus on my site"
4. Fill out the form:
   - **Website Name**: Your blog name (e.g., "FinTalk Blog")
   - **Category**: Choose appropriate category
   - **Website URL**: Use a placeholder like `https://example.com` (we'll fix this later)
   - **Shortname**: This is important! Choose something like `fintalk-blog` or `your-blog-name`
   - Remember this shortname - you'll need it for configuration

**Important**: Disqus doesn't accept localhost URLs during setup, so use a placeholder domain initially.

### 2. Configure Disqus Site Settings

1. After creating your site, go to Disqus Admin
2. Navigate to **Settings → General**
3. Update the **Website URL** to your actual domain (or keep the placeholder for now)
4. In the **Trusted Domains** section, add:
   - `localhost` (for development - note: no port number)
   - `127.0.0.1` (alternative localhost)
   - Your production domain when you deploy
5. Save the settings

**Note**: For development, Disqus will work with localhost even if your main URL is different.

### 3. Update Environment Configuration

1. Open your `.env` file in the project root
2. Replace `your-disqus-shortname` with your actual shortname:

```env
# Replace with your actual Disqus shortname
REACT_APP_DISQUS_SHORTNAME=your-actual-shortname-here
REACT_APP_SITE_URL=http://localhost:3000
```

### 4. Restart Docker Containers

After updating the `.env` file:

```bash
docker-compose down
docker-compose up -d
```

### 5. Test the Integration

1. Visit your blog at `http://localhost:3000`
2. Go to any blog post
3. Scroll down to see the comments section
4. Visit `http://localhost:3000/test-disqus` for a dedicated test page

## Troubleshooting

### "We were unable to load Disqus" Error

This error means:
- Your shortname doesn't exist in Disqus
- Your domain isn't trusted in Disqus settings
- There's a network issue

**Solutions:**
1. Double-check your shortname in Disqus admin
2. Ensure `localhost` (without port) is in trusted domains
3. Try adding `127.0.0.1` to trusted domains as well
4. Check browser console for specific errors
5. Wait a few minutes after adding domains (Disqus may need time to propagate changes)

### Comments Not Appearing

1. **Check Configuration**: Verify shortname is correct
2. **Check Domain**: Ensure your domain is trusted in Disqus
3. **Clear Cache**: Try hard refresh (Ctrl+F5)
4. **Check Network**: Ensure you can access disqus.com

### Development vs Production

- **Development**: Use `localhost` (no port) in trusted domains
- **Production**: Add your actual domain to trusted domains
- **Consider**: Using different Disqus sites for dev/prod

### Common Setup Issues

#### "Invalid URL" Error During Site Creation
- **Problem**: Disqus rejects `http://localhost:3000` during initial setup
- **Solution**: Use a placeholder like `https://example.com` initially
- **Fix Later**: Update the URL in Settings → General after creation

#### Localhost Not Working
- **Add to Trusted Domains**: `localhost` (without port number)
- **Also Try**: `127.0.0.1`
- **Don't Use**: `localhost:3000` (Disqus doesn't like ports in trusted domains)

## Free vs Paid Disqus

- **Free Plan**: Includes ads, basic moderation
- **Paid Plans**: Remove ads, advanced features
- **For Development**: Free plan is sufficient

## Security Considerations

- Disqus handles user authentication
- Comments are stored on Disqus servers
- You can moderate comments through Disqus admin
- Consider privacy implications for your users

## Alternative: Mock Mode for Development

If you don't want to set up Disqus immediately, the system will show a helpful message explaining how to configure it. This allows you to develop other features while planning your commenting strategy.

## Need Help?

- [Disqus Help Center](https://help.disqus.com/)
- [Disqus Installation Guide](https://help.disqus.com/en/articles/1717112-universal-embed-code)
- Check the browser console for specific error messages