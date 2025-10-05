/**
 * Comprehensive form validation utilities with accessibility support
 */

/**
 * Validation rule types
 */
export const VALIDATION_RULES = {
  REQUIRED: 'required',
  EMAIL: 'email',
  MIN_LENGTH: 'minLength',
  MAX_LENGTH: 'maxLength',
  PATTERN: 'pattern',
  CUSTOM: 'custom',
  CONFIRM: 'confirm'
};

/**
 * Default error messages
 */
export const DEFAULT_ERROR_MESSAGES = {
  required: 'This field is required',
  email: 'Please enter a valid email address',
  minLength: 'Must be at least {min} characters long',
  maxLength: 'Must be no more than {max} characters long',
  pattern: 'Please enter a valid format',
  confirm: 'Fields do not match',
  custom: 'Invalid value'
};

/**
 * Common validation patterns
 */
export const VALIDATION_PATTERNS = {
  email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  phone: /^\+?[\d\s\-\(\)]+$/,
  url: /^https?:\/\/.+/,
  password: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/,
  alphanumeric: /^[a-zA-Z0-9]+$/,
  numeric: /^\d+$/
};

/**
 * Validate a single field value against rules
 * @param {*} value - Field value
 * @param {Array} rules - Validation rules
 * @param {Object} allValues - All form values (for confirm validation)
 * @returns {string|null} Error message or null if valid
 */
export const validateField = (value, rules = [], allValues = {}) => {
  for (const rule of rules) {
    const error = validateRule(value, rule, allValues);
    if (error) {
      return error;
    }
  }
  return null;
};

/**
 * Validate a single rule
 * @param {*} value - Field value
 * @param {Object} rule - Validation rule
 * @param {Object} allValues - All form values
 * @returns {string|null} Error message or null if valid
 */
export const validateRule = (value, rule, allValues = {}) => {
  const { type, message, ...params } = rule;

  switch (type) {
    case VALIDATION_RULES.REQUIRED:
      if (!value || (typeof value === 'string' && value.trim() === '')) {
        return message || DEFAULT_ERROR_MESSAGES.required;
      }
      break;

    case VALIDATION_RULES.EMAIL:
      if (value && !VALIDATION_PATTERNS.email.test(value)) {
        return message || DEFAULT_ERROR_MESSAGES.email;
      }
      break;

    case VALIDATION_RULES.MIN_LENGTH:
      if (value && value.length < params.min) {
        return message || DEFAULT_ERROR_MESSAGES.minLength.replace('{min}', params.min);
      }
      break;

    case VALIDATION_RULES.MAX_LENGTH:
      if (value && value.length > params.max) {
        return message || DEFAULT_ERROR_MESSAGES.maxLength.replace('{max}', params.max);
      }
      break;

    case VALIDATION_RULES.PATTERN:
      if (value && !params.pattern.test(value)) {
        return message || DEFAULT_ERROR_MESSAGES.pattern;
      }
      break;

    case VALIDATION_RULES.CONFIRM:
      if (value !== allValues[params.field]) {
        return message || DEFAULT_ERROR_MESSAGES.confirm;
      }
      break;

    case VALIDATION_RULES.CUSTOM:
      if (params.validator && !params.validator(value, allValues)) {
        return message || DEFAULT_ERROR_MESSAGES.custom;
      }
      break;

    default:
      break;
  }

  return null;
};

/**
 * Validate entire form
 * @param {Object} values - Form values
 * @param {Object} validationSchema - Validation schema
 * @returns {Object} Errors object
 */
export const validateForm = (values, validationSchema) => {
  const errors = {};

  Object.keys(validationSchema).forEach(fieldName => {
    const fieldRules = validationSchema[fieldName];
    const fieldValue = values[fieldName];
    const error = validateField(fieldValue, fieldRules, values);
    
    if (error) {
      errors[fieldName] = error;
    }
  });

  return errors;
};

/**
 * Check if form has any errors
 * @param {Object} errors - Errors object
 * @returns {boolean} True if form has errors
 */
export const hasFormErrors = (errors) => {
  return Object.keys(errors).length > 0;
};

/**
 * Get first error message from errors object
 * @param {Object} errors - Errors object
 * @returns {string|null} First error message or null
 */
export const getFirstError = (errors) => {
  const errorKeys = Object.keys(errors);
  return errorKeys.length > 0 ? errors[errorKeys[0]] : null;
};

