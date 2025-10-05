import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import './ProfileEdit.css';

/**
 * ProfileEdit component for editing user profile information
 * Includes avatar upload, bio editing, and personal information
 */
const ProfileEdit = ({ currentUser, onProfileUpdate }) => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    bio: '',
    website: '',
    location: '',
    birth_date: ''
  });
  const [avatar, setAvatar] = useState(null);
  const [avatarPreview, setAvatarPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (currentUser) {
      setFormData({
        first_name: currentUser.first_name || '',
        last_name: currentUser.last_name || '',
        bio: currentUser.bio || '',
        website: currentUser.website || '',
        location: currentUser.location || '',
        birth_date: currentUser.birth_date || ''
      });
      setAvatarPreview(currentUser.avatar_url);
    }
  }, [currentUser]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: null
      }));
    }
  };

  const handleAvatarChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        setErrors(prev => ({
          ...prev,
          avatar: 'Please select a valid image file'
        }));
        return;
      }

      // Validate file size (5MB limit)
      if (file.size > 5 * 1024 * 1024) {
        setErrors(prev => ({
          ...prev,
          avatar: 'Image size must be less than 5MB'
        }));
        return;
      }

      setAvatar(file);
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setAvatarPreview(e.target.result);
      };
      reader.readAsDataURL(file);
      
      // Clear avatar error
      if (errors.avatar) {
        setErrors(prev => ({
          ...prev,
          avatar: null
        }));
      }
    }
  };

  const validateForm = () => {
    const newErrors = {};

    // Validate bio length
    if (formData.bio && formData.bio.length > 500) {
      newErrors.bio = 'Bio cannot exceed 500 characters';
    }

    // Validate website URL
    if (formData.website && !formData.website.match(/^https?:\/\/.+/)) {
      newErrors.website = 'Website must be a valid URL starting with http:// or https://';
    }

    // Validate birth date
    if (formData.birth_date) {
      const birthDate = new Date(formData.birth_date);
      const today = new Date();
      if (birthDate >= today) {
        newErrors.birth_date = 'Birth date must be in the past';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setSuccess(false);

    try {
      // Create FormData for file upload
      const submitData = new FormData();
      
      // Add text fields
      Object.keys(formData).forEach(key => {
        if (formData[key]) {
          submitData.append(key, formData[key]);
        }
      });

      // Add avatar if selected
      if (avatar) {
        submitData.append('avatar', avatar);
      }

      const response = await api.put('/api/auth/profile/', submitData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setSuccess(true);
      
      // Call callback to update parent component
      if (onProfileUpdate) {
        onProfileUpdate(response.data);
      }

      // Show success message briefly then redirect
      setTimeout(() => {
        navigate(`/profile/${currentUser.user_id}`);
      }, 2000);

    } catch (error) {
      console.error('Error updating profile:', error);
      
      if (error.response?.data) {
        setErrors(error.response.data);
      } else {
        setErrors({
          general: 'Failed to update profile. Please try again.'
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    navigate(`/profile/${currentUser?.user_id || ''}`);
  };

  if (!currentUser) {
    return (
      <div className="profile-edit">
        <div className="error-message">
          You must be logged in to edit your profile.
        </div>
      </div>
    );
  }

  return (
    <div className="profile-edit">
      <div className="profile-edit-container">
        <div className="profile-edit-header">
          <h1>Edit Profile</h1>
          <p>Update your profile information and avatar</p>
        </div>

        {success && (
          <div className="success-message">
            Profile updated successfully! Redirecting...
          </div>
        )}

        {errors.general && (
          <div className="error-message">
            {errors.general}
          </div>
        )}

        <form onSubmit={handleSubmit} className="profile-edit-form">
          {/* Avatar Section */}
          <div className="form-section">
            <h3>Profile Picture</h3>
            <div className="avatar-upload">
              <div className="avatar-preview">
                {avatarPreview ? (
                  <img src={avatarPreview} alt="Avatar preview" />
                ) : (
                  <div className="avatar-placeholder">
                    {currentUser.full_name?.charAt(0)?.toUpperCase() || 'U'}
                  </div>
                )}
              </div>
              <div className="avatar-upload-controls">
                <input
                  type="file"
                  id="avatar"
                  accept="image/*"
                  onChange={handleAvatarChange}
                  className="avatar-input"
                />
                <label htmlFor="avatar" className="avatar-upload-btn">
                  Choose Photo
                </label>
                <p className="avatar-help">
                  JPG, PNG or GIF. Max size 5MB.
                </p>
              </div>
            </div>
            {errors.avatar && (
              <div className="field-error">{errors.avatar}</div>
            )}
          </div>

          {/* Personal Information */}
          <div className="form-section">
            <h3>Personal Information</h3>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="first_name">First Name</label>
                <input
                  type="text"
                  id="first_name"
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleInputChange}
                  maxLength="30"
                />
                {errors.first_name && (
                  <div className="field-error">{errors.first_name}</div>
                )}
              </div>
              <div className="form-group">
                <label htmlFor="last_name">Last Name</label>
                <input
                  type="text"
                  id="last_name"
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleInputChange}
                  maxLength="30"
                />
                {errors.last_name && (
                  <div className="field-error">{errors.last_name}</div>
                )}
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="bio">Bio</label>
              <textarea
                id="bio"
                name="bio"
                value={formData.bio}
                onChange={handleInputChange}
                rows="4"
                maxLength="500"
                placeholder="Tell us about yourself..."
              />
              <div className="character-count">
                {formData.bio.length}/500 characters
              </div>
              {errors.bio && (
                <div className="field-error">{errors.bio}</div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="location">Location</label>
              <input
                type="text"
                id="location"
                name="location"
                value={formData.location}
                onChange={handleInputChange}
                maxLength="100"
                placeholder="City, Country"
              />
              {errors.location && (
                <div className="field-error">{errors.location}</div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="website">Website</label>
              <input
                type="url"
                id="website"
                name="website"
                value={formData.website}
                onChange={handleInputChange}
                placeholder="https://yourwebsite.com"
              />
              {errors.website && (
                <div className="field-error">{errors.website}</div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="birth_date">Birth Date</label>
              <input
                type="date"
                id="birth_date"
                name="birth_date"
                value={formData.birth_date}
                onChange={handleInputChange}
              />
              {errors.birth_date && (
                <div className="field-error">{errors.birth_date}</div>
              )}
            </div>
          </div>

          {/* Form Actions */}
          <div className="form-actions">
            <button
              type="button"
              onClick={handleCancel}
              className="btn btn-secondary"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProfileEdit;