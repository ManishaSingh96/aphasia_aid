import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import Dashboard from "./pages/Dashboard";
import About from "./pages/About";
import ProfileSettings from "./pages/ProfileSettings";
import ActivitySession from "./pages/ActivitySession";
import ProtectedRoute from "./components/ProtectedRoute";

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route path="/about" element={<About />} />
        <Route
          path="/profile-settings"
          element={
            <ProtectedRoute>
              <ProfileSettings />
            </ProtectedRoute>
          }
        />
        <Route
          path="/activity/:activityId"
          element={
            <ProtectedRoute>
              <ActivitySession />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<h2>404 Not Found</h2>} />
      </Routes>
    </Layout>
  );
}

export default App;
