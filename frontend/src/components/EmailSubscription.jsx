import React, { useState, useEffect } from 'react';
import axios from 'axios';

const EmailSubscription = () => {
  const [email, setEmail] = useState('');
  const [subscriptionType, setSubscriptionType] = useState('all_posts');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [subscriptions, setSubscriptions] = useState([]);

  const subscriptionTypes = [
    { value: 'all_posts', label: 'All New Posts' },
    { value: 'weekly_digest', label: 'Weekly Digest' },
    { value: 'featured_posts', label: 'Featured Posts Only' },
  ];

  useEffect(() => {
    // Load user's existing subscriptions if authenticated
    const token = localStorage.getItem('token');
    if (token) {
      loadSubscriptions();
    }
  }, []);

  const loadSubscriptions = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('/api/notifications/subscriptions/', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSubscriptions(response.data.results || []);
    } catch (error) {
      console.error('Error loading subscriptions:', error);
    }
  };

  const handleSubscribe = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const response = await axios.post('/api/notifications/subscribe/', {
        email,
        subscription_type: subscriptionType
      });

      setMessage('Successfully subscribed! Please check your email for confirmation.');
      setEmail('');
      
      // Reload subscriptions if user is authenticated
      const token = localStorage.getItem('token');
      if (token) {
        loadSubscriptions();
      }
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

  const handleUnsubscribe = async (subscriptionId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`/api/notifications/subscriptions/${subscriptionId}/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setMessage('Successfully unsubscribed.');
      loadSubscriptions();
    } catch (error) {
      setMessage('Error unsubscribing. Please try again.');
    }
  };

  return (
    <div className="email-subscription">
      <div className="subscription-form">
        <h3>Subscribe to Email Notifications</h3>
        <form onSubmit={handleSubscribe}>
          <div className="form-group">
            <label htmlFor="email">Email Address:</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="Enter your email address"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="subscriptionType">Subscription Type:</label>
            <select
              id="subscriptionType"
              value={subscriptionType}
              onChange={(e) => setSubscriptionType(e.target.value)}
            >
              {subscriptionTypes.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>
          
          <button type="submit" disabled={loading}>
            {loading ? 'Subscribing...' : 'Subscribe'}
          </button>
        </form>
        
        {message && (
          <div className={`message ${message.includes('Successfully') ? 'success' : 'error'}`}>
            {message}
          </div>
        )}
      </div>

      {subscriptions.length > 0 && (
        <div className="current-subscriptions">
          <h3>Your Current Subscriptions</h3>
          <div className="subscriptions-list">
            {subscriptions.map(subscription => (
              <div key={subscription.id} className="subscription-item">
                <div className="subscription-info">
                  <strong>{subscription.email}</strong>
                  <span className="subscription-type">
                    {subscriptionTypes.find(t => t.value === subscription.subscription_type)?.label}
                  </span>
                  <span className={`status ${subscription.is_active ? 'active' : 'inactive'}`}>
                    {subscription.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                {subscription.is_active && (
                  <button
                    onClick={() => handleUnsubscribe(subscription.id)}
                    className="unsubscribe-btn"
                  >
                    Unsubscribe
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <style jsx>{`
        .email-subscription {
          max-width: 600px;
          margin: 0 auto;
          padding: 20px;
        }

        .subscription-form {
          background: #f9f9f9;
          padding: 20px;
          border-radius: 8px;
          margin-bottom: 30px;
        }

        .form-group {
          margin-bottom: 15px;
        }

        .form-group label {
          display: block;
          margin-bottom: 5px;
          font-weight: bold;
        }

        .form-group input,
        .form-group select {
          width: 100%;
          padding: 10px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 16px;
        }

        button {
          background: #007bff;
          color: white;
          padding: 12px 24px;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 16px;
        }

        button:hover {
          background: #0056b3;
        }

        button:disabled {
          background: #ccc;
          cursor: not-allowed;
        }

        .message {
          margin-top: 15px;
          padding: 10px;
          border-radius: 4px;
        }

        .message.success {
          background: #d4edda;
          color: #155724;
          border: 1px solid #c3e6cb;
        }

        .message.error {
          background: #f8d7da;
          color: #721c24;
          border: 1px solid #f5c6cb;
        }

        .current-subscriptions {
          background: #fff;
          padding: 20px;
          border-radius: 8px;
          border: 1px solid #ddd;
        }

        .subscription-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 15px;
          border-bottom: 1px solid #eee;
        }

        .subscription-item:last-child {
          border-bottom: none;
        }

        .subscription-info {
          display: flex;
          flex-direction: column;
          gap: 5px;
        }

        .subscription-type {
          color: #666;
          font-size: 14px;
        }

        .status {
          font-size: 12px;
          padding: 2px 8px;
          border-radius: 12px;
        }

        .status.active {
          background: #d4edda;
          color: #155724;
        }

        .status.inactive {
          background: #f8d7da;
          color: #721c24;
        }

        .unsubscribe-btn {
          background: #dc3545;
          font-size: 14px;
          padding: 8px 16px;
        }

        .unsubscribe-btn:hover {
          background: #c82333;
        }
      `}</style>
    </div>
  );
};

export default EmailSubscription;