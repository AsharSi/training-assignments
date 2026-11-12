from typing import List

from fastapi import FastAPI
from pydantic import BaseModel
import psycopg2

app = FastAPI()

class Book(BaseModel):
    book_id: int
    title: str
    author: str
    category: str
    price: float
    stock: int

def connect_db():
    con = psycopg2.connect(
        host="localhost",
        user="postgres",
        password="Admin@123",
        database="library_store",
    )
    print("Connected to PostgreSQL successfully")

    return con

conn = connect_db()
cur = conn.cursor()

@app.get("/")
async def get_root():
    return {"Hello": "World"}


@app.post("/books/create")
async def create_book(books: List[Book]):
    for book in books:
        cur.execute(
            "INSERT into books (book_id, title, author, category, price, stock) VALUES (%s, %s, %s, %s, %s, %s)",
            (book.book_id, book.title, book.author, book.category, book.price, book.stock)
        )

    conn.commit()
    return {"message": "Books created successfully"}

@app.post("/book/create")
async def create_book(book: Book):
    cur.execute(
        "INSERT into books (book_id, title, author, category, price, stock) VALUES (%s, %s, %s, %s, %s, %s)",
        (book.book_id, book.title, book.author, book.category, book.price, book.stock)
    )

    conn.commit()
    return {"message": "Book created successfully"}

@app.get("/book/{book_id}")
async def get_book(book_id: str):
    cur.execute(
        "SELECT book_id, title, author, price, stock FROM books WHERE id = %s",
        book_id
    )

    return cur.fetchone()

@app.get("/books")
async def get_books(category: str = "", price_gt: int = 0):
    query = f"SELECT * FROM books WHERE price > {price_gt} "
    if category != "":
        query += f"AND category = '{category}'"
    cur.execute(query)

    return cur.fetchall()

class Update_Book(BaseModel):
    price: float
    stock: int

@app.put("/book/{book_id}")
async def get_book(book_id: str, book: Update_Book):
    cur.execute(
        "UPDATE books SET price = %s, stock = %s WHERE book_id = %s",
        (book.price, book.stock, book_id)
    )

    conn.commit()
    return {"message": "Book updated successfully"}

@app.delete("/book/{book_id}")
async def delete_book(book_id: str):
    cur.execute("DELETE FROM books WHERE book_id = %s", (book_id,))

    conn.commit()
    return {"message": "Book deleted successfully"}
