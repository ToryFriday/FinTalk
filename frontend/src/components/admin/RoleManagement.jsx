/**
 * Role Management Interface for Administrators
 * Provides CRUD operations for roles and role assignments
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';

const RoleManagement = () => {
  const [roles, setRoles] = useState([]);
  const [users, setUsers] = useState([]);
  const [userRoles, setUserRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('roles');

  // Form states
  const [newRole, setNewRole] = useState({
    name: '',
    display_name: '',
    description: ''
  });
  const [roleAssignment, setRoleAssignment] = useState({
    user_id: '',
    role_id: '',
    notes: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [rolesRes, userRolesRes] = await Promise.all([
        axios.get('/api/accounts/roles/'),
        axios.get('/api/accounts/user-roles/')
      ]);
      
      setRoles(rolesRes.data.results || rolesRes.data);
      setUserRoles(userRolesRes.data.results || userRolesRes.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch data: ' + (err.response?.data?.error || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRole = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/api/accounts/roles/', newRole);
      setNewRole({ name: '', display_name: '', description: '' });
      fetchData();
      alert('Role created successfully!');
    } catch (err) {
      alert('Failed to create role: ' + (err.response?.data?.error || err.message));
    }
  };

  const handleAssignRole = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/api/accounts/role-assignment/', roleAssignment);
      setRoleAssignment({ user_id: '', role_id: '', notes: '' });
      fetchData();
      alert('Role assigned successfully!');
    } catch (err) {
      alert('Failed to assign role: ' + (err.response?.data?.error || err.message));
    }
  };

  const handleRevokeRole = async (userId, roleId) => {
    if (!window.confirm('Are you sure you want to revoke this role?')) return;
    
    try {
      await axios.post('/api/accounts/role-revocation/', {
        user_id: userId,
        role_id: roleId
      });
      fetchData();
      alert('Role revoked successfully!');
    } catch (err) {
      alert('Failed to revoke role: ' + (err.response?.data?.error || err.message));
    }
  };

  if (loading) {
    return (
      <div className="role-management">
        <div className="loading">Loading role management interface...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="role-management">
        <div className="error">Error: {error}</div>
        <button onClick={fetchData}>Retry</button>
      </div>
    );
  }

  return (
    <div className="role-management">
      <h2>Role Management</h2>
      
      {/* Tab Navigation */}
      <div className="tabs">
        <button 
          className={activeTab === 'roles' ? 'active' : ''}
          onClick={() => setActiveTab('roles')}
        >
          Roles
        </button>
        <button 
          className={activeTab === 'assignments' ? 'active' : ''}
          onClick={() => setActiveTab('assignments')}
        >
          Role Assignments
        </button>
        <button 
          className={activeTab === 'assign' ? 'active' : ''}
          onClick={() => setActiveTab('assign')}
        >
          Assign Role
        </button>
      </div>

      {/* Roles Tab */}
      {activeTab === 'roles' && (
        <div className="tab-content">
          <h3>System Roles</h3>
          
          {/* Create Role Form */}
          <div className="create-role-form">
            <h4>Create New Role</h4>
            <form onSubmit={handleCreateRole}>
              <div className="form-group">
                <label>Role Name:</label>
                <select
                  value={newRole.name}
                  onChange={(e) => setNewRole({...newRole, name: e.target.value})}
                  required
                >
                  <option value="">Select role type</option>
                  <option value="admin">Admin</option>
                  <option value="editor">Editor</option>
                  <option value="writer">Writer</option>
                  <option value="reader">Reader</option>
                  <option value="guest">Guest</option>
                </select>
              </div>
              <div className="form-group">
                <label>Display Name:</label>
                <input
                  type="text"
                  value={newRole.display_name}
                  onChange={(e) => setNewRole({...newRole, display_name: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Description:</label>
                <textarea
                  value={newRole.description}
                  onChange={(e) => setNewRole({...newRole, description: e.target.value})}
                  required
                />
              </div>
              <button type="submit">Create Role</button>
            </form>
          </div>

          {/* Roles List */}
          <div className="roles-list">
            <h4>Existing Roles</h4>
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Display Name</th>
                  <th>Description</th>
                  <th>Active</th>
                  <th>Users</th>
                  <th>Permissions</th>
                </tr>
              </thead>
              <tbody>
                {roles.map(role => (
                  <tr key={role.id}>
                    <td>{role.name}</td>
                    <td>{role.display_name}</td>
                    <td>{role.description}</td>
                    <td>{role.is_active ? 'Yes' : 'No'}</td>
                    <td>{role.user_count || 0}</td>
                    <td>{role.permission_count || 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Role Assignments Tab */}
      {activeTab === 'assignments' && (
        <div className="tab-content">
          <h3>Role Assignments</h3>
          <table>
            <thead>
              <tr>
                <th>User</th>
                <th>Role</th>
                <th>Assigned By</th>
                <th>Assigned At</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {userRoles.map(assignment => (
                <tr key={assignment.id}>
                  <td>{assignment.user_username}</td>
                  <td>{assignment.role_display_name}</td>
                  <td>{assignment.assigned_by_username || 'System'}</td>
                  <td>{new Date(assignment.assigned_at).toLocaleDateString()}</td>
                  <td>
                    <span className={assignment.is_valid ? 'status-active' : 'status-inactive'}>
                      {assignment.is_valid ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>
                    {assignment.is_active && (
                      <button 
                        onClick={() => handleRevokeRole(assignment.user, assignment.role)}
                        className="revoke-btn"
                      >
                        Revoke
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Assign Role Tab */}
      {activeTab === 'assign' && (
        <div className="tab-content">
          <h3>Assign Role to User</h3>
          <form onSubmit={handleAssignRole}>
            <div className="form-group">
              <label>User ID:</label>
              <input
                type="number"
                value={roleAssignment.user_id}
                onChange={(e) => setRoleAssignment({...roleAssignment, user_id: e.target.value})}
                required
                placeholder="Enter user ID"
              />
            </div>
            <div className="form-group">
              <label>Role:</label>
              <select
                value={roleAssignment.role_id}
                onChange={(e) => setRoleAssignment({...roleAssignment, role_id: e.target.value})}
                required
              >
                <option value="">Select role</option>
                {roles.map(role => (
                  <option key={role.id} value={role.id}>
                    {role.display_name}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Notes (optional):</label>
              <textarea
                value={roleAssignment.notes}
                onChange={(e) => setRoleAssignment({...roleAssignment, notes: e.target.value})}
                placeholder="Assignment notes..."
              />
            </div>
            <button type="submit">Assign Role</button>
          </form>
        </div>
      )}

      <style jsx>{`
        .role-management {
          max-width: 1200px;
          margin: 0 auto;
          padding: 20px;
        }

        .tabs {
          display: flex;
          border-bottom: 2px solid #ddd;
          margin-bottom: 20px;
        }

        .tabs button {
          padding: 10px 20px;
          border: none;
          background: none;
          cursor: pointer;
          border-bottom: 2px solid transparent;
        }

        .tabs button.active {
          border-bottom-color: #007bff;
          color: #007bff;
        }

        .tab-content {
          padding: 20px 0;
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
        .form-group select,
        .form-group textarea {
          width: 100%;
          padding: 8px;
          border: 1px solid #ddd;
          border-radius: 4px;
        }

        .form-group textarea {
          height: 80px;
          resize: vertical;
        }

        button {
          background: #007bff;
          color: white;
          border: none;
          padding: 10px 20px;
          border-radius: 4px;
          cursor: pointer;
        }

        button:hover {
          background: #0056b3;
        }

        .revoke-btn {
          background: #dc3545;
          padding: 5px 10px;
          font-size: 12px;
        }

        .revoke-btn:hover {
          background: #c82333;
        }

        table {
          width: 100%;
          border-collapse: collapse;
          margin-top: 20px;
        }

        th, td {
          padding: 12px;
          text-align: left;
          border-bottom: 1px solid #ddd;
        }

        th {
          background-color: #f8f9fa;
          font-weight: bold;
        }

        .status-active {
          color: #28a745;
          font-weight: bold;
        }

        .status-inactive {
          color: #dc3545;
          font-weight: bold;
        }

        .loading, .error {
          text-align: center;
          padding: 40px;
          font-size: 18px;
        }

        .error {
          color: #dc3545;
        }

        .create-role-form {
          background: #f8f9fa;
          padding: 20px;
          border-radius: 8px;
          margin-bottom: 30px;
        }
      `}</style>
    </div>
  );
};

export default RoleManagement;