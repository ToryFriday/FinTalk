import React from 'react';
import { useAccessibility } from '../../hooks/useAccessibility';
import './LoadingSpinner.css';

/**
 * Accessible loading spinner component
 * @param {Object} props - Component props
 * @param {string} props.size - Size variant (sm, md, lg)
 * @param {string} props.color - Color variant
 * @param {string} props.message - Loading message for screen readers
 * @param {boolean} props.overlay - Whether to show as overlay
 * @param {string} props.className - Additional CSS classes
 */
const LoadingSpinner = ({ 
  size = 'md', 
  color = 'primary', 
  message = 'Loading...', 
  overlay = false,
  className = '',
  ...props 
}) => {
  const { announce } = useAccessibility();

  React.useEffect(() => {
    if (message) {
      announce(message, 'polite');
    }
  }, [message, announce]);

  const spinnerClasses = [
    'loading-spinner',
    `loading-spinner-${size}`,
    `loading-spinner-${color}`,
    className
  ].filter(Boolean).join(' ');

  const containerClasses = [
    'loading-container',
    overlay && 'loading-overlay'
  ].filter(Boolean).join(' ');

  const spinner = (
    <div 
      className={spinnerClasses}
      role="status"
      aria-label={message}
      {...props}
    >
      <div className="loading-spinner-circle" />
      <span className="sr-only">{message}</span>
    </div>
  );

  if (overlay) {
    return (
      <div className={containerClasses}>
        {spinner}
      </div>
    );
  }

  return spinner;
};

export default LoadingSpinner;