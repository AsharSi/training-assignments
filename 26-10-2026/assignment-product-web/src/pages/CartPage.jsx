import React from 'react';
import { Link } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import './CartPage.css';

export default function CartPage() {
    const {
        cartItems,
        removeFromCart,
        updateQuantity,
        clearCart,
        totalItemsCount,
        subtotalPrice,
    } = useCart();

    // Helper function for Indian Rupee currency formatting
    const formatINR = (amount) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0,
        }).format(amount);
    };

    // If cart is empty, show empty state view
    if (cartItems.length === 0) {
        return (
            <div className="cart-page-container">
                <div className="cart-empty">
                    <div className="cart-empty-icon">🛒</div>
                    <h2 className="cart-empty-text">Your cart is empty</h2>
                    <p className="cart-empty-subtext">
                        Looks like you haven't added anything to your cart yet.
                    </p>
                    <Link to="/" className="continue-shopping-btn">
                        Continue Shopping
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="cart-page-container">
            <h1 className="cart-title">Shopping Cart</h1>

            <div className="cart-layout">
                {/* Left Column: Cart Items */}
                <div className="cart-items-section">
                    <div className="cart-header-actions">
                        <span>{totalItemsCount} {totalItemsCount === 1 ? 'Item' : 'Items'}</span>
                        <button className="clear-cart-btn" onClick={clearCart}>
                            Clear Cart
                        </button>
                    </div>

                    {cartItems.map((item) => {
                        const itemId = item.id || item.name;
                        const itemQuantity = item.quantity || 1;
                        const itemPrice = item.price || 0;
                        const itemTotal = itemPrice * itemQuantity;

                        return (
                            <div key={itemId} className="cart-item">
                                <img
                                    src={
                                        item.image ||
                                        'https://images.unsplash.com/photo-1560343090-f0409e92791a?w=500&auto=format&fit=crop'
                                    }
                                    alt={item.name}
                                    className="cart-item-image"
                                />

                                <div className="cart-item-details">
                                    <h3 className="cart-item-name">{item.name}</h3>
                                    <span className="cart-item-price">{formatINR(itemPrice)}</span>
                                </div>

                                {/* Quantity Controls */}
                                <div className="cart-quantity-controls">
                                    <button
                                        className="cart-qty-btn"
                                        onClick={() => updateQuantity(itemId, itemQuantity - 1)}
                                        aria-label="Decrease quantity"
                                    >
                                        -
                                    </button>
                                    <span className="cart-qty-count">{itemQuantity}</span>
                                    <button
                                        className="cart-qty-btn"
                                        onClick={() => updateQuantity(itemId, itemQuantity + 1)}
                                        aria-label="Increase quantity"
                                    >
                                        +
                                    </button>
                                </div>

                                {/* Item Total */}
                                <div className="cart-item-total">{formatINR(itemTotal)}</div>

                                {/* Remove Button */}
                                <button
                                    className="cart-item-remove"
                                    onClick={() => removeFromCart(itemId)}
                                    title="Remove item"
                                    aria-label="Remove item"
                                >
                                    ✕
                                </button>
                            </div>
                        );
                    })}
                </div>

                {/* Right Column: Order Summary */}
                <div className="cart-summary">
                    <h2 className="summary-title">Order Summary</h2>

                    <div className="summary-row">
                        <span>Subtotal</span>
                        <span>{formatINR(subtotalPrice)}</span>
                    </div>

                    <div className="summary-row">
                        <span>Estimated Shipping</span>
                        <span>Free</span>
                    </div>

                    <div className="summary-row total">
                        <span>Total</span>
                        <span>{formatINR(subtotalPrice)}</span>
                    </div>

                    <Link to="/payment" className="checkout-btn">
                        Proceed to Checkout
                    </Link>
                </div>
            </div>
        </div>
    );
}