/**
 * Create validation schema helpers
 */
export const createValidationRule = (type, params = {}, message = null) => ({
  type,
  message,
  ...params
});

export const required = (message) => 
  createValidationRule(VALIDATION_RULES.REQUIRED, {}, message);

export const email = (message) => 
  createValidationRule(VALIDATION_RULES.EMAIL, {}, message);

export const minLength = (min, message) => 
  createValidationRule(VALIDATION_RULES.MIN_LENGTH, { min }, message);

export const maxLength = (max, message) => 
  createValidationRule(VALIDATION_RULES.MAX_LENGTH, { max }, message);

export const pattern = (regex, message) => 
  createValidationRule(VALIDATION_RULES.PATTERN, { pattern: regex }, message);

export const confirm = (field, message) => 
  createValidationRule(VALIDATION_RULES.CONFIRM, { field }, message);

export const custom = (validator, message) => 
  createValidationRule(VALIDATION_RULES.CUSTOM, { validator }, message);

/**
 * Common validation schemas
 */
export const COMMON_SCHEMAS = {
  login: {
    email: [required(), email()],
    password: [required(), minLength(6)]
  },
  
  register: {
    email: [required(), email()],
    password: [
      required(),
      minLength(8, 'Password must be at least 8 characters'),
      pattern(
        VALIDATION_PATTERNS.password,
        'Password must contain at least one uppercase letter, one lowercase letter, and one number'
      )
    ],
    confirmPassword: [
      required(),
      confirm('password', 'Passwords do not match')
    ],
    firstName: [required(), maxLength(50)],
    lastName: [required(), maxLength(50)]
  },
  
  post: {
    title: [required(), minLength(3), maxLength(200)],
    content: [required(), minLength(10)],
    author: [required(), maxLength(100)]
  },
  
  profile: {
    bio: [maxLength(500)],
    website: [pattern(VALIDATION_PATTERNS.url, 'Please enter a valid URL')],
    phone: [pattern(VALIDATION_PATTERNS.phone, 'Please enter a valid phone number')]
  }
};

/**
 * Real-time validation hook
 * @param {Object} initialValues - Initial form values
 * @param {Object} validationSchema - Validation schema
 * @returns {Object} Form state and handlers
 */
export const useFormValidation = (initialValues = {}, validationSchema = {}) => {
  const [values, setValues] = React.useState(initialValues);
  const [errors, setErrors] = React.useState({});
  const [touched, setTouched] = React.useState({});
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const validateSingleField = React.useCallback((name, value) => {
    const fieldRules = validationSchema[name];
    if (!fieldRules) return null;
    
    return validateField(value, fieldRules, values);
  }, [validationSchema, values]);

  const handleChange = React.useCallback((name, value) => {
    setValues(prev => ({ ...prev, [name]: value }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  }, [errors]);

  const handleBlur = React.useCallback((name) => {
    setTouched(prev => ({ ...prev, [name]: true }));
    
    const error = validateSingleField(name, values[name]);
    if (error) {
      setErrors(prev => ({ ...prev, [name]: error }));
    }
  }, [validateSingleField, values]);

  const handleSubmit = React.useCallback(async (onSubmit) => {
    setIsSubmitting(true);
    
    // Validate all fields
    const formErrors = validateForm(values, validationSchema);
    setErrors(formErrors);
    
    // Mark all fields as touched
    const allTouched = Object.keys(validationSchema).reduce((acc, key) => {
      acc[key] = true;
      return acc;
    }, {});
    setTouched(allTouched);
    
    if (!hasFormErrors(formErrors)) {
      try {
        await onSubmit(values);
      } catch (error) {
        console.error('Form submission error:', error);
      }
    }
    
    setIsSubmitting(false);
  }, [values, validationSchema]);

  const reset = React.useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
    setIsSubmitting(false);
  }, [initialValues]);

  const isValid = !hasFormErrors(errors);
  const canSubmit = isValid && !isSubmitting;

  return {
    values,
    errors,
    touched,
    isSubmitting,
    isValid,
    canSubmit,
    handleChange,
    handleBlur,
    handleSubmit,
    reset,
    setFieldValue: (name, value) => setValues(prev => ({ ...prev, [name]: value })),
    setFieldError: (name, error) => setErrors(prev => ({ ...prev, [name]: error })),
    clearFieldError: (name) => setErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors[name];
      return newErrors;
    })
  };
};

// Import React for the hook
import React from 'react';