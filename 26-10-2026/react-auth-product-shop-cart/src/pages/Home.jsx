import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import ProductList from "../components/ProductList";

export default function Home() {
    const [products, setProducts] = useState([])

    useEffect(() => {
        const getProducts = async () => {
            try {
                const res = await fetch("http://127.0.0.1:8000/products")

                if (!res.ok) {
                    throw new Error(`HTTP error! Status: ${res.status}`)
                }

                const data = await res.json()

                setProducts(data)
            } catch (error) {
                console.error("Fetch operation failed: ", error.message)
            }
        }

        getProducts()
    }, [])
    return (
        <div>
            <ProductList products={products} />
        </div>
    )
}