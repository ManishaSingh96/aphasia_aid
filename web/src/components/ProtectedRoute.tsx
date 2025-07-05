import { Navigate } from "react-router-dom";
import type { ReactNode } from "react";

interface ProtectedRouteProps {
  children: ReactNode;
}

function ProtectedRoute({ children }: ProtectedRouteProps) {
  // This is a placeholder for authentication logic.
  // In a real application, you would check if the user is authenticated
  // (e.g., from a context, Redux store, or API call).
  const dummyUserId = import.meta.env.VITE_DUMMY_BUT_VALID_USER_ID;
  const isAuthenticated = !!dummyUserId; // Check if the dummy user ID exists

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return children;
}

export default ProtectedRoute;
