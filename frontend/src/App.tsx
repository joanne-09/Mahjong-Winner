import { useState } from 'react';
import axios from 'axios';
import { BrowserRouter as Router, Routes, Route, Navigate, NavLink, useLocation } from 'react-router-dom';
import './App.css';
import { API_URL, APP_BASENAME } from './config';
import UploadForm from './components/UploadForm';
import Results from './components/Results';
import Game from './components/Game';
import Lobby from './components/Lobby';

export type Wind = 'east' | 'south' | 'west' | 'north';

export interface MoneyBreakdown {
  east?: number;
  south?: number;
  west?: number;
  north?: number;
  [key: string]: number | undefined;
}

export interface AnalysisResult {
  is_winning: boolean;
  message?: string;
  money?: MoneyBreakdown | number;
  breakdown?: unknown[];
  tai_log?: string[];
  uploaded_image_url: string;
  generated_image_url?: string;
}

const tileBase = `${import.meta.env.BASE_URL}mahjong-tiles/`;
const showcaseTiles = ['east.png', 'south.png', 'west.png', 'north.png', 'b_one.png', 'b_five.png', 'w_nine.png'];

const AppContent = () => {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const location = useLocation();
  const isGameRoute = location.pathname.startsWith('/game');

  const handleAnalyze = async (formData: FormData) => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post<AnalysisResult>(`${API_URL}/api/analyze`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setResult(response.data);
    } catch (err: unknown) {
      if (axios.isAxiosError<{ error?: string }>(err)) {
        setError(err.response?.data?.error || '辨識失敗，請確認後端服務與圖片格式。');
      } else {
        setError('發生未知錯誤，請稍後再試。');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <nav className="top-nav" aria-label="主要導覽">
        <NavLink to="/" className="brand" aria-label="Mahjong Winner 首頁">
          <span className="brand-mark" aria-hidden="true">
            <img src={`${tileBase}east.png`} alt="" />
          </span>
          <span>
            <strong>Mahjong Winner</strong>
            <small>台灣麻將計分</small>
          </span>
        </NavLink>
        <div className="nav-links">
          <NavLink to="/" end className={({ isActive }) => (isActive && !isGameRoute ? 'active' : undefined)}>
            手牌辨識
          </NavLink>
          <NavLink to="/game" className={() => (isGameRoute ? 'active' : undefined)}>
            對局計分
          </NavLink>
        </div>
      </nav>

      <main className="content">
        <Routes>
          <Route
            path="/"
            element={
              !result ? (
                <section className="analyzer-workspace">
                  <div className="workspace-intro">
                    <span className="eyebrow">Mahjong Winner</span>
                    <h1>拍下手牌，快速算出胡牌台數與得失分。</h1>
                    <p>
                      依照後端計分欄位設計，從圈風、座風、連莊、骰子到特殊役種都能直接輸入。
                    </p>
                    <div className="tile-showcase" aria-label="麻將牌素材">
                      {showcaseTiles.map((tile) => (
                        <img key={tile} src={`${tileBase}${tile}`} alt="" />
                      ))}
                    </div>
                    <dl className="feature-metrics">
                      <div>
                        <dt>API 欄位</dt>
                        <dd>完整對齊</dd>
                      </div>
                      <div>
                        <dt>模式</dt>
                        <dd>照片與計分</dd>
                      </div>
                      <div>
                        <dt>同步</dt>
                        <dd>即時房間</dd>
                      </div>
                    </dl>
                  </div>

                  <div className="workspace-panel">
                    <UploadForm onAnalyze={handleAnalyze} loading={loading} />
                    {error && <div className="error-message">{error}</div>}
                  </div>
                </section>
              ) : (
                <Results result={result} onReset={() => setResult(null)} />
              )
            }
          />
          <Route path="/game" element={<Lobby />} />
          <Route path="/game/:roomCode" element={<Game />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
};

function App() {
  return (
    <Router basename={APP_BASENAME}>
      <AppContent />
    </Router>
  );
}

export default App;
