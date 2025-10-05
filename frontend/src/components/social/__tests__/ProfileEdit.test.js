import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ProfileEdit from '../ProfileEdit';
import api from '../../../services/api';

// Mock the API
jest.mock('../../../services/api');

// Mock useNavigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

const mockCurrentUser = {
  user_id: 1,
  username: 'testuser',
  first_name: 'Test',
  last_name: 'User',
  email: 'test@example.com',
  bio: 'Test bio',
  website: 'https://example.com',
  location: 'Test City',
  birth_date: '1990-01-01',
  avatar_url: null,
  full_name: 'Test User'
};

const renderProfileEdit = (props = {}) => {
  return render(
    <BrowserRouter>
      <ProfileEdit currentUser={mockCurrentUser} {...props} />
    </BrowserRouter>
  );
};

describe('ProfileEdit Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders profile edit form with current user data', () => {
    renderProfileEdit();
    
    expect(screen.getByDisplayValue('Test')).toBeInTheDocument();
    expect(screen.getByDisplayValue('User')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test bio')).toBeInTheDocument();
    expect(screen.getByDisplayValue('https://example.com')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test City')).toBeInTheDocument();
    expect(screen.getByDisplayValue('1990-01-01')).toBeInTheDocument();
  });

  test('shows error when no current user provided', () => {
    render(
      <BrowserRouter>
        <ProfileEdit currentUser={null} />
      </BrowserRouter>
    );
    
    expect(screen.getByText('You must be logged in to edit your profile.')).toBeInTheDocument();
  });

  test('validates bio character limit', () => {
    renderProfileEdit();
    
    const bioTextarea = screen.getByLabelText('Bio');
    const longBio = 'a'.repeat(501);
    
    fireEvent.change(bioTextarea, { target: { value: longBio } });
    fireEvent.blur(bioTextarea);
    
    expect(screen.getByText('Bio cannot exceed 500 characters')).toBeInTheDocument();
  });

  test('validates website URL format', () => {
    renderProfileEdit();
    
    const websiteInput = screen.getByLabelText('Website');
    
    fireEvent.change(websiteInput, { target: { value: 'invalid-url' } });
    fireEvent.blur(websiteInput);
    
    expect(screen.getByText('Website must be a valid URL starting with http:// or https://')).toBeInTheDocument();
  });

  test('validates birth date is in the past', () => {
    renderProfileEdit();
    
    const birthDateInput = screen.getByLabelText('Birth Date');
    const futureDate = new Date();
    futureDate.setFullYear(futureDate.getFullYear() + 1);
    
    fireEvent.change(birthDateInput, { 
      target: { value: futureDate.toISOString().split('T')[0] } 
    });
    fireEvent.blur(birthDateInput);
    
    expect(screen.getByText('Birth date must be in the past')).toBeInTheDocument();
  });

  test('handles avatar file selection', () => {
    renderProfileEdit();
    
    const file = new File(['avatar'], 'avatar.jpg', { type: 'image/jpeg' });
    const avatarInput = screen.getByLabelText('Choose Photo');
    
    fireEvent.change(avatarInput, { target: { files: [file] } });
    
    // Should not show any error for valid image
    expect(screen.queryByText('Please select a valid image file')).not.toBeInTheDocument();
  });

  test('validates avatar file type', () => {
    renderProfileEdit();
    
    const file = new File(['document'], 'document.pdf', { type: 'application/pdf' });
    const avatarInput = screen.getByLabelText('Choose Photo');
    
    fireEvent.change(avatarInput, { target: { files: [file] } });
    
    expect(screen.getByText('Please select a valid image file')).toBeInTheDocument();
  });

  test('validates avatar file size', () => {
    renderProfileEdit();
    
    // Create a mock file larger than 5MB
    const largeFile = new File(['x'.repeat(6 * 1024 * 1024)], 'large.jpg', { type: 'image/jpeg' });
    Object.defineProperty(largeFile, 'size', { value: 6 * 1024 * 1024 });
    
    const avatarInput = screen.getByLabelText('Choose Photo');
    
    fireEvent.change(avatarInput, { target: { files: [largeFile] } });
    
    expect(screen.getByText('Image size must be less than 5MB')).toBeInTheDocument();
  });

  test('submits form with valid data', async () => {
    const mockOnProfileUpdate = jest.fn();
    api.put.mockResolvedValue({ data: { ...mockCurrentUser, bio: 'Updated bio' } });
    
    renderProfileEdit({ onProfileUpdate: mockOnProfileUpdate });
    
    const bioTextarea = screen.getByLabelText('Bio');
    fireEvent.change(bioTextarea, { target: { value: 'Updated bio' } });
    
    const submitButton = screen.getByText('Save Changes');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(api.put).toHaveBeenCalledWith('/api/auth/profile/', expect.any(FormData), {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
    });
    
    expect(mockOnProfileUpdate).toHaveBeenCalled();
    expect(screen.getByText('Profile updated successfully! Redirecting...')).toBeInTheDocument();
  });

  test('handles form submission error', async () => {
    api.put.mockRejectedValue({
      response: { data: { bio: ['Bio is required'] } }
    });
    
    renderProfileEdit();
    
    const submitButton = screen.getByText('Save Changes');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Bio is required')).toBeInTheDocument();
    });
  });

  test('handles cancel button click', () => {
    renderProfileEdit();
    
    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('/profile/1');
  });

  test('shows character count for bio', () => {
    renderProfileEdit();
    
    const bioTextarea = screen.getByLabelText('Bio');
    fireEvent.change(bioTextarea, { target: { value: 'Test bio content' } });
    
    expect(screen.getByText('17/500 characters')).toBeInTheDocument();
  });

  test('displays avatar placeholder when no avatar', () => {
    renderProfileEdit();
    
    expect(screen.getByText('T')).toBeInTheDocument(); // First letter of full name
  });
});