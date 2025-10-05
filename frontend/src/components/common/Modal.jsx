import React, { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { useAccessibility } from '../../hooks/useAccessibility';
import { useResponsive } from '../../hooks/useResponsive';
import Button from './Button';
import './Modal.css';

/**
 * Accessible modal component with focus management
 * @param {Object} props - Component props
 * @param {boolean} props.isOpen - Whether modal is open
 * @param {Function} props.onClose - Close handler
 * @param {string} props.title - Modal title
 * @param {React.ReactNode} props.children - Modal content
 * @param {string} props.size - Modal size (sm, md, lg, xl)
 * @param {boolean} props.closeOnBackdrop - Close on backdrop click
 * @param {boolean} props.closeOnEscape - Close on escape key
 * @param {Array} props.actions - Action buttons
 * @param {string} props.className - Additional CSS classes
 */
const Modal = ({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
  closeOnBackdrop = true,
  closeOnEscape = true,
  actions = [],
  className = '',
  ...props
}) => {
  const modalRef = useRef(null);
  const previousActiveElement = useRef(null);
  const { trapFocus, announce } = useAccessibility();
  const { isMobile } = useResponsive();

  useEffect(() => {
    if (isOpen) {
      // Store previously focused element
      previousActiveElement.current = document.activeElement;
      
      // Prevent body scroll
      document.body.style.overflow = 'hidden';
      
      // Announce modal opening
      announce(`Modal opened: ${title || 'Dialog'}`, 'polite');
      
      // Set up focus trap
      const cleanup = trapFocus(modalRef.current);
      
      return () => {
        cleanup();
        // Restore body scroll
        document.body.style.overflow = '';
        
        // Restore focus to previous element
        if (previousActiveElement.current) {
          previousActiveElement.current.focus();
        }
      };
    }
  }, [isOpen, title, trapFocus, announce]);

  useEffect(() => {
    if (closeOnEscape) {
      const handleEscape = (e) => {
        if (e.key === 'Escape' && isOpen) {
          onClose();
        }
      };

      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [closeOnEscape, isOpen, onClose]);

  const handleBackdropClick = (e) => {
    if (closeOnBackdrop && e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleClose = () => {
    announce('Modal closed', 'polite');
    onClose();
  };

  const modalClasses = [
    'modal',
    `modal-${size}`,
    isMobile && 'modal-mobile',
    className
  ].filter(Boolean).join(' ');

  if (!isOpen) return null;

  const modalContent = (
    <div 
      className="modal-backdrop"
      onClick={handleBackdropClick}
      role="presentation"
    >
      <div
        ref={modalRef}
        className={modalClasses}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? 'modal-title' : undefined}
        aria-describedby="modal-content"
        {...props}
      >
        <div className="modal-header">
          {title && (
            <h2 id="modal-title" className="modal-title">
              {title}
            </h2>
          )}
          <Button
            variant="outline-secondary"
            size="sm"
            onClick={handleClose}
            className="modal-close"
            ariaLabel="Close modal"
          >
            ×
          </Button>
        </div>
        
        <div id="modal-content" className="modal-body">
          {children}
        </div>
        
        {actions.length > 0 && (
          <div className="modal-footer">
            {actions.map((action, index) => (
              <Button
                key={index}
                variant={action.variant || 'primary'}
                onClick={action.onClick}
                disabled={action.disabled}
                loading={action.loading}
                className="modal-action-btn"
              >
                {action.label}
              </Button>
            ))}
          </div>
        )}
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
};

export default Modal;