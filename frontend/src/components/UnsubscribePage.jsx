import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';

const UnsubscribePage = () => {
  const { token } = useParams();
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [reason, setReason] = useState('');
  const [feedback, setFeedback] = useState('');
  const [unsubscribed, setUnsubscribed] = useState(false);

  const reasonOptions = [
    { value: 'too_frequent', label: 'Too Many Emails' },
    { value: 'not_interested', label: 'Not Interested Anymore' },
    { value: 'wrong_email', label: 'Wrong Email Address' },
    { value: 'spam', label: 'Marked as Spam' },
    { value: 'other', label: 'Other Reason' },
  ];

  useEffect(() => {
    loadSubscriptionDetails();
  }, [token]);

  const loadSubscriptionDetails = async () => {
    try {
      const response = await axios.get(`/api/notifications/unsubscribe/${token}/`);
      setSubscription(response.data);
    } catch (error) {
      setMessage('Invalid or expired unsubscribe link.');
    } finally {
      setLoading(false);
    }
  };

  const handleUnsubscribe = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`/api/notifications/unsubscribe/${token}/`, {
        reason,
        feedback
      });

      setMessage('You have been successfully unsubscribed from our mailing list.');
      setUnsubscribed(true);
    } catch (error) {
      if (error.response?.data?.detail) {
        setMessage(error.response.data.detail);
      } else {
        setMessage('An error occurred. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="unsubscribe-page">
        <div className="container">
          <div className="loading">Loading...</div>
        </div>
      </div>
    );
  }

  if (unsubscribed) {
    return (
      <div className="unsubscribe-page">
        <div className="container">
          <div className="success-message">
            <h2>✓ Successfully Unsubscribed</h2>
            <p>{message}</p>
            <p>We're sorry to see you go. You can resubscribe at any time by visiting our website.</p>
            <a href="/" className="btn">Return to Homepage</a>
          </div>
        </div>
      </div>
    );
  }

  if (!subscription) {
    return (
      <div className="unsubscribe-page">
        <div className="container">
          <div className="error-message">
            <h2>Invalid Link</h2>
            <p>{message}</p>
            <a href="/" className="btn">Return to Homepage</a>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="unsubscribe-page">
      <div className="container">
        <div className="unsubscribe-form">
          <h2>Unsubscribe from Email Notifications</h2>
          
          <div className="subscription-details">
            <p><strong>Email:</strong> {subscription.email}</p>
            <p><strong>Subscription Type:</strong> {subscription.subscription_type}</p>
          </div>

          <p>We're sorry to see you go! Before you unsubscribe, please let us know why:</p>

          <form onSubmit={handleUnsubscribe}>
            <div className="form-group">
              <label htmlFor="reason">Reason for unsubscribing:</label>
              <select
                id="reason"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              >
                <option value="">Select a reason (optional)</option>
                {reasonOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="feedback">Additional feedback (optional):</label>
              <textarea
                id="feedback"
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder="Tell us how we can improve..."
                rows="4"
              />
            </div>

            <div className="form-actions">
              <button type="submit" className="btn btn-danger" disabled={loading}>
                {loading ? 'Unsubscribing...' : 'Confirm Unsubscribe'}
              </button>
              <a href="/" className="btn btn-secondary">Keep Subscription</a>
            </div>
          </form>

          {message && (
            <div className="message error">
              {message}
            </div>
          )}
        </div>
      </div>

      <style jsx>{`
        .unsubscribe-page {
          min-height: 100vh;
          background: #f8f9fa;
          padding: 40px 20px;
        }

        .container {
          max-width: 600px;
          margin: 0 auto;
        }

        .unsubscribe-form,
        .success-message,
        .error-message {
          background: white;
          padding: 40px;
          border-radius: 8px;
          box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .subscription-details {
          background: #f8f9fa;
          padding: 20px;
          border-radius: 6px;
          margin: 20px 0;
        }

        .form-group {
          margin-bottom: 20px;
        }

        .form-group label {
          display: block;
          margin-bottom: 8px;
          font-weight: bold;
          color: #333;
        }

        .form-group select,
        .form-group textarea {
          width: 100%;
          padding: 12px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 16px;
          font-family: inherit;
        }

        .form-group textarea {
          resize: vertical;
        }

        .form-actions {
          display: flex;
          gap: 15px;
          margin-top: 30px;
        }

        .btn {
          padding: 12px 24px;
          border: none;
          border-radius: 4px;
          text-decoration: none;
          font-size: 16px;
          cursor: pointer;
          display: inline-block;
          text-align: center;
        }

        .btn-danger {
          background: #dc3545;
          color: white;
        }

        .btn-danger:hover {
          background: #c82333;
        }

        .btn-secondary {
          background: #6c757d;
          color: white;
        }

        .btn-secondary:hover {
          background: #5a6268;
        }

        .btn:disabled {
          background: #ccc;
          cursor: not-allowed;
        }

        .loading {
          text-align: center;
          padding: 40px;
          font-size: 18px;
        }

        .success-message {
          text-align: center;
        }

        .success-message h2 {
          color: #28a745;
          margin-bottom: 20px;
        }

        .error-message {
          text-align: center;
        }

        .error-message h2 {
          color: #dc3545;
          margin-bottom: 20px;
        }

        .message {
          margin-top: 20px;
          padding: 15px;
          border-radius: 4px;
        }

        .message.error {
          background: #f8d7da;
          color: #721c24;
          border: 1px solid #f5c6cb;
        }
      `}</style>
    </div>
  );
};

export default UnsubscribePage;