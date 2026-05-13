import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API_URL } from '../config';
import './Lobby.css';

const defaultNames = ['東家', '南家', '西家', '北家'];
const seatTiles = ['east.png', 'south.png', 'west.png', 'north.png'];
const tileBase = `${import.meta.env.BASE_URL}mahjong-tiles/`;

const Lobby = () => {
  const [roomCode, setRoomCode] = useState('');
  const [playerNames, setPlayerNames] = useState(defaultNames);
  const [baseScore, setBaseScore] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const updatePlayerName = (index: number, value: string) => {
    setPlayerNames((current) => current.map((name, itemIndex) => (itemIndex === index ? value : name)));
  };

  const handleCreateGame = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError('');

    try {
      const players = playerNames.map((name, index) => name.trim() || defaultNames[index]);
      const response = await axios.post<{ game_code: string }>(`${API_URL}/api/game/create`, {
        players,
        base_score: baseScore,
      });
      navigate(`/game/${response.data.game_code}`);
    } catch (err: unknown) {
      setError('建立房間失敗，請確認後端服務是否啟動。');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleJoinGame = async (event: FormEvent) => {
    event.preventDefault();
    if (!roomCode.trim()) return;

    const normalizedCode = roomCode.trim().toUpperCase();
    setLoading(true);
    setError('');

    try {
      await axios.get(`${API_URL}/api/game/${normalizedCode}`);
      navigate(`/game/${normalizedCode}`);
    } catch (err: unknown) {
      if (axios.isAxiosError(err) && err.response?.status === 404) {
        setError('找不到這個房間代碼。');
      } else {
        setError('加入房間失敗，請稍後再試。');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="lobby-page">
      <header className="page-heading lobby-heading">
        <span className="eyebrow">Live Score Table</span>
        <h1>建立一桌新的麻將計分。</h1>
        <p>後端會建立 room code、四位玩家、起始分數，並用 Socket.IO 同步每一手結果。</p>
      </header>

      <div className="lobby-grid">
        <form className="lobby-panel create-panel" onSubmit={handleCreateGame}>
          <div className="panel-title-row">
            <div>
              <span className="section-kicker">Create</span>
              <h2>新牌局</h2>
            </div>
            <span className="panel-badge">4 Players</span>
          </div>

          <div className="player-name-grid">
            {playerNames.map((name, index) => (
              <label className="field player-field" key={defaultNames[index]}>
                <span>
                  <img src={`${tileBase}${seatTiles[index]}`} alt="" />
                  {defaultNames[index]}
                </span>
                <input
                  type="text"
                  value={name}
                  onChange={(event) => updatePlayerName(index, event.target.value)}
                  maxLength={20}
                />
              </label>
            ))}
          </div>

          <label className="field base-score-field">
            <span>起始分數</span>
            <input
              type="number"
              value={baseScore}
              onChange={(event) => setBaseScore(Number(event.target.value))}
            />
          </label>

          <div className="table-preview" aria-label="座位預覽">
            {playerNames.map((name, index) => (
              <span key={`${defaultNames[index]}-${index}`}>
                <img src={`${tileBase}${seatTiles[index]}`} alt="" />
                {name.trim().slice(0, 3) || defaultNames[index]}
              </span>
            ))}
          </div>

          <button className="create-btn" type="submit" disabled={loading}>
            {loading ? '建立中...' : '建立房間'}
          </button>
        </form>

        <form className="lobby-panel join-panel" onSubmit={handleJoinGame}>
          <div className="panel-title-row">
            <div>
              <span className="section-kicker">Join</span>
              <h2>加入既有房間</h2>
            </div>
          </div>

          <label className="room-code-field" htmlFor="room-code">
            <span>Room Code</span>
            <input
              id="room-code"
              type="text"
              placeholder="ABC123"
              value={roomCode}
              onChange={(event) => setRoomCode(event.target.value.toUpperCase())}
              maxLength={6}
              disabled={loading}
            />
          </label>

          <button type="submit" className="join-btn" disabled={loading || !roomCode.trim()}>
            加入房間
          </button>

          <div className="join-footnote">
            <span>即時分數</span>
            <span>胡牌紀錄</span>
            <span>照片輔助計算</span>
          </div>
        </form>
      </div>

      {error && <p className="error-text">{error}</p>}
    </section>
  );
};

export default Lobby;
