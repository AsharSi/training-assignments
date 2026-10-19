
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from database import get_connection

app = FastAPI()

class Product(BaseModel):
    id: int | None = None
    name: str
    price: float

conn = get_connection()
cursor = conn.cursor()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/hello/{name}")
async def hello(name: str):
    return {"message": f"Hello {name}"}

@app.post("/product")
async def create_product(product: Product):
    cursor.execute("INSERT INTO products (name, price) VALUES (%s, %s)",
    (product.name, product.price))
    conn.commit()
    return {
        "message": "Product created",
        "product": product
    }

@app.post("/products")
async def create_products(prods: List[Product]):
    for pro in prods:
        cursor.execute(
            "INSERT INTO products (id, name, price) VALUES (%s, %s, %s)",
            (pro.id, pro.name, pro.price)
        )

    conn.commit()

    return {
        "message": "Products created",
    }
@app.get("/products")
async def get_products():
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    return rows

@app.get("/products/{prod_id}")
async def get_product(prod_id: int):
    cursor.execute("SELECT * FROM products WHERE id = %s", (prod_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    return row

@app.put("/products/{prod_id}")
async def update_product(prod_id: int, product: Product):
    cursor.execute("SELECT * FROM products WHERE id = %s", (prod_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Product not found")

    # Fixed: Combined into one query and passed parameters as a proper tuple
    cursor.execute(
        "UPDATE products SET name = %s, price = %s WHERE id = %s",
        (product.name, product.price, prod_id)
    )
    conn.commit() # Added commit
    return {
        "message": "Product updated",
    }

@app.delete("/products/{prod_id}")
async def delete_product(prod_id: int):
    cursor.execute("SELECT * FROM products WHERE id = %s", (prod_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Product not found")

    cursor.execute("DELETE FROM products WHERE id = %s", (prod_id,))
    conn.commit()
    return {
        "message": "Product deleted",
    }