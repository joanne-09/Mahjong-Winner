import { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { io } from 'socket.io-client';
import { API_URL } from '../config';
import './Game.css';
import UploadForm from './UploadForm';
import Results from './Results';
import type { AnalysisResult, MoneyBreakdown, Wind } from '../App';
import type { AnalysisSettings } from './UploadForm';

interface Player {
  id: number;
  name: string;
  money: number;
  seat_position: number;
}

interface RoundRecord {
  id: number;
  winner_id: number | null;
  loser_id: number | null;
  winner_name: string | null;
  loser_name: string | null;
  points_exchanged: number;
  win_type: 'ron' | 'tsumo' | 'draw';
  is_dealer_win: boolean;
}

interface GameState {
  id: number;
  game_code: string;
  round_wind: string;
  dealer_id: number;
  continues: number;
  players: Player[];
  rounds: RoundRecord[];
}

const windCodes: Wind[] = ['east', 'south', 'west', 'north'];

const windShortLabels: Record<Wind, string> = {
  east: '東',
  south: '南',
  west: '西',
  north: '北',
};

const windFullLabels: Record<Wind, string> = {
  east: '東風',
  south: '南風',
  west: '西風',
  north: '北風',
};

const windTiles: Record<Wind, string> = {
  east: 'east.png',
  south: 'south.png',
  west: 'west.png',
  north: 'north.png',
};

const tileBase = `${import.meta.env.BASE_URL}mahjong-tiles/`;

const normalizeWind = (wind: string): Wind => {
  const normalized = wind.toLowerCase() as Wind;
  return windCodes.includes(normalized) ? normalized : 'east';
};

const formatMoney = (value: number) => `${value > 0 ? '+' : ''}${value.toLocaleString()}`;

const derivePointInput = (money: AnalysisResult['money']) => {
  if (typeof money === 'number') {
    return Math.abs(money);
  }

  if (typeof money !== 'object' || money === null) {
    return 0;
  }

  const values = Object.values(money as MoneyBreakdown).filter((value): value is number => typeof value === 'number');
  const losses = values.filter((value) => value < 0).map((value) => Math.abs(value));

  if (losses.length > 0) {
    return Math.max(...losses);
  }

  const gains = values.filter((value) => value > 0);
  return gains.length > 0 ? Math.max(...gains) : 0;
};

const getPlayerWind = (seatPosition: number, currentDealerId: number): Wind => {
  const distance = (seatPosition - currentDealerId + 4) % 4;
  return windCodes[distance] || 'east';
};

const Game = () => {
  const { roomCode } = useParams<{ roomCode: string }>();
  const navigate = useNavigate();

  const [gameState, setGameState] = useState<GameState | null>(null);
  const [showWinModal, setShowWinModal] = useState(false);
  const [winType, setWinType] = useState<'tsumo' | 'ron'>('ron');
  const [loserId, setLoserId] = useState<number | null>(null);
  const [points, setPoints] = useState<number>(0);
  const [modalError, setModalError] = useState('');
  const [copied, setCopied] = useState(false);

  const [showAnalyzer, setShowAnalyzer] = useState(false);
  const [analyzingPlayerId, setAnalyzingPlayerId] = useState<number | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchGame = async () => {
      try {
        const response = await axios.get<GameState>(`${API_URL}/api/game/${roomCode}`);
        setGameState(response.data);
      } catch (err) {
        console.error('Game not found', err);
        navigate('/game');
      }
    };

    if (roomCode) {
      void fetchGame();

      const socket = io(API_URL);
      socket.emit('join_game', { room_code: roomCode });

      socket.on('game_updated', (updatedGame: GameState) => {
        setGameState(updatedGame);
      });

      socket.on('game_ended', () => {
        navigate('/game');
      });

      return () => {
        socket.disconnect();
      };
    }

    return undefined;
  }, [roomCode, navigate]);

  const sortedPlayers = useMemo(
    () => [...(gameState?.players || [])].sort((a, b) => a.seat_position - b.seat_position),
    [gameState?.players],
  );

  const leader = useMemo(() => (
    sortedPlayers.length
      ? sortedPlayers.reduce((best, player) => (player.money > best.money ? player : best), sortedPlayers[0])
      : null
  ), [sortedPlayers]);

  const totalMoney = useMemo(
    () => sortedPlayers.reduce((total, player) => total + player.money, 0),
    [sortedPlayers],
  );

  const selectedWinner = sortedPlayers.find((player) => player.id === analyzingPlayerId) || null;

  const analyzerPresetSettings = useMemo<Partial<AnalysisSettings>>(() => {
    if (!gameState || !selectedWinner) {
      return {};
    }

    const winnerWind = getPlayerWind(selectedWinner.seat_position, gameState.dealer_id);
    const loser = loserId ? sortedPlayers.find((player) => player.id === loserId) : null;
    const loserWind = loser ? getPlayerWind(loser.seat_position, gameState.dealer_id) : 'east';

    return {
      round: normalizeWind(gameState.round_wind),
      dealer: 'east',
      continues: gameState.continues,
      seat: winnerWind,
      wins: winType === 'tsumo' ? 'self' : loserWind,
    };
  }, [gameState, loserId, selectedWinner, sortedPlayers, winType]);

  if (!gameState) {
    return <div className="game-container loading-state">載入牌局中...</div>;
  }

  const dealerPlayer = sortedPlayers.find((player) => player.seat_position === gameState.dealer_id) || null;
  const currentRoundWind = normalizeWind(gameState.round_wind);

  const handleAnalyze = async (formData: FormData) => {
    if (!gameState || analyzingPlayerId === null) return;

    setLoading(true);
    setError(null);

    const winnerPlayer = gameState.players.find((player) => player.id === analyzingPlayerId);
    const loserPlayer = loserId ? gameState.players.find((player) => player.id === loserId) : null;

    if (winnerPlayer) {
      const winnerWind = getPlayerWind(winnerPlayer.seat_position, gameState.dealer_id);
      const loserWind = loserPlayer ? getPlayerWind(loserPlayer.seat_position, gameState.dealer_id) : 'east';
      formData.set('round', normalizeWind(gameState.round_wind));
      formData.set('dealer', 'east');
      formData.set('seat', winnerWind);
      formData.set('wins', winType === 'tsumo' ? 'self' : loserWind);
      formData.set('continues', String(gameState.continues));
    }

    try {
      const response = await axios.post<AnalysisResult>(`${API_URL}/api/analyze`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setResult(response.data);

      if (response.data.is_winning && response.data.money !== undefined) {
        setPoints(derivePointInput(response.data.money));
        setShowAnalyzer(false);
        setShowWinModal(true);
      }
    } catch (err: unknown) {
      if (axios.isAxiosError<{ error?: string }>(err)) {
        setError(err.response?.data?.error || '辨識失敗，請確認圖片與後端服務。');
      } else {
        setError('發生未知錯誤，請稍後再試。');
      }
    } finally {
      setLoading(false);
    }
  };

  const submitWin = async () => {
    if (analyzingPlayerId === null) return;
    if (winType === 'ron' && loserId === null) {
      setModalError('請選擇放槍玩家。');
      return;
    }

    setModalError('');

    try {
      const response = await axios.post<GameState>(`${API_URL}/api/game/${roomCode}/win`, {
        winner_id: analyzingPlayerId,
        points,
        win_type: winType,
        loser_id: winType === 'ron' ? loserId : null,
      });

      setGameState(response.data);
      closeAnalyzer();
    } catch (err) {
      console.error('Failed to submit win', err);
      setModalError('寫入計分失敗，請確認後端服務。');
    }
  };

  const openWinModal = (playerId: number) => {
    const defaultLoser = sortedPlayers.find((player) => player.id !== playerId) || null;
    setAnalyzingPlayerId(playerId);
    setLoserId(defaultLoser?.id ?? null);
    setPoints(0);
    setWinType('ron');
    setResult(null);
    setShowAnalyzer(false);
    setShowWinModal(true);
    setModalError('');
  };

  const closeAnalyzer = () => {
    setShowAnalyzer(false);
    setShowWinModal(false);
    setAnalyzingPlayerId(null);
    setResult(null);
    setError(null);
    setModalError('');
    setPoints(0);
    setWinType('ron');
    setLoserId(null);
  };

  const endGame = async () => {
    if (window.confirm('確定要結束並刪除這個牌局嗎？這會移除玩家與所有歷史紀錄。')) {
      try {
        await axios.delete(`${API_URL}/api/game/${roomCode}`);
      } catch (err) {
        console.error('Failed to end game', err);
        setModalError('刪除牌局失敗。');
      }
    }
  };

  const copyRoomCode = () => {
    if (roomCode && navigator.clipboard) {
      void navigator.clipboard.writeText(roomCode);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    }
  };

  return (
    <section className="game-container">
      <header className="game-topbar">
        <div>
          <span className="eyebrow">Room {gameState.game_code} · Game ID #{gameState.id}</span>
          <h1>{windFullLabels[currentRoundWind]}牌局</h1>
          <p>第 {gameState.rounds.length + 1} 手 · 目前莊家 {dealerPlayer?.name || '未指定'} · 連莊 {gameState.continues}</p>
        </div>
        <div className="room-actions">
          <button className="ghost-btn" type="button" onClick={copyRoomCode}>{copied ? '已複製' : '複製房號'}</button>
          <button className="ghost-btn" type="button" onClick={() => navigate('/game')}>回房間</button>
          <button className="danger-btn" type="button" onClick={endGame}>結束牌局</button>
        </div>
      </header>

      <div className="game-summary">
        <div>
          <span>圈風</span>
          <strong>{windFullLabels[currentRoundWind]}</strong>
        </div>
        <div>
          <span>莊家座位</span>
          <strong>{dealerPlayer ? `#${dealerPlayer.seat_position} ${dealerPlayer.name}` : `#${gameState.dealer_id}`}</strong>
        </div>
        <div>
          <span>目前領先</span>
          <strong>{leader ? leader.name : '-'}</strong>
        </div>
        <div>
          <span>總分</span>
          <strong>{formatMoney(totalMoney)}</strong>
        </div>
      </div>

      <div className="game-dashboard">
        <section className="score-panel">
          <div className="panel-title-row">
            <div>
              <span className="section-kicker">Players</span>
              <h2>四家分數</h2>
            </div>
            <span className="panel-badge">{sortedPlayers.length} Seats</span>
          </div>

          <div className="score-list">
            {sortedPlayers.map((player) => {
              const wind = getPlayerWind(player.seat_position, gameState.dealer_id);
              const isDealer = player.seat_position === gameState.dealer_id;

              return (
                <button className={`score-row ${isDealer ? 'dealer' : ''}`} key={player.id} type="button" onClick={() => openWinModal(player.id)}>
                  <span className="seat-tile">
                    <img src={`${tileBase}${windTiles[wind]}`} alt="" />
                    {windShortLabels[wind]}
                  </span>
                  <span className="score-name">
                    <strong>{player.name}</strong>
                    <small>座位 #{player.seat_position} · Player ID #{player.id}</small>
                  </span>
                  {isDealer && <span className="dealer-chip">莊</span>}
                  <strong className={player.money >= 0 ? 'positive' : 'negative'}>{formatMoney(player.money)}</strong>
                </button>
              );
            })}
          </div>
        </section>

        <section className="table-panel">
          <div className="mahjong-layout" aria-label="麻將桌座位">
            <div className="table-center">
              <img src={`${tileBase}${windTiles[currentRoundWind]}`} alt="" />
              <span>{windFullLabels[currentRoundWind]}</span>
              <strong>{gameState.continues}</strong>
              <small>連莊</small>
            </div>

            {sortedPlayers.map((player, index) => {
              const positionClass = ['pos-bottom', 'pos-right', 'pos-top', 'pos-left'][index];
              const wind = getPlayerWind(player.seat_position, gameState.dealer_id);
              const isDealer = gameState.dealer_id === player.seat_position;

              return (
                <button
                  key={player.id}
                  type="button"
                  className={`player-seat ${positionClass} ${isDealer ? 'dealer' : ''}`}
                  onClick={() => openWinModal(player.id)}
                >
                  <span className="seat-wind">{windShortLabels[wind]}</span>
                  <span className="seat-name">{player.name}</span>
                  <strong className={player.money >= 0 ? 'positive' : 'negative'}>{formatMoney(player.money)}</strong>
                </button>
              );
            })}
          </div>
        </section>

        <section className="history-panel">
          <div className="panel-title-row">
            <div>
              <span className="section-kicker">Rounds</span>
              <h2>胡牌紀錄</h2>
            </div>
            <span className="panel-badge">{gameState.rounds.length}</span>
          </div>

          {gameState.rounds.length > 0 ? (
            <ol className="round-list">
              {[...gameState.rounds].reverse().map((round) => (
                <li key={round.id}>
                  <span className="round-id">#{round.id}</span>
                  <div>
                    <strong>{round.winner_name || '流局'}</strong>
                    <small>
                      {round.win_type === 'tsumo' ? '自摸' : round.win_type === 'ron' ? `榮和 ${round.loser_name || '未記錄'}` : '流局'}
                      {' · '}
                      {round.points_exchanged.toLocaleString()} 分
                      {round.is_dealer_win ? ' · 莊家胡牌' : ''}
                    </small>
                  </div>
                </li>
              ))}
            </ol>
          ) : (
            <p className="empty-state">還沒有胡牌紀錄。點選玩家即可登記第一手。</p>
          )}
        </section>
      </div>

      {showWinModal && selectedWinner && (
        <div className="modal-overlay">
          <div className="modal-content win-modal">
            <button className="close-modal" type="button" onClick={closeAnalyzer} aria-label="關閉">×</button>
            <span className="section-kicker">Record Win</span>
            <h2>登記 {selectedWinner.name} 胡牌</h2>

            <div className="win-form">
              <div className="segmented-control" role="group" aria-label="胡牌方式">
                <button className={winType === 'ron' ? 'active' : ''} type="button" onClick={() => setWinType('ron')}>
                  榮和
                </button>
                <button className={winType === 'tsumo' ? 'active' : ''} type="button" onClick={() => { setWinType('tsumo'); setLoserId(null); }}>
                  自摸
                </button>
              </div>

              {winType === 'ron' && (
                <label className="field">
                  <span>放槍玩家</span>
                  <select value={loserId || ''} onChange={(event) => setLoserId(Number(event.target.value))}>
                    <option value="" disabled>選擇放槍者</option>
                    {sortedPlayers
                      .filter((player) => player.id !== analyzingPlayerId)
                      .map((player) => (
                        <option key={player.id} value={player.id}>{player.name}</option>
                      ))}
                  </select>
                </label>
              )}

              <label className="field">
                <span>每家交換分數</span>
                <input
                  type="number"
                  value={points}
                  min="0"
                  onChange={(event) => setPoints(Number(event.target.value))}
                />
              </label>

              {modalError && <p className="error-text">{modalError}</p>}

              <div className="modal-actions">
                <button className="submit-win-btn" type="button" onClick={() => void submitWin()}>
                  寫入計分
                </button>
                <button className="secondary-btn" type="button" onClick={() => { setShowWinModal(false); setShowAnalyzer(true); }}>
                  用照片計算
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {showAnalyzer && selectedWinner && (
        <div className="modal-overlay">
          <div className="modal-content analyzer-modal">
            <button className="close-modal" type="button" onClick={closeAnalyzer} aria-label="關閉">×</button>
            {!result ? (
              <>
                <span className="section-kicker">Analyzer</span>
                <h2>{selectedWinner.name} 的手牌分析</h2>
                <UploadForm onAnalyze={handleAnalyze} loading={loading} compact presetSettings={analyzerPresetSettings} />
                {error && <div className="error-message">{error}</div>}
              </>
            ) : (
              <Results result={result} onReset={() => setResult(null)} />
            )}
          </div>
        </div>
      )}
    </section>
  );
};

export default Game;
