import psycopg2

def get_connection():
    return psycopg2.connect(
    host="localhost",
    database="product_store",
    user="postgres",
    password="Admin@123"
    )