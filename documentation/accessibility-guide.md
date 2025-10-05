# Accessibility and Responsive Design Guide

This document outlines the accessibility and responsive design enhancements implemented in the FinTalk frontend application.

## Overview

The FinTalk application has been enhanced with comprehensive accessibility features and responsive design to ensure it works well for all users across different devices and assistive technologies.

## Accessibility Features

### 1. Semantic HTML and ARIA

- **Proper HTML5 semantic elements**: `<header>`, `<nav>`, `<main>`, `<article>`, `<section>`, `<footer>`
- **ARIA landmarks**: `role="banner"`, `role="navigation"`, `role="main"`, `role="contentinfo"`
- **ARIA labels**: Descriptive labels for interactive elements
- **ARIA live regions**: For dynamic content announcements
- **ARIA states**: `aria-expanded`, `aria-current`, `aria-busy`, etc.

### 2. Keyboard Navigation

- **Focus management**: Proper focus indicators and focus trapping in modals
- **Skip links**: "Skip to main content" link for keyboard users
- **Tab order**: Logical tab sequence throughout the application
- **Keyboard shortcuts**: Standard keyboard interactions (Enter, Space, Escape, Arrow keys)

### 3. Screen Reader Support

- **Screen reader only content**: `.sr-only` class for context that's only needed by screen readers
- **Descriptive text**: Comprehensive alt text, labels, and descriptions
- **Live announcements**: Dynamic content changes are announced to screen readers
- **Proper heading hierarchy**: Logical H1-H6 structure

### 4. Visual Accessibility

- **High contrast support**: `@media (prefers-contrast: high)` queries
- **Focus indicators**: Visible focus outlines with proper contrast
- **Color accessibility**: Not relying solely on color to convey information
- **Text scaling**: Responsive typography that scales appropriately

### 5. Motor Accessibility

- **Touch targets**: Minimum 44px touch target size on mobile devices
- **Reduced motion**: `@media (prefers-reduced-motion: reduce)` support
- **Hover alternatives**: All hover interactions have keyboard/touch equivalents

## Responsive Design Features

### 1. Breakpoint System

```css
:root {
  --breakpoint-sm: 576px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 992px;
  --breakpoint-xl: 1200px;
}
```

### 2. Responsive Grid System

- **CSS Grid**: Flexible grid layouts that adapt to screen size
- **Flexbox**: For component-level responsive layouts
- **Utility classes**: `.col-*`, `.d-flex`, `.justify-content-*`, etc.

### 3. Mobile-First Design

- **Progressive enhancement**: Base styles for mobile, enhanced for larger screens
- **Touch-friendly**: Larger touch targets and appropriate spacing on mobile
- **Mobile navigation**: Collapsible navigation menu for mobile devices

### 4. Responsive Typography

- **Fluid typography**: Font sizes that scale with viewport
- **Readable line lengths**: Optimal character count per line
- **Scalable spacing**: Consistent spacing that adapts to screen size

## Component Accessibility

### Button Component

```jsx
<Button
  variant="primary"
  loading={isLoading}
  loadingText="Saving..."
  ariaLabel="Save post"
  ariaDescribedBy="save-help"
>
  Save Post
</Button>
```

**Features:**
- Minimum 44px touch target
- Loading states with `aria-busy`
- Descriptive ARIA labels
- Keyboard accessible
- Focus indicators

### FormField Component

```jsx
<FormField
  label="Email Address"
  type="email"
  required
  error={errors.email}
  helpText="We'll never share your email"
  value={email}
  onChange={handleEmailChange}
/>
```

**Features:**
- Proper label association
- Required field indicators
- Error messages with `role="alert"`
- Help text association
- Validation feedback

### Modal Component

```jsx
<Modal
  isOpen={isOpen}
  onClose={handleClose}
  title="Confirm Action"
  closeOnEscape
  closeOnBackdrop
>
  <p>Are you sure you want to delete this post?</p>
</Modal>
```

**Features:**
- Focus trapping
- Escape key handling
- Backdrop click handling
- Proper ARIA attributes
- Focus restoration

### Alert Component

```jsx
<Alert
  type="success"
  title="Success"
  dismissible
  autoHide={5000}
  onDismiss={handleDismiss}
>
  Your post has been saved successfully!
</Alert>
```

**Features:**
- Appropriate ARIA live regions
- Keyboard dismissal
- Auto-hide functionality
- Screen reader announcements

## Responsive Hooks

### useResponsive Hook

