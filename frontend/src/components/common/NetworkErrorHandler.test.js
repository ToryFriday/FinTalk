import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import NetworkErrorHandler from './NetworkErrorHandler';
import { ERROR_TYPES } from '../../services/apiConfig';

describe('NetworkErrorHandler', () => {
  const mockOnRetry = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders nothing when no error is provided', () => {
    const { container } = render(
      <NetworkErrorHandler error={null} onRetry={mockOnRetry} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders network error correctly', () => {
    const error = {
      type: ERROR_TYPES.NETWORK_ERROR,
      message: 'Network error occurred'
    };

    render(
      <NetworkErrorHandler 
        error={error} 
        onRetry={mockOnRetry} 
        operation="loading data"
      />
    );

    expect(screen.getByText('Connection Problem')).toBeInTheDocument();
    expect(screen.getByText(/unable to connect to the server/i)).toBeInTheDocument();
    expect(screen.getByText('Try Again')).toBeInTheDocument();
  });

  it('renders not found error correctly', () => {
    const error = {
      type: ERROR_TYPES.NOT_FOUND,
      message: 'Resource not found'
    };

    render(
      <NetworkErrorHandler 
        error={error} 
        onRetry={mockOnRetry} 
        operation="fetching post"
      />
    );

    expect(screen.getByText('Not Found')).toBeInTheDocument();
    expect(screen.getByText(/the requested resource could not be found/i)).toBeInTheDocument();
  });

  it('renders validation error correctly', () => {
    const error = {
      type: ERROR_TYPES.VALIDATION_ERROR,
      message: 'Validation failed'
    };

    render(
      <NetworkErrorHandler 
        error={error} 
        onRetry={mockOnRetry} 
        operation="saving post"
      />
    );

    expect(screen.getByText('Validation Error')).toBeInTheDocument();
    expect(screen.getByText(/the saving post failed due to invalid data/i)).toBeInTheDocument();
  });

  it('renders server error correctly', () => {
    const error = {
      type: ERROR_TYPES.SERVER_ERROR,
      message: 'Internal server error'
    };

    render(
      <NetworkErrorHandler 
        error={error} 
        onRetry={mockOnRetry} 
        operation="processing request"
      />
    );

    expect(screen.getByText('Server Error')).toBeInTheDocument();
    expect(screen.getByText(/a server error occurred while processing your processing request/i)).toBeInTheDocument();
  });

  it('renders unknown error correctly', () => {
    const error = {
      type: 'UNKNOWN_TYPE',
      message: 'Something went wrong'
    };

    render(
      <NetworkErrorHandler 
        error={error} 
        onRetry={mockOnRetry} 
        operation="operation"
      />
    );

    expect(screen.getByText('Unexpected Error')).toBeInTheDocument();
    expect(screen.getByText(/an unexpected error occurred during operation/i)).toBeInTheDocument();
  });

  it('calls onRetry when retry button is clicked', () => {
    const error = {
      type: ERROR_TYPES.NETWORK_ERROR,
      message: 'Network error'
    };

    render(
      <NetworkErrorHandler 
        error={error} 
        onRetry={mockOnRetry} 
        operation="loading data"
      />
    );

    fireEvent.click(screen.getByText('Try Again'));
    expect(mockOnRetry).toHaveBeenCalledTimes(1);
  });

  it('shows detailed information when showDetails is true', () => {
    const error = {
      type: ERROR_TYPES.NETWORK_ERROR,
      message: 'Network error',
      status: 500,
      details: { message: 'Server unavailable' }
    };

    render(
      <NetworkErrorHandler 
        error={error} 
        onRetry={mockOnRetry} 
        operation="loading data"
        showDetails={true}
      />
    );

    expect(screen.getByText('What can you do?')).toBeInTheDocument();
    expect(screen.getByText(/status:/i)).toBeInTheDocument();
    expect(screen.getByText(/500/)).toBeInTheDocument();
  });

  it('hides detailed information when showDetails is false', () => {
    const error = {
      type: ERROR_TYPES.NETWORK_ERROR,
      message: 'Network error',
      status: 500
    };

    render(
      <NetworkErrorHandler 
        error={error} 
        onRetry={mockOnRetry} 
        operation="loading data"
        showDetails={false}
      />
    );

    expect(screen.queryByText('What can you do?')).not.toBeInTheDocument();
    expect(screen.queryByText('Status:')).not.toBeInTheDocument();
  });
});