from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import get_connection

app = FastAPI()


# Enable CORS for React/Vite
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

conn = get_connection()
cursor = conn.cursor()

# Product model
class Product(BaseModel):
    id: int
    name: str
    price: float
    image: str

#
# # In-memory product data
# products = [
#     {
#         "id": 1,
#         "name": "Wireless Headphones",
#         "price": 4500,
#         "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e"
#     },
#     {
#         "id": 2,
#         "name": "Smart Watch",
#         "price": 7000,
#         "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30"
#     },
#     {
#         "id": 3,
#         "name": "Laptop",
#         "price": 65000,
#         "image": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853"
#     }
# ]


# Home endpoint
@app.get("/")
def home():
    return {
        "message": "Product API is running"
    }


@app.get("/products")
def get_products():
    cursor.execute("""
    SELECT id, name, price, image
    FROM products
    ORDER BY id
    """)
    rows = cursor.fetchall()
    products = []
    for row in rows:
        products.append({
        "id": row[0],
        "name": row[1],
        "price": float(row[2]),
        "image": row[3]
        })
    return products

# GET product by ID
@app.get("/products/{product_id}")
def get_product(product_id: int):

    cursor.execute("SELECT id, name, price, image from products WHERE id = %s", (product_id,))
    row = cursor.fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )
    else:
        return {
            "id": row[0],
            "name": row[1],
            "price": row[2],
            "image": row[3]
        }



# POST - Add product
@app.post("/products")
def add_product(product: Product):

    cursor.execute("""
        INSERT INTO products (id, name, price, image) VALUES (%s, %s, %s, %s)
    """, (product.id, product.name, product.price, product.image))

    return {
        "message": "Product added successfully",
        "product": product
    }


# PUT - Update product
@app.put("/products/{product_id}")
def update_product(
    product_id: int,
    updated_product: Product
):

    cursor.execute("SELECT id, name, price, image FROM products WHERE id = %s", (product_id,))
    row = cursor.fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    else:
        cursor.execute("""
        UPDATE products SET name = %s, price = %s, image = %s WHERE id = %s
        """, (updated_product.name, updated_product.price, updated_product.image, product_id))

        return {
            "message": "Product updated successfully",
        }


# DELETE - Delete product
@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))

    return {
        "message": "Product deleted successfully",
    }