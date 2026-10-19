import psycopg2


def get_connection():
    conn = psycopg2.connect(
        host = "localhost",
        database="fastapi_store",
        user="postgres",
        password="Admin@123"
    )

    print("Connected to database")

    return conn