```jsx
const { isMobile, isTablet, isDesktop, currentBreakpoint } = useResponsive();

// Conditional rendering based on screen size
if (isMobile) {
  return <MobileLayout />;
}
```

### useAccessibility Hook

```jsx
const { announce, manageFocus, trapFocus } = useAccessibility();

// Announce changes to screen readers
announce('Post saved successfully', 'polite');

// Manage focus programmatically
manageFocus(inputRef.current);
```

## CSS Architecture

### 1. CSS Custom Properties

```css
:root {
  /* Colors */
  --primary-color: #3498db;
  --text-primary: #2c3e50;
  --background-primary: #ffffff;
  
  /* Typography */
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  
  /* Spacing */
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  
  /* Transitions */
  --transition-normal: 0.3s ease;
}
```

### 2. Responsive Utilities

```css
/* Display utilities */
.d-none { display: none; }
.d-flex { display: flex; }
.d-block { display: block; }

/* Flexbox utilities */
.justify-content-center { justify-content: center; }
.align-items-center { align-items: center; }

/* Text utilities */
.text-center { text-align: center; }
.text-left { text-align: left; }

/* Spacing utilities */
.mt-3 { margin-top: var(--spacing-md); }
.p-2 { padding: var(--spacing-sm); }
```

### 3. Media Query Support

```css
/* High contrast mode */
@media (prefers-contrast: high) {
  :root {
    --primary-color: #0066cc;
    --border-color: #000000;
  }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  :root {
    --text-primary: #ffffff;
    --background-primary: #1a1a1a;
  }
}
```

## Testing

### Accessibility Testing

```javascript
// Test ARIA attributes
expect(button).toHaveAttribute('aria-label', 'Save post');
expect(input).toHaveAttribute('aria-invalid', 'true');

// Test keyboard navigation
fireEvent.keyDown(element, { key: 'Enter' });
fireEvent.keyDown(element, { key: 'Escape' });

// Test focus management
expect(document.activeElement).toBe(modal);
```

### Responsive Testing

```javascript
// Mock viewport size
mockMatchMedia(768); // Tablet size

// Test responsive behavior
const { isMobile, isTablet } = useResponsive();
expect(isMobile).toBe(false);
expect(isTablet).toBe(true);
```

## Best Practices

### 1. Accessibility

- Always provide alternative text for images
- Use semantic HTML elements
- Ensure sufficient color contrast (4.5:1 for normal text)
- Test with keyboard navigation
- Test with screen readers
- Provide skip links for keyboard users
- Use ARIA attributes appropriately

### 2. Responsive Design

- Design mobile-first
- Use relative units (rem, em, %)
- Test on real devices
- Optimize touch targets for mobile
- Consider different orientations
- Use progressive enhancement

### 3. Performance

- Lazy load images
- Use responsive images with srcset
- Minimize CSS and JavaScript
- Use CSS custom properties for theming
- Avoid layout shifts

## Browser Support

- **Modern browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Mobile browsers**: iOS Safari 14+, Chrome Mobile 90+
- **Assistive technologies**: NVDA, JAWS, VoiceOver, TalkBack

## Tools and Resources

### Testing Tools

- **axe-core**: Automated accessibility testing
- **WAVE**: Web accessibility evaluation
- **Lighthouse**: Performance and accessibility audits
- **Screen readers**: NVDA (free), VoiceOver (macOS/iOS)

### Development Tools

- **React Testing Library**: Accessibility-focused testing
- **Jest**: Unit testing framework
- **Storybook**: Component development and testing

### Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [MDN Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility)
- [WebAIM](https://webaim.org/)
- [A11y Project](https://www.a11yproject.com/)

## Maintenance

### Regular Audits

- Run automated accessibility tests
- Perform manual keyboard testing
- Test with screen readers
- Validate responsive design on various devices
- Monitor performance metrics

### Updates

- Keep dependencies updated
- Follow WCAG guidelines updates
- Monitor browser support changes
- Update testing procedures as needed

## Contributing

When contributing to the accessibility and responsive design features:

1. Follow the established patterns and conventions
2. Test with keyboard navigation
3. Test with screen readers when possible
4. Ensure responsive design works on various screen sizes
5. Add appropriate tests for new features
6. Update documentation as needed

## Support

For questions about accessibility or responsive design features, please:

1. Check this documentation first
2. Review the component examples
3. Run the test suite
4. Create an issue with detailed information about the problem

Remember: Accessibility is not a feature to be added later—it should be considered from the beginning of the development process.