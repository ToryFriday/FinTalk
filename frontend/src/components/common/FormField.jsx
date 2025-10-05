import React, { forwardRef, useId } from 'react';
import './FormField.css';

/**
 * Accessible form field component with validation
 * @param {Object} props - Component props
 * @param {string} props.label - Field label
 * @param {string} props.type - Input type
 * @param {string} props.value - Field value
 * @param {Function} props.onChange - Change handler
 * @param {Function} props.onBlur - Blur handler
 * @param {string} props.error - Error message
 * @param {string} props.helpText - Help text
 * @param {boolean} props.required - Required field
 * @param {boolean} props.disabled - Disabled state
 * @param {string} props.placeholder - Placeholder text
 * @param {string} props.className - Additional CSS classes
 * @param {Object} props.validation - Validation rules
 */
const FormField = forwardRef(({
  label,
  type = 'text',
  value = '',
  onChange,
  onBlur,
  error,
  helpText,
  required = false,
  disabled = false,
  placeholder,
  className = '',
  validation = {},
  ...props
}, ref) => {
  const fieldId = useId();
  const errorId = useId();
  const helpId = useId();

  const handleChange = (e) => {
    if (onChange) {
      onChange(e);
    }
  };

  const handleBlur = (e) => {
    if (onBlur) {
      onBlur(e);
    }
  };

  const fieldClasses = [
    'form-control',
    error && 'form-control-error',
    className
  ].filter(Boolean).join(' ');

  const ariaDescribedBy = [
    error && errorId,
    helpText && helpId
  ].filter(Boolean).join(' ');

  return (
    <div className="form-group">
      {label && (
        <label 
          htmlFor={fieldId} 
          className="form-label"
        >
          {label}
          {required && (
            <span className="form-required" aria-label="required">
              *
            </span>
          )}
        </label>
      )}
      
      {type === 'textarea' ? (
        <textarea
          ref={ref}
          id={fieldId}
          className={fieldClasses}
          value={value}
          onChange={handleChange}
          onBlur={handleBlur}
          disabled={disabled}
          placeholder={placeholder}
          required={required}
          aria-describedby={ariaDescribedBy || undefined}
          aria-invalid={error ? 'true' : 'false'}
          rows={4}
          {...props}
        />
      ) : (
        <input
          ref={ref}
          id={fieldId}
          type={type}
          className={fieldClasses}
          value={value}
          onChange={handleChange}
          onBlur={handleBlur}
          disabled={disabled}
          placeholder={placeholder}
          required={required}
          aria-describedby={ariaDescribedBy || undefined}
          aria-invalid={error ? 'true' : 'false'}
          {...props}
        />
      )}
      
      {helpText && (
        <div id={helpId} className="form-text">
          {helpText}
        </div>
      )}
      
      {error && (
        <div 
          id={errorId} 
          className="form-error" 
          role="alert"
          aria-live="polite"
        >
          {error}
        </div>
      )}
    </div>
  );
});

FormField.displayName = 'FormField';

export default FormField;