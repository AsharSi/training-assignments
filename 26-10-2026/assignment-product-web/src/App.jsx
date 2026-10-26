
import { Routes, Route, Link } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Payment from "./pages/Payment";
import './App.css'
import About from "./pages/About";
import Logout from "./pages/Logout";
import Navbar from "./components/Navbar";
import CartPage from "./pages/CartPage";

export default function App() {
  const { user, logout } = useAuth()
  return (
    <>
      <Navbar />
      <Routes>
        {
          user ?
            <Route path="/logout" element={<Logout />} /> :
            <Route path="/login" element={<Login />} />
        }
        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />
        <Route path="/cart" element={<CartPage />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/payment" element={<Payment />} />
        </Route>

        <Route
          path="*"
          element={<h1>404 - Page Not Found</h1>}
        />
      </Routes>
    </>
  );
}
