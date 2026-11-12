
import { Routes, Route, Link } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import './App.css'
import About from "./pages/About";
import Logout from "./pages/Logout";

export default function App() {
  const { user, logout } = useAuth()
  return (
    <>

      <div>
        <Link to={"/about"}>About</Link>
        {" | "}
        <Link to={"/dashboard"}>Dashboard</Link>
        {" | "}
        {
          !user ?
            <Link to={"/login"}>Login</Link> :
            <Link to={"/logout"}>Logout</Link>
        }
      </div>
      <Routes>
        <Route path="/" element={<Home />} />
        {
          user ?
            <Route path="/logout" element={<Logout />} /> :
            <Route path="/login" element={<Login />} />
        }
        <Route path="/about" element={<About />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<Dashboard />} />
        </Route>

        <Route
          path="*"
          element={<h1>404 - Page Not Found</h1>}
        />
      </Routes>
    </>
  );
}
