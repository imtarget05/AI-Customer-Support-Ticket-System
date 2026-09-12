import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { Link, Navigate, Route, Routes } from "react-router-dom";
import { api, getToken, setToken } from "./lib/api";
import type { User } from "./types";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import SupportPage from "./pages/SupportPage";
import DashboardPage from "./pages/DashboardPage";
import TicketDetailPage from "./pages/TicketDetailPage";

interface AuthContextValue {
  user: User | null;
  setUser: (user: User | null) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);
export { AuthContext };

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside App");
  return ctx;
}

function RequireAgent({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== "agent") return <p className="notice">Agent access only.</p>;
  return <>{children}</>;
}

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(getToken() !== null);

  useEffect(() => {
    if (!getToken()) return;
    api<User>("/api/auth/me")
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setLoading(false));
  }, []);

  const value: AuthContextValue = {
    user,
    setUser,
    logout: () => {
      setToken(null);
      setUser(null);
    },
  };

  return (
    <AuthContext.Provider value={value}>
      <header className="topbar">
        <Link to="/" className="brand">
          SupportDesk
        </Link>
        <nav>
          <Link to="/">Submit a Ticket</Link>
          {user?.role === "agent" && <Link to="/agent">Agent Dashboard</Link>}
          {user ? (
            <button className="linklike" onClick={value.logout}>
              Log out ({user.name})
            </button>
          ) : (
            <>
              <Link to="/login">Log in</Link>
              <Link to="/register">Sign up</Link>
            </>
          )}
        </nav>
      </header>
      <main className="container">
        {loading ? (
          <p>Loading…</p>
        ) : (
          <Routes>
            <Route path="/" element={<SupportPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route
              path="/agent"
              element={
                <RequireAgent>
                  <DashboardPage />
                </RequireAgent>
              }
            />
            <Route path="/tickets/:id" element={<TicketDetailPage />} />
          </Routes>
        )}
      </main>
    </AuthContext.Provider>
  );
}
