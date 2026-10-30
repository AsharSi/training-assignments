import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [games, setGames] = useState([]);
  const [selectedGame, setSelectedGame] = useState(null);
  const [playerName, setPlayerName] = useState('');
  const [playerEmail, setPlayerEmail] = useState('');
  const [playersCount, setPlayersCount] = useState(1);
  const [message, setMessage] = useState('');

  const API_URL = "http://localhost:8000";

  useEffect(() => {
    fetch(`${API_URL}/games`)
      .then(res => res.json())
      .then(data => setGames(data))
      .catch(err => console.error("Error fetching games:", err));
  }, []);

  const handleBooking = async (e) => {
    e.preventDefault();
    if (!selectedGame) return;

    const bookingData = {
      game_id: selectedGame.id,
      player_name: playerName,
      player_email: playerEmail,
      players_count: Number(playersCount)
    };

    try {
      const response = await fetch(`${API_URL}/bookings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bookingData)
      });

      const result = await response.json();
      if (response.ok) {
        setMessage(`Success! Booking reference ID: ${result.booking.id}`);
        setPlayerName('');
        setPlayerEmail('');
        setPlayersCount(1);
        setSelectedGame(null);
      } else {
        setMessage(`Error: ${result.detail}`);
      }
    } catch (err) {
      setMessage("Failed to connect to the server.");
    }
  };

  return (
    <div style={{ padding: '30px', fontFamily: 'Arial, sans-serif', maxWidth: '800px', margin: 'auto' }}>
      <h1>🎮 Game Booking System</h1>
      {message && <div style={{ padding: '10px', background: '#e2f0d9', marginBottom: '20px', borderRadius: '4px' }}>{message}</div>}

      <h2>Available Games</h2>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '15px' }}>
        {games.map(game => (
          <div key={game.id} style={{ border: '1px solid #ccc', padding: '15px', borderRadius: '8px' }}>
            <h3>{game.title}</h3>
            <p>{game.description}</p>
            <p><strong>Max Players:</strong> {game.max_players}</p>
            <p><strong>Schedule:</strong> {new Date(game.schedule_time).toLocaleString()}</p>
            <button
              onClick={() => setSelectedGame(game)}
              style={{ background: '#007bff', color: 'white', border: 'none', padding: '8px 15px', borderRadius: '4px', cursor: 'pointer' }}
            >
              Book This Game
            </button>
          </div>
        ))}
      </div>

      {selectedGame && (
        <div style={{ marginTop: '30px', padding: '20px', border: '2px dashed #007bff', borderRadius: '8px' }}>
          <h3>Book Session: {selectedGame.title}</h3>
          <form onSubmit={handleBooking} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <label>
              Your Name:
              <input type="text" value={playerName} onChange={e => setPlayerName(e.target.value)} required style={{ width: '100%', padding: '8px', marginTop: '4px' }} />
            </label>
            <label>
              Email Address:
              <input type="email" value={playerEmail} onChange={e => setPlayerEmail(e.target.value)} required style={{ width: '100%', padding: '8px', marginTop: '4px' }} />
            </label>
            <label>
              Number of Players (Pre-decided):
              <input type="number" min="1" max={selectedGame.max_players} value={playersCount} onChange={e => setPlayersCount(e.target.value)} required style={{ width: '100%', padding: '8px', marginTop: '4px' }} />
            </label>
            <button type="submit" style={{ background: '#28a745', color: 'white', border: 'none', padding: '10px', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
              Confirm Booking
            </button>
          </form>
        </div>
      )}
    </div>
  );
}

export default App;