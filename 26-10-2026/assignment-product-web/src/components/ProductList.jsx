import React, { useState } from 'react';
import './ProductList.css';
import { useCart } from '../context/CartContext';

const ProductCard = ({ product }) => {
    const { addToCart } = useCart()
    const [isLiked, setIsLiked] = useState(false);

    // Fallback defaults
    const {
        name = 'Unnamed Product',
        image = 'https://images.unsplash.com/photo-1560343090-f0409e92791a?w=500&auto=format&fit=crop',
        price = 0,
    } = product;
    
    const formattedPrice = new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0, // Optional: remove decimals if you don't need paise (e.g., ₹1,299 instead of ₹1,299.00)
    }).format(price);

    return (
        <div className="product-card">
            <div className="product-card-image-wrapper">
                <img src={image} alt={name} className="product-card-image" loading="lazy" />

                <button
                    className={`product-card-wishlist ${isLiked ? 'active' : ''}`}
                    onClick={() => setIsLiked(!isLiked)}
                    aria-label="Add to wishlist"
                >
                    {isLiked ? '♥' : '♡'}
                </button>
            </div>

            <div className="product-card-body">
                <div>
                    <h3 className="product-card-title">{name}</h3>
                </div>

                <div className="product-card-footer">
                    <div className="product-card-price-container">
                        <span className="product-card-price">{formattedPrice}</span>
                    </div>

                    <button className="product-card-add-btn" onClick={() => addToCart(product)}>
                        + Add
                    </button>
                </div>
            </div>
        </div>
    );
};

export default function ProductList({ products }) {
    return (
        <div className="product-grid">
            {products?.map((product, index) => (
                <ProductCard key={product.id || index} product={product} />
            ))}
        </div>
    );
}