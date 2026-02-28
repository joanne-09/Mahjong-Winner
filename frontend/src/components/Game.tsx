import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { io } from 'socket.io-client';
import { API_URL } from '../config';
import './Game.css';
import UploadForm from './UploadForm';
import Results from './Results';
import type { AnalysisResult } from '../App';

interface Player {
  id: number;
  name: string;
  money: number;
  seat_position: number;
}

interface GameState {
  id: number;
  game_code: string;
  round_wind: string;
  dealer_id: number;
  continues: number;
  players: Player[];
}

const WINDS = ['East', 'South', 'West', 'North'];

const Game = () => {
  const { roomCode } = useParams<{ roomCode: string }>();
  const navigate = useNavigate();
  
  const [gameState, setGameState] = useState<GameState | null>(null);

  // Analyzer / Win Modal state
  const [showWinModal, setShowWinModal] = useState(false);
  const [winType, setWinType] = useState<'tsumo' | 'ron'>('ron');
  const [loserId, setLoserId] = useState<number | null>(null);
  const [points, setPoints] = useState<number>(0);

  const [showAnalyzer, setShowAnalyzer] = useState(false);
  const [analyzingPlayerId, setAnalyzingPlayerId] = useState<number | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // 1. Fetch initial game state
    const fetchGame = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/game/${roomCode}`);
        setGameState(response.data);
      } catch (err) {
        console.error("Game not found", err);
        navigate('/');
      }
    };
    
    if (roomCode) {
      fetchGame();
      
      // 2. Setup WebSocket
      const newSocket = io(API_URL);
      
      newSocket.emit('join_game', { room_code: roomCode });
      
      newSocket.on('game_updated', (updatedGame: GameState) => {
        setGameState(updatedGame);
      });

      newSocket.on('game_ended', () => {
        alert('This game has been ended and recorded data deleted.');
        navigate('/');
      });
      
      return () => {
        newSocket.disconnect();
      };
    }
  }, [roomCode, navigate]);

  const getPlayerWindName = (seatPosition: number, currentDealerId: number) => {
    const distance = (seatPosition - currentDealerId + 4) % 4;
    return WINDS[distance];
  };

  if (!gameState) {
    return <div className="game-container">Loading game...</div>;
  }

  const handleAnalyze = async (formData: FormData) => {
    if (!gameState || !analyzingPlayerId) return;
    
    setLoading(true);
    setError(null);
    
    const winnerPlayer = gameState.players.find(p => p.id === analyzingPlayerId);
    let winnerWindName = 'east';
    if (winnerPlayer) {
      winnerWindName = getPlayerWindName(winnerPlayer.seat_position, gameState.dealer_id).toLowerCase();
    }
    
    formData.append('round', gameState.round_wind.toLowerCase());
    formData.append('dealer', 'east'); 
    formData.append('seat', winnerWindName);
    formData.append('continues', gameState.continues.toString());

    try {
      const response = await axios.post(`${API_URL}/api/analyze`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setResult(response.data);
      
      // Auto-populate the points from the backend analysis
      if (response.data.money && typeof response.data.money === 'number') {
         setPoints(response.data.money);
         // Open the manual confirmation modal pre-filled
         setShowAnalyzer(false);
         setShowWinModal(true);
      }
      
    } catch (err: any) {
      setError(err.response?.data?.error || 'An error occurred during analysis.');
    } finally {
      setLoading(false);
    }
  };

  const submitWin = async () => {
    if (!analyzingPlayerId) return;
    
    try {
      await axios.post(`${API_URL}/api/game/${roomCode}/win`, {
        winner_id: analyzingPlayerId,
        points: points,
        win_type: winType,
        loser_id: loserId
      });
      
      // Close modal
      closeAnalyzer();
    } catch (err) {
      console.error('Failed to submit win', err);
      alert('Failed to submit win');
    }
  };

  const openAnalyzer = (playerId: number) => {
    setAnalyzingPlayerId(playerId);
    setShowWinModal(true); // Open win modal by default now
  };

  const closeAnalyzer = () => {
    setShowAnalyzer(false);
    setShowWinModal(false);
    setAnalyzingPlayerId(null);
    setResult(null);
    setError(null);
    setPoints(0);
    setWinType('ron');
    setLoserId(null);
  };

  const endGame = async () => {
    if (window.confirm("Are you sure you want to end this game? History and scores will be permanently deleted for everyone.")) {
      try {
        await axios.delete(`${API_URL}/api/game/${roomCode}`);
        // The websocket 'game_ended' event will trigger navigate('/')
      } catch (err) {
        console.error('Failed to end game', err);
        alert('Error: Failed to end game.');
      }
    }
  };

  return (
    <div className="game-container">
      <div className="game-header">
        <h2>Room: {roomCode}</h2>
      </div>
      
      <div className="mahjong-layout">
        <div className="table-center">
            <h3>{gameState.round_wind} Round</h3>
            <p>Continues: {gameState.continues}</p>
        </div>
        
        {gameState.players.sort((a,b) => a.seat_position - b.seat_position).map((player, index) => {
          const positionClass = ['pos-bottom', 'pos-right', 'pos-top', 'pos-left'][index];
          const wind = getPlayerWindName(player.seat_position, gameState.dealer_id);
          const isDealer = gameState.dealer_id === player.seat_position;
          
          return (
            <div 
              key={player.id} 
              className={`player-card ${positionClass} ${isDealer ? 'dealer' : ''}`}
              onClick={() => openAnalyzer(player.id)}
            >
              <div className="player-info">
                <h3>{player.name}</h3>
                <span className={`wind-badge ${isDealer ? 'dealer-badge' : ''}`}>
                  {wind} {isDealer && `(Deal +${gameState.continues})`}
                </span>
              </div>
              <p className={`money ${player.money >= 0 ? 'positive' : 'negative'}`}>
                {player.money >= 0 ? '+' : ''}{player.money}
              </p>
            </div>
          );
        })}
      </div>

      <div className="game-actions">
        <button className="action-btn" onClick={() => navigate('/')}>Leave Room</button>
        <button className="action-btn danger" onClick={endGame}>End Game (Delete)</button>
      </div>

      {showWinModal && (
        <div className="modal-overlay">
          <div className="modal-content win-modal">
            <button className="close-modal" onClick={closeAnalyzer}>&times;</button>
            <h3>Record Win for {gameState.players.find(p => p.id === analyzingPlayerId)?.name}</h3>
            
            <div className="win-form">
               <div className="form-group">
                 <label>Win Type:</label>
                 <select value={winType} onChange={(e) => setWinType(e.target.value as 'ron' | 'tsumo')}>
                   <option value="ron">Ron (Discard)</option>
                   <option value="tsumo">Tsumo (Self-Draw)</option>
                 </select>
               </div>

               {winType === 'ron' && (
                 <div className="form-group">
                   <label>Who discarded (Loser)?</label>
                   <select value={loserId || ''} onChange={(e) => setLoserId(Number(e.target.value))}>
                     <option value="" disabled>Select Player</option>
                     {gameState.players
                        .filter(p => p.id !== analyzingPlayerId)
                        .map(p => (
                          <option key={p.id} value={p.id}>{p.name}</option>
                     ))}
                   </select>
                 </div>
               )}

               <div className="form-group">
                 <label>Points to exchange:</label>
                 <input 
                    type="number" 
                    value={points} 
                    onChange={(e) => setPoints(Number(e.target.value))} 
                 />
               </div>

               <button className="submit-win-btn" onClick={submitWin}>Submit Win</button>
               
               <hr />
               <p>OR calculate using image</p>
               <button className="action-btn" onClick={() => {setShowWinModal(false); setShowAnalyzer(true);}}>
                 Open Camera Analyzer
               </button>
            </div>
          </div>
        </div>
      )}

      {showAnalyzer && (
        <div className="modal-overlay">
          <div className="modal-content">
            <button className="close-modal" onClick={closeAnalyzer}>&times;</button>
            {!result ? (
              <>
                <h3>Analyze Hand for {gameState.players.find(p => p.id === analyzingPlayerId)?.name}</h3>
                <UploadForm onAnalyze={handleAnalyze} loading={loading} />
                {error && <div className="error-message">{error}</div>}
              </>
            ) : (
              <Results result={result} onReset={() => setResult(null)} />
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Game;
