import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '../types';
import { authApi, userApi } from '../api';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  _hasHydrated: boolean;
  
  setTokens: (accessToken: string, refreshToken: string) => void;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  fetchProfile: () => Promise<void>;
  setHasHydrated: (state: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      _hasHydrated: false,

      setHasHydrated: (state) => {
        set({ _hasHydrated: state });
      },

      setTokens: (accessToken, refreshToken) => {
        set({ accessToken, refreshToken, isAuthenticated: true });
      },

      login: async (email, password) => {
        set({ isLoading: true });
        try {
          const response = await authApi.login(email, password);
          set({
            accessToken: response.access_token,
            refreshToken: response.refresh_token,
            isAuthenticated: true,
          });
          // Fetch user profile after login
          await get().fetchProfile();
        } finally {
          set({ isLoading: false });
        }
      },

      register: async (email, password, fullName) => {
        set({ isLoading: true });
        try {
          await authApi.register({ email, password, full_name: fullName });
          // Auto-login after registration
          await get().login(email, password);
        } finally {
          set({ isLoading: false });
        }
      },

      logout: () => {
        authApi.logout().catch(() => {});
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        });
      },

      fetchProfile: async () => {
        const token = get().accessToken;
        if (!token) return;
        
        try {
          const response = await userApi.getProfile();
          set({ user: response.data });
        } catch (error: unknown) {
          // Only clear on 401 errors
          const axiosError = error as { response?: { status?: number } };
          if (axiosError.response?.status === 401) {
            set({
              user: null,
              accessToken: null,
              refreshToken: null,
              isAuthenticated: false,
            });
          }
          // For other errors, just log and keep current state
          console.warn('Failed to fetch profile:', error);
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
        user: state.user,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    }
  )
);
