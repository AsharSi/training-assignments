from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = FastAPI(title="Game Booking API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "game_booking_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "Admin@123")


def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")


# Pydantic models for validation
class BookingCreate(BaseModel):
    game_id: int
    player_name: str
    player_email: str
    players_count: int


@app.get("/games")
def get_games():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM games ORDER BY schedule_time ASC;")
    games = cursor.fetchall()
    cursor.close()
    conn.close()
    return games


@app.post("/bookings", status_code=status.HTTP_201_CREATED)
def create_booking(booking: BookingCreate):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if game exists and has enough capacity
    cursor.execute("SELECT max_players FROM games WHERE id = %s;", (booking.game_id,))
    game = cursor.fetchone()
    if not game:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Game not found")

    # Check current booked players count
    cursor.execute("SELECT SUM(players_count) as total_booked FROM bookings WHERE game_id = %s;", (booking.game_id,))
    result = cursor.fetchone()
    total_booked = result['total_booked'] or 0

    if total_booked + booking.players_count > game['max_players']:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Not enough slots available for this game session.")

    # Insert booking
    cursor.execute(
        """
        INSERT INTO bookings (game_id, player_name, player_email, players_count)
        VALUES (%s, %s, %s, %s) RETURNING id, game_id, player_name, player_email, players_count, created_at;
        """,
        (booking.game_id, booking.player_name, booking.player_email, booking.players_count)
    )
    new_booking = cursor.fetchone()
    conn.commit()

    cursor.close()
    conn.close()
    return {"message": "Booking successful!", "booking": new_booking}


@app.get("/bookings/{game_id}")
def get_game_bookings(game_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE game_id = %s;", (game_id,))
    bookings = cursor.fetchall()
    cursor.close()
    conn.close()
    return bookings