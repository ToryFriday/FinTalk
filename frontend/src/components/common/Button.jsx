import React, { forwardRef } from 'react';
import LoadingSpinner from './LoadingSpinner';
import { useAccessibility } from '../../hooks/useAccessibility';

/**
 * Enhanced accessible button component
 * @param {Object} props - Component props
 * @param {string} props.variant - Button variant (primary, secondary, danger, etc.)
 * @param {string} props.size - Button size (sm, md, lg)
 * @param {boolean} props.loading - Loading state
 * @param {boolean} props.disabled - Disabled state
 * @param {string} props.loadingText - Text to show when loading
 * @param {React.ReactNode} props.children - Button content
 * @param {Function} props.onClick - Click handler
 * @param {string} props.ariaLabel - ARIA label for accessibility
 * @param {string} props.ariaDescribedBy - ARIA described by
 * @param {string} props.type - Button type
 * @param {string} props.className - Additional CSS classes
 */
const Button = forwardRef(({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  loadingText = 'Loading...',
  children,
  onClick,
  ariaLabel,
  ariaDescribedBy,
  type = 'button',
  className = '',
  ...props
}, ref) => {
  const { announce } = useAccessibility();

  const handleClick = (e) => {
    if (loading || disabled) {
      e.preventDefault();
      return;
    }

    if (onClick) {
      onClick(e);
    }

    // Announce action for screen readers if needed
    if (ariaLabel && !loading) {
      announce(`${ariaLabel} activated`, 'polite');
    }
  };

  const buttonClasses = [
    'btn',
    `btn-${variant}`,
    `btn-${size}`,
    loading && 'btn-loading',
    className
  ].filter(Boolean).join(' ');

  const isDisabled = disabled || loading;

  return (
    <button
      ref={ref}
      type={type}
      className={buttonClasses}
      onClick={handleClick}
      disabled={isDisabled}
      aria-label={ariaLabel}
      aria-describedby={ariaDescribedBy}
      aria-busy={loading}
      {...props}
    >
      {loading && (
        <LoadingSpinner 
          size="sm" 
          color="white" 
          message={loadingText}
        />
      )}
      <span className={loading ? 'sr-only' : ''}>
        {loading ? loadingText : children}
      </span>
    </button>
  );
});

Button.displayName = 'Button';

export default Button;