import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

interface Props {
  allowedRoles?: string[];
}

export default function ProtectedRoute({ allowedRoles }: Props) {
  const { isAuthenticated, user } = useAuthStore((state) => ({
    isAuthenticated: state.isAuthenticated,
    user: state.user,
  }));
  const location = useLocation();

  if (!isAuthenticated) {
    // Redirect to login with return URL
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    // Redirect to home if authorized but not allowed role
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
