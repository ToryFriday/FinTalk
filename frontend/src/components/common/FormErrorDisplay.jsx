import React from 'react';
import './FormErrorDisplay.css';

/**
 * FormErrorDisplay component for displaying form validation errors
 * @param {Object} props - Component props
 * @param {Object} props.errors - Object containing field errors
 * @param {Array} props.fieldOrder - Optional array to control error display order
 * @param {string} props.title - Optional title for the error section
 */
const FormErrorDisplay = ({ 
  errors, 
  fieldOrder = null, 
  title = "Please fix the following errors:" 
}) => {
  if (!errors || Object.keys(errors).length === 0) {
    return null;
  }

  // Get error entries in specified order or default order
  const getErrorEntries = () => {
    const errorEntries = Object.entries(errors).filter(([_, error]) => error);
    
    if (fieldOrder) {
      // Sort by specified field order
      return errorEntries.sort(([fieldA], [fieldB]) => {
        const indexA = fieldOrder.indexOf(fieldA);
        const indexB = fieldOrder.indexOf(fieldB);
        
        // If field not in order array, put it at the end
        if (indexA === -1) return 1;
        if (indexB === -1) return -1;
        
        return indexA - indexB;
      });
    }
    
    return errorEntries;
  };

  const errorEntries = getErrorEntries();

  return (
    <div className="form-error-display">
      <div className="form-error-header">
        <span className="form-error-icon">⚠️</span>
        <h4 className="form-error-title">{title}</h4>
      </div>
      
      <ul className="form-error-list">
        {errorEntries.map(([field, error]) => (
          <li key={field} className="form-error-item">
            <strong className="form-error-field">
              {formatFieldName(field)}:
            </strong>
            <span className="form-error-message">{error}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

/**
 * Format field name for display
 * @param {string} fieldName - The field name to format
 * @returns {string} Formatted field name
 */
const formatFieldName = (fieldName) => {
  // Convert camelCase or snake_case to Title Case
  return fieldName
    .replace(/([A-Z])/g, ' $1') // Add space before capital letters
    .replace(/_/g, ' ') // Replace underscores with spaces
    .replace(/^./, str => str.toUpperCase()) // Capitalize first letter
    .trim();
};

export default FormErrorDisplay;