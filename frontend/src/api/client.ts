import axios from 'axios';
import { useAuthStore } from '../stores/authStore';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

// Track if we're currently refreshing to prevent loops
let isRefreshing = false;
let refreshAttempted = false;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => {
    // Reset refresh flag on successful response
    refreshAttempted = false;
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    // Skip refresh for auth endpoints to prevent loops
    if (originalRequest.url?.includes('/auth/')) {
      return Promise.reject(error);
    }
    
    // If 401, not currently refreshing, and haven't already retried
    if (error.response?.status === 401 && !isRefreshing && !originalRequest._retry && !refreshAttempted) {
      originalRequest._retry = true;
      isRefreshing = true;
      refreshAttempted = true;
      
      const refreshToken = useAuthStore.getState().refreshToken;
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          
          const { access_token, refresh_token } = response.data;
          useAuthStore.getState().setTokens(access_token, refresh_token);
          
          isRefreshing = false;
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch {
          isRefreshing = false;
          // Refresh failed, clear auth state
          useAuthStore.setState({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,
          });
        }
      } else {
        isRefreshing = false;
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;
