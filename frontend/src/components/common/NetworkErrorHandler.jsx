import React from 'react';
import ErrorMessage from './ErrorMessage';
import { ERROR_TYPES } from '../../services/apiConfig';
import './NetworkErrorHandler.css';

/**
 * NetworkErrorHandler component for handling different types of network errors
 * @param {Object} props - Component props
 * @param {Object} props.error - Error object from API
 * @param {Function} props.onRetry - Retry function
 * @param {string} props.operation - Description of the operation that failed
 * @param {boolean} props.showDetails - Whether to show detailed error information
 */
const NetworkErrorHandler = ({ 
  error, 
  onRetry, 
  operation = "operation", 
  showDetails = false 
}) => {
  if (!error) {
    return null;
  }

  const getErrorContent = () => {
    switch (error.type) {
      case ERROR_TYPES.NETWORK_ERROR:
        return {
          title: "Connection Problem",
          message: `Unable to connect to the server. Please check your internet connection and try again.`,
          icon: "🌐",
          type: "error",
          suggestions: [
            "Check your internet connection",
            "Try refreshing the page",
            "Contact support if the problem persists"
          ]
        };

      case ERROR_TYPES.NOT_FOUND:
        return {
          title: "Not Found",
          message: `The requested resource could not be found.`,
          icon: "🔍",
          type: "warning",
          suggestions: [
            "Check if the item still exists",
            "Try going back and selecting again",
            "The item may have been deleted"
          ]
        };

      case ERROR_TYPES.VALIDATION_ERROR:
        return {
          title: "Validation Error",
          message: `The ${operation} failed due to invalid data.`,
          icon: "⚠️",
          type: "warning",
          suggestions: [
            "Check all required fields are filled",
            "Ensure data meets the specified format",
            "Review any field-specific error messages"
          ]
        };

      case ERROR_TYPES.SERVER_ERROR:
        return {
          title: "Server Error",
          message: `A server error occurred while processing your ${operation}.`,
          icon: "🔧",
          type: "error",
          suggestions: [
            "Try again in a few moments",
            "The issue is on our end, not yours",
            "Contact support if the problem continues"
          ]
        };

      case ERROR_TYPES.API_ERROR:
        return {
          title: "API Error",
          message: `An error occurred while communicating with the server.`,
          icon: "⚡",
          type: "error",
          suggestions: [
            "Try the operation again",
            "Check if you have the necessary permissions",
            "Contact support if needed"
          ]
        };

      default:
        return {
          title: "Unexpected Error",
          message: `An unexpected error occurred during ${operation}.`,
          icon: "❌",
          type: "error",
          suggestions: [
            "Try refreshing the page",
            "Try the operation again",
            "Contact support if the issue persists"
          ]
        };
    }
  };

  const errorContent = getErrorContent();

  return (
    <div className="network-error-handler">
      <div className="network-error-main">
        <div className="network-error-icon">
          {errorContent.icon}
        </div>
        
        <div className="network-error-content">
          <h3 className="network-error-title">
            {errorContent.title}
          </h3>
          
          <ErrorMessage 
            error={errorContent.message}
            type={errorContent.type}
            onRetry={onRetry}
          />
        </div>
      </div>

      {showDetails && (
        <div className="network-error-details">
          <details className="error-details-section">
            <summary>What can you do?</summary>
            <ul className="error-suggestions">
              {errorContent.suggestions.map((suggestion, index) => (
                <li key={index}>{suggestion}</li>
              ))}
            </ul>
          </details>

          {error.status && (
            <div className="error-technical-info">
              <small>
                <strong>Status:</strong> {error.status}
                {error.details && (
                  <>
                    {" | "}
                    <strong>Details:</strong> {JSON.stringify(error.details)}
                  </>
                )}
              </small>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NetworkErrorHandler;