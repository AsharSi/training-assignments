import { useEffect, useState } from "react"
import EditItem from "./editItem"

function Products() {
    const [products, setProducts] = useState([])
    const [id, setId] = useState('')
    const [productName, setProductName] = useState('')
    const [price, setPrice] = useState('')
    const [image, setImage] = useState('')
    const [edit, setEdit] = useState(false)

    useEffect(() => {
        fetch("http://127.0.0.1:8000/products")
            .then((response) => response.json())
            .then((data) => {
                setProducts(data)
            })
            .catch((error) => {
                console.error("Error fetching products:", error)
            })
    }, [])

    const addProduct = (e) => {
        e.preventDefault();
        const product = {
            id: Number(id),
            name: productName,
            price: Number(price),
            image: image
        }

        fetch("http://127.0.0.1:8000/products", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(product)

        }).then((res) => {
            if (res.status === 200) {
                console.log("product added successfully")
            } else {
                console.log(res)
            }
        }).catch((err) => {
            console.log(err)
        })
    }

    const deleteProduct = (id) => {

        fetch(`http://127.0.0.1:8000/products/${id}`, {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json"
            }
        }).then((res) => {
            if (res.status === 200) {
                console.log("product deleted successfully")
            } else {
                console.log(res)
            }
        }).catch((err) => {
            console.log(err)
        })
    }

    return (
        <div>
            <h1>Product Store</h1>

            <form onSubmit={addProduct}>
                <div>
                    <label>Product ID:</label>
                    <input
                        type="number"
                        value={id}
                        onChange={(e) => setId(e.target.value)}
                        required
                    />
                </div>

                <div>
                    <label>Product Name:</label>
                    <input
                        type="text"
                        value={productName}
                        onChange={(e) => setProductName(e.target.value)}
                        required
                    />
                </div>

                <div>
                    <label>Price:</label>
                    <input
                        type="number"
                        value={price}
                        onChange={(e) => setPrice(e.target.value)}
                        required
                    />
                </div>

                <div>
                    <label>Image URL:</label>
                    <input
                        type="text"
                        value={image}
                        onChange={(e) => setImage(e.target.value)}
                        required
                    />
                </div>

                <button type="submit">Add Product</button>
            </form>

            {products.map((product) => (
                <>

                    <div key={product.id}>
                        <img
                            src={product.image}
                            alt={product.name}
                            width="180"
                        />

                        <h2>{product.name}</h2>

                        <p>Price: ₹{product.price}</p>

                    </div>

                    <button onClick={() => setEdit(!edit)}>
                        Edit this product
                    </button>
                    <button onClick={() => deleteProduct(product.id)}>
                        Delete this product
                    </button>
                    {
                        edit &&
                        <EditItem product={product} />
                    }


                    <hr />
                </>
            ))}
        </div>
    )
}

export default Products