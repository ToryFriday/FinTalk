import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import PostCard from './PostCard';

const mockPost = {
  id: 1,
  title: 'Test Post Title',
  content: 'This is a test post content that should be displayed in the card component.',
  author: 'Test Author',
  tags: 'react, testing, javascript',
  image_url: 'https://example.com/image.jpg',
  created_at: '2023-01-01T12:00:00Z',
  updated_at: '2023-01-01T12:00:00Z'
};

describe('PostCard Component', () => {
  const renderWithRouter = (component) => {
    return render(
      <MemoryRouter>
        {component}
      </MemoryRouter>
    );
  };

  test('renders post information correctly', () => {
    renderWithRouter(<PostCard post={mockPost} onDelete={jest.fn()} />);
    
    expect(screen.getByText('Test Post Title')).toBeInTheDocument();
    expect(screen.getByText(/This is a test post content/)).toBeInTheDocument();
    expect(screen.getByText('By Test Author')).toBeInTheDocument();
  });

  test('renders action buttons', () => {
    renderWithRouter(<PostCard post={mockPost} onDelete={jest.fn()} />);
    
    expect(screen.getByText('View')).toBeInTheDocument();
    expect(screen.getByText('Edit')).toBeInTheDocument();
    expect(screen.getByText('Delete')).toBeInTheDocument();
  });

  test('calls onDelete when delete button is clicked', () => {
    const mockOnDelete = jest.fn();
    renderWithRouter(<PostCard post={mockPost} onDelete={mockOnDelete} />);
    
    const deleteButton = screen.getByText('Delete');
    fireEvent.click(deleteButton);
    
    expect(mockOnDelete).toHaveBeenCalledWith(1);
  });

  test('renders tags correctly', () => {
    renderWithRouter(<PostCard post={mockPost} onDelete={jest.fn()} />);
    
    expect(screen.getByText('react')).toBeInTheDocument();
    expect(screen.getByText('testing')).toBeInTheDocument();
    expect(screen.getByText('javascript')).toBeInTheDocument();
  });
});