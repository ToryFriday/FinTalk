# Disqus Integration Components

This directory contains components for integrating Disqus commenting system into the blog platform.

## Components

### DisqusComments

A React component that embeds Disqus comments into a page.

**Props:**
- `postId` (required): Unique identifier for the post
- `postTitle` (required): Title of the post for Disqus
- `postUrl` (optional): URL of the post page (defaults to generated URL)
- `postSlug` (optional): Custom slug for the post (defaults to `post-{postId}`)

**Usage:**
```jsx
import DisqusComments from '../components/common/DisqusComments';

<DisqusComments
  postId={post.id}
  postTitle={post.title}
  postUrl={`${window.location.origin}/posts/${post.id}`}
/>
```

### CommentCount

A React component that displays the comment count for a post.

**Props:**
- `postId` (required): Unique identifier for the post
- `postSlug` (optional): Custom slug for the post
- `className` (optional): Additional CSS classes
- `showZero` (optional): Whether to show "0 comments" or hide when zero (default: true)

**Usage:**
```jsx
import CommentCount from '../components/common/CommentCount';

<CommentCount 
  postId={post.id} 
  className="compact" 
  showZero={false}
/>
```

## Configuration

The Disqus integration requires the following environment variables:

- `REACT_APP_DISQUS_SHORTNAME`: Your Disqus shortname (required)
- `REACT_APP_SITE_URL`: Your site URL (optional, defaults to current origin)

### Docker Environment

Add these variables to your `.env` file:

```env
REACT_APP_DISQUS_SHORTNAME=your-disqus-shortname
REACT_APP_SITE_URL=http://localhost:3000
```

And ensure they're passed to the frontend container in `docker-compose.yml`:

```yaml
frontend:
  environment:
    - REACT_APP_DISQUS_SHORTNAME=${REACT_APP_DISQUS_SHORTNAME}
    - REACT_APP_SITE_URL=${REACT_APP_SITE_URL}
```

## Features

### Automatic Configuration Detection

Both components automatically detect if Disqus is properly configured:
- If `REACT_APP_DISQUS_SHORTNAME` is not set, components will show fallback messages or render nothing
- No errors are thrown for missing configuration

### Error Handling

- **DisqusComments**: Shows fallback message if Disqus fails to load
- **CommentCount**: Silently fails and shows 0 comments if service is unavailable

### Loading States

- **DisqusComments**: Shows loading spinner while Disqus initializes
- **CommentCount**: Shows loading spinner while fetching count

### Responsive Design

Both components include responsive CSS that works on mobile and desktop devices.

## Testing

### Manual Testing

Visit `/test-disqus` in your application to access a test page that demonstrates both components.

### Unit Tests

Run the test suite:

```bash
npm test -- --testPathPattern="Disqus"
```

### Integration Testing

The components are tested with:
- Proper configuration scenarios
- Missing configuration scenarios
- Error handling
- Loading states

## Troubleshooting

### Comments Not Loading

1. Verify `REACT_APP_DISQUS_SHORTNAME` is set correctly
2. Check that your Disqus shortname exists and is active
3. Ensure your domain is added to your Disqus site settings
4. Check browser console for JavaScript errors

### Comment Counts Not Showing

1. Comment counts may take time to load from Disqus API
2. Counts are cached to improve performance
3. New posts may show 0 comments until first comment is posted

### Development vs Production

- Use different Disqus shortnamesfor development and production
- Ensure production domain is configured in Disqus settings
- Test thoroughly in production environment before launch