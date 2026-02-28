import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API_URL } from '../config';
import './Lobby.css';

const Lobby = () => {
  const [roomCode, setRoomCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleCreateGame = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await axios.post(`${API_URL}/api/game/create`, {
        players: ['Player 1', 'Player 2', 'Player 3', 'Player 4'],
        base_score: 0
      });
      navigate(`/game/${response.data.game_code}`);
    } catch (err: any) {
      setError('Failed to create game. Ensure backend is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleJoinGame = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!roomCode.trim()) return;
    
    setLoading(true);
    setError('');
    try {
      // Just check if it exists before routing
      await axios.get(`${API_URL}/api/game/${roomCode}`);
      navigate(`/game/${roomCode}`);
    } catch (err: any) {
      if (err.response && err.response.status === 404) {
        setError('Room not found! Check the code.');
      } else {
        setError('Failed to join game. Ensure backend is running.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="lobby-container">
      <div className="lobby-card">
        <h1>Mahjong Tracker</h1>
        <p>Keep your scores in sync across devices.</p>
        
        <div className="lobby-actions">
          <button 
            className="create-btn" 
            onClick={handleCreateGame} 
            disabled={loading}
          >
            {loading ? 'Creating...' : '+ Create New Room'}
          </button>
          
          <div className="divider"><span>OR</span></div>
          
          <form className="join-form" onSubmit={handleJoinGame}>
            <input 
              type="text" 
              placeholder="Enter 6-Digit Code" 
              value={roomCode}
              onChange={(e) => setRoomCode(e.target.value.toUpperCase())}
              maxLength={6}
              disabled={loading}
            />
            <button type="submit" className="join-btn" disabled={loading || !roomCode}>
              Join Game
            </button>
          </form>
          
          {error && <p className="error-text">{error}</p>}
        </div>
      </div>
    </div>
  );
};

export default Lobby;