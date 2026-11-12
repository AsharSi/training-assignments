import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import './Payment.css';

export default function Payment({ user }) {
  const { subtotalPrice, clearCart } = useCart();
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  // Helper format function for INR
  const formatINR = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const handlePaymentSubmit = (e) => {
    e.preventDefault();
    setIsProcessing(true);

    // Simulate payment gateway delay (e.g., 1.5 seconds)
    setTimeout(() => {
      setIsProcessing(false);
      setIsSuccess(true);
      clearCart(); // Clear the cart after successful order placement
    }, 1500);
  };

  // If order was placed successfully, show success view
  if (isSuccess) {
    return (
      <div className="payment-page-container">
        <div className="success-container">
          <div className="success-icon">✓</div>
          <h2 className="success-title">Order Placed Successfully!</h2>
          <p className="success-message">
            Thank you for your purchase{user?.email ? `, ${user.email.split('@')[0]}` : ''}. We've received your order and are getting it ready.
          </p>
          <Link to="/" className="continue-shopping-btn">
            Continue Shopping
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="payment-page-container">
      <div className="payment-card">
        <h1 className="payment-title">Checkout & Payment</h1>

        <form onSubmit={handlePaymentSubmit} className="payment-form">
          

          <div className="payment-total-box">
            <span>Total Amount:</span>
            <span style={{ fontSize: '18px', fontWeight: '700' }}>
              {formatINR(subtotalPrice)}
            </span>
          </div>

          <button type="submit" className="pay-btn" disabled={isProcessing}>
            {isProcessing ? 'Processing Payment...' : `Pay ${formatINR(subtotalPrice)}`}
          </button>
        </form>
      </div>
    </div>
  );
}