import { useState } from "react"

export default function EditItem(props) {

    const [id, setId] = useState(props.product.id)
    const [productName, setProductName] = useState(props.product.name)
    const [price, setPrice] = useState(props.product.price)
    const [image, setImage] = useState(props.product.image)

    const updateProduct = (e) => {
        e.preventDefault();
        const product = {
            id: Number(id),
            name: productName,
            price: Number(price),
            image: image
        }

        fetch(`http://127.0.0.1:8000/products/${id}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(product)

        }).then((res) => {
            if (res.status === 200) {
                console.log("product updated successfully")
            } else {
                console.log(res)
            }
        }).catch((err) => {
            console.log(err)
        })
    }


    return (
        <>

            <form onSubmit={updateProduct}>
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

                <button type="submit">Update Product</button>
            </form>
        </>
    )
}