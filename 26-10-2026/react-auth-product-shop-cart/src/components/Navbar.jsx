import { Link } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import './Navbar.css';

export default function Navbar({ user }) {
  const { totalItemsCount } = useCart();

  return (
    <nav className="navbar">
      {/* Brand / Logo */}
      <Link to="/" className="navbar-brand">
        MyStore
      </Link>

      {/* Navigation Links */}
      <div className="navbar-links">
        <Link to="/about" className="navbar-link">
          About
        </Link>
        <Link to="/payment" className="navbar-link">
          Payment
        </Link>

        {/* Cart Link with Badge */}
        <Link to="/cart" className="navbar-cart-link">
          🛒 Cart
          {totalItemsCount > 0 && (
            <span className="navbar-cart-badge">{totalItemsCount}</span>
          )}
        </Link>

        {/* User Info & Auth Links */}
        {user && user.email ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span className="navbar-user-info" title={user.email}>
              👤 {user.email.split('@')[0]}
            </span>
            <Link to="/logout" className="navbar-link" style={{ color: '#ef4444' }}>
              Logout
            </Link>
          </div>
        ) : (
          <Link to="/login" className="navbar-link" style={{ fontWeight: '600', color: '#2563eb' }}>
            Login
          </Link>
        )}
      </div>
    </nav>
  );
}