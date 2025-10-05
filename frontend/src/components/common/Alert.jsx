import React, { useEffect } from 'react';
import { useAccessibility } from '../../hooks/useAccessibility';
import Button from './Button';
import './Alert.css';

/**
 * Accessible alert component with auto-dismiss and actions
 * @param {Object} props - Component props
 * @param {string} props.type - Alert type (success, danger, warning, info)
 * @param {string} props.title - Alert title
 * @param {React.ReactNode} props.children - Alert content
 * @param {boolean} props.dismissible - Whether alert can be dismissed
 * @param {Function} props.onDismiss - Dismiss handler
 * @param {number} props.autoHide - Auto hide after milliseconds
 * @param {Array} props.actions - Action buttons
 * @param {string} props.className - Additional CSS classes
 * @param {boolean} props.icon - Whether to show icon
 */
const Alert = ({
  type = 'info',
  title,
  children,
  dismissible = false,
  onDismiss,
  autoHide,
  actions = [],
  className = '',
  icon = true,
  ...props
}) => {
  const { announce } = useAccessibility();

  useEffect(() => {
    // Announce alert to screen readers
    const message = title ? `${title}. ${children}` : children;
    const priority = type === 'danger' ? 'assertive' : 'polite';
    announce(message, priority);
  }, [title, children, type, announce]);

  useEffect(() => {
    if (autoHide && onDismiss) {
      const timer = setTimeout(() => {
        onDismiss();
      }, autoHide);

      return () => clearTimeout(timer);
    }
  }, [autoHide, onDismiss]);

  const handleDismiss = () => {
    if (onDismiss) {
      onDismiss();
      announce('Alert dismissed', 'polite');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape' && dismissible) {
      handleDismiss();
    }
  };

  const alertClasses = [
    'alert',
    `alert-${type}`,
    dismissible && 'alert-dismissible',
    className
  ].filter(Boolean).join(' ');

  const getIcon = () => {
    const icons = {
      success: '✓',
      danger: '⚠',
      warning: '⚠',
      info: 'ℹ'
    };
    return icons[type] || icons.info;
  };

  const getRole = () => {
    return type === 'danger' ? 'alert' : 'status';
  };

  return (
    <div
      className={alertClasses}
      role={getRole()}
      aria-live={type === 'danger' ? 'assertive' : 'polite'}
      onKeyDown={handleKeyDown}
      tabIndex={dismissible ? 0 : -1}
      {...props}
    >
      <div className="alert-content">
        {icon && (
          <div className="alert-icon" aria-hidden="true">
            {getIcon()}
          </div>
        )}
        
        <div className="alert-body">
          {title && (
            <div className="alert-title">
              {title}
            </div>
          )}
          
          <div className="alert-message">
            {children}
          </div>
          
          {actions.length > 0 && (
            <div className="alert-actions">
              {actions.map((action, index) => (
                <Button
                  key={index}
                  variant={action.variant || 'outline-primary'}
                  size="sm"
                  onClick={action.onClick}
                  className="alert-action-btn"
                >
                  {action.label}
                </Button>
              ))}
            </div>
          )}
        </div>
        
        {dismissible && (
          <Button
            variant="outline-secondary"
            size="sm"
            onClick={handleDismiss}
            className="alert-dismiss"
            ariaLabel="Dismiss alert"
          >
            ×
          </Button>
        )}
      </div>
    </div>
  );
};

export default Alert;