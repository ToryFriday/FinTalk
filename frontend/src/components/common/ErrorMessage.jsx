import React from 'react';
import { formatErrorMessage } from '../../services/api';
import './ErrorMessage.css';

/**
 * ErrorMessage component for displaying error states
 * @param {Object} props - Component props
 * @param {Object|string} props.error - Error object or string message
 * @param {Function} props.onRetry - Optional retry function
 * @param {string} props.type - Error type ('error', 'warning', 'info')
 */
const ErrorMessage = ({ error, onRetry, type = 'error' }) => {
  const getErrorMessage = () => {
    if (typeof error === 'string') {
      return error;
    }
    if (error && typeof error === 'object') {
      return formatErrorMessage(error);
    }
    return 'An unexpected error occurred';
  };

  return (
    <div className={`error-message ${type}`}>
      <div className="error-content">
        <div className="error-icon">
          {type === 'error' && '⚠️'}
          {type === 'warning' && '⚠️'}
          {type === 'info' && 'ℹ️'}
        </div>
        <div className="error-text">
          <p className="error-title">
            {type === 'error' && 'Error'}
            {type === 'warning' && 'Warning'}
            {type === 'info' && 'Information'}
          </p>
          <p className="error-description">{getErrorMessage()}</p>
        </div>
      </div>
      {onRetry && (
        <button 
          className="retry-button" 
          onClick={onRetry}
          type="button"
        >
          Try Again
        </button>
      )}
    </div>
  );
};

export default ErrorMessage;