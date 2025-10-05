import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { getCurrentUser, getStoredUser, clearAuth, initializeCSRF } from '../services/authService';

// Initial state
const initialState = {
  user: null,
  isAuthenticated: false,
  loading: true,
  error: null,
};

// Action types
const AUTH_ACTIONS = {
  LOGIN_START: 'LOGIN_START',
  LOGIN_SUCCESS: 'LOGIN_SUCCESS',
  LOGIN_FAILURE: 'LOGIN_FAILURE',
  LOGOUT: 'LOGOUT',
  UPDATE_USER: 'UPDATE_USER',
  SET_LOADING: 'SET_LOADING',
  CLEAR_ERROR: 'CLEAR_ERROR',
};

// Reducer function
const authReducer = (state, action) => {
  switch (action.type) {
    case AUTH_ACTIONS.LOGIN_START:
      return {
        ...state,
        loading: true,
        error: null,
      };
    
    case AUTH_ACTIONS.LOGIN_SUCCESS:
      return {
        ...state,
        user: action.payload,
        isAuthenticated: true,
        loading: false,
        error: null,
      };
    
    case AUTH_ACTIONS.LOGIN_FAILURE:
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        loading: false,
        error: action.payload,
      };
    
    case AUTH_ACTIONS.LOGOUT:
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        loading: false,
        error: null,
      };
    
    case AUTH_ACTIONS.UPDATE_USER:
      return {
        ...state,
        user: { ...state.user, ...action.payload },
      };
    
    case AUTH_ACTIONS.SET_LOADING:
      return {
        ...state,
        loading: action.payload,
      };
    
    case AUTH_ACTIONS.CLEAR_ERROR:
      return {
        ...state,
        error: null,
      };
    
    default:
      return state;
  }
};

// Create context
const AuthContext = createContext();

// Custom hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Auth provider component
export const AuthProvider = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Initialize auth state on app load
  useEffect(() => {
    const initializeAuth = async () => {
      dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: true });
      
      try {
        // Initialize CSRF token first
        await initializeCSRF();
        
        // Then check if there's a stored user
        const storedUser = getStoredUser();
        
        if (storedUser) {
          // Verify the stored user is still valid by fetching current user
          try {
            const response = await getCurrentUser();
            if (response.data) {
              dispatch({ 
                type: AUTH_ACTIONS.LOGIN_SUCCESS, 
                payload: response.data 
              });
            } else {
              // Stored user is invalid, clear it
              clearAuth();
              dispatch({ type: AUTH_ACTIONS.LOGOUT });
            }
          } catch (error) {
            // If getCurrentUser fails, the stored user is invalid
            clearAuth();
            dispatch({ type: AUTH_ACTIONS.LOGOUT });
          }
        } else {
          // No stored user
          dispatch({ type: AUTH_ACTIONS.LOGOUT });
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        dispatch({ 
          type: AUTH_ACTIONS.LOGIN_FAILURE, 
          payload: 'Failed to initialize authentication' 
        });
      } finally {
        dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: false });
      }
    };

    initializeAuth();
  }, []);

  // Auth actions
  const login = (userData) => {
    dispatch({ type: AUTH_ACTIONS.LOGIN_SUCCESS, payload: userData });
  };

  const logout = () => {
    clearAuth();
    dispatch({ type: AUTH_ACTIONS.LOGOUT });
  };

  const updateUser = (userData) => {
    dispatch({ type: AUTH_ACTIONS.UPDATE_USER, payload: userData });
  };

  const clearError = () => {
    dispatch({ type: AUTH_ACTIONS.CLEAR_ERROR });
  };

  const setLoading = (loading) => {
    dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: loading });
  };

  // Check if user has specific role
  const hasRole = (role) => {
    if (!state.user || !state.user.roles) return false;
    return state.user.roles.some(userRole => userRole.role.name === role);
  };

  // Check if user has any of the specified roles
  const hasAnyRole = (roles) => {
    if (!state.user || !state.user.roles) return false;
    return roles.some(role => hasRole(role));
  };

  // Check if user is admin
  const isAdmin = () => {
    return state.user?.is_superuser || hasRole('admin');
  };

  // Check if user is editor
  const isEditor = () => {
    return isAdmin() || hasRole('editor');
  };

  // Check if user can create posts
  const canCreatePosts = () => {
    return state.isAuthenticated && (isAdmin() || hasAnyRole(['editor', 'writer']));
  };

  // Check if user can edit specific post
  const canEditPost = (post) => {
    if (!state.isAuthenticated) return false;
    if (isAdmin() || isEditor()) return true;
    return post.author_user === state.user?.user_id;
  };

  // Check if user can delete specific post
  const canDeletePost = (post) => {
    if (!state.isAuthenticated) return false;
    return isAdmin() || isEditor();
  };

  const value = {
    // State
    ...state,
    
    // Actions
    login,
    logout,
    updateUser,
    clearError,
    setLoading,
    
    // Permission helpers
    hasRole,
    hasAnyRole,
    isAdmin,
    isEditor,
    canCreatePosts,
    canEditPost,
    canDeletePost,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;