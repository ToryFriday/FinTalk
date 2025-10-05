# Quick Disqus Fix Guide

## Current Status
- ✅ Code is fixed (React hooks issue resolved)
- ❓ Shortname `fintalk-blog` needs verification
- ❓ Disqus account setup needs completion

## What You Need to Do

### Option 1: Use Your Existing Shortname (if you have one)
If you already created a Disqus site:
1. Check your Disqus admin panel for your actual shortname
2. Update `.env` file with the correct shortname
3. Restart containers: `docker-compose restart frontend`

### Option 2: Create New Disqus Site
If you haven't created a Disqus site yet:

1. **Go to https://disqus.com/**
2. **Click "Get Started"**
3. **Choose "I want to install Disqus on my site"**
4. **Fill out the form:**
   - Website Name: "FinTalk Blog" (or whatever you prefer)
   - Website URL: `https://example.com` (temporary placeholder)
   - Shortname: `fintalk-blog` (or choose your own)
   - Category: Choose appropriate category

5. **After creation, go to Settings → General:**
   - Add `localhost` to Trusted Domains (no port number)
   - Add `127.0.0.1` to Trusted Domains
   - Save settings

6. **Restart your containers:**
   ```bash
   docker-compose restart frontend
   ```

## Test Your Setup

1. Visit `http://localhost:3000/test-disqus`
2. Look for the "Disqus Shortname Test" section
3. It will tell you if your shortname is valid
4. Check browser console for detailed debug info

## Common Issues

### "Shortname Invalid" Error
- The shortname doesn't exist in Disqus
- You need to create a Disqus site first
- Double-check spelling in your .env file

### "We were unable to load Disqus" Error
- Shortname exists but domain not trusted
- Add `localhost` to Disqus trusted domains
- Wait a few minutes for changes to propagate

### Still Not Working?
- Check browser console for specific errors
- Try the debug tools on the test page
- Verify your .env file has the correct shortname

## Current Configuration
Your `.env` file currently has:
```
REACT_APP_DISQUS_SHORTNAME=fintalk-blog
```

This shortname needs to exist in your Disqus account for it to work.