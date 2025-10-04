import React from 'react';
import { render, screen } from '@testing-library/react';
import FormErrorDisplay from './FormErrorDisplay';

describe('FormErrorDisplay', () => {
  it('renders nothing when no errors are provided', () => {
    const { container } = render(<FormErrorDisplay errors={{}} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders nothing when errors object is null', () => {
    const { container } = render(<FormErrorDisplay errors={null} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders errors correctly', () => {
    const errors = {
      title: 'Title is required',
      content: 'Content must be at least 10 characters',
      author: 'Author is required'
    };

    render(<FormErrorDisplay errors={errors} />);

    expect(screen.getByText('Please fix the following errors:')).toBeInTheDocument();
    expect(screen.getByText('Title:')).toBeInTheDocument();
    expect(screen.getByText('Title is required')).toBeInTheDocument();
    expect(screen.getByText('Content:')).toBeInTheDocument();
    expect(screen.getByText('Content must be at least 10 characters')).toBeInTheDocument();
    expect(screen.getByText('Author:')).toBeInTheDocument();
    expect(screen.getByText('Author is required')).toBeInTheDocument();
  });

  it('formats field names correctly', () => {
    const errors = {
      firstName: 'First name is required',
      email_address: 'Email address is invalid',
      phoneNumber: 'Phone number is required'
    };

    render(<FormErrorDisplay errors={errors} />);

    expect(screen.getByText('First Name:')).toBeInTheDocument();
    expect(screen.getByText('Email address:')).toBeInTheDocument();
    expect(screen.getByText('Phone Number:')).toBeInTheDocument();
  });

  it('uses custom title when provided', () => {
    const errors = {
      title: 'Title is required'
    };

    render(<FormErrorDisplay errors={errors} title="Custom error message:" />);

    expect(screen.getByText('Custom error message:')).toBeInTheDocument();
  });

  it('orders errors according to fieldOrder when provided', () => {
    const errors = {
      author: 'Author is required',
      title: 'Title is required',
      content: 'Content is required'
    };

    const fieldOrder = ['title', 'content', 'author'];

    render(<FormErrorDisplay errors={errors} fieldOrder={fieldOrder} />);

    const errorItems = screen.getAllByRole('listitem');
    expect(errorItems[0]).toHaveTextContent('Title:');
    expect(errorItems[1]).toHaveTextContent('Content:');
    expect(errorItems[2]).toHaveTextContent('Author:');
  });

  it('ignores null or empty error values', () => {
    const errors = {
      title: 'Title is required',
      content: null,
      author: '',
      tags: 'Tags are invalid'
    };

    render(<FormErrorDisplay errors={errors} />);

    expect(screen.getByText('Title:')).toBeInTheDocument();
    expect(screen.getByText('Tags:')).toBeInTheDocument();
    expect(screen.queryByText('Content:')).not.toBeInTheDocument();
    expect(screen.queryByText('Author:')).not.toBeInTheDocument();
  });
});