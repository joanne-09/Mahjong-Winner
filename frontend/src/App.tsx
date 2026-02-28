import { useState } from 'react';
import axios from 'axios';
import { BrowserRouter as Router, Routes, Route, Navigate, NavLink, useLocation } from 'react-router-dom';
import './App.css';
import { API_URL } from './config';
import UploadForm from './components/UploadForm';
import Results from './components/Results';
import Game from './components/Game';
import Lobby from './components/Lobby';

export interface AnalysisResult {
  money: number;
  breakdown: string;
  uploaded_image_url: string;
  generated_image_url: string;
}

// Inner component so we can use useLocation for styling navigation
const AppContent = () => {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const location = useLocation();

  const handleAnalyze = async (formData: FormData) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(`${API_URL}/api/analyze`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.error || 'An error occurred during analysis.');
    } finally {
      setLoading(false);
    }
  };

  const isGameRoute = location.pathname.startsWith('/game');

  return (
    <div className="app-container">
      <nav className="navbar">
        <div className="brand">Mahjong Winner</div>
        <div className="nav-links">
          <NavLink to="/" className={({ isActive }) => (isActive && !isGameRoute ? 'active' : '')} end>Analyzer</NavLink>
          <NavLink to="/game" className={() => (isGameRoute ? 'active' : '')}>Game Tracker</NavLink>
        </div>
      </nav>

      <main className="content">
        <Routes>
          {/* Analyzer Route */}
          <Route path="/" element={
            !result ? (
              <>
                <h1>Analyze Your Hand</h1>
                <p>Upload an image of your Mahjong hand to see the results.</p>
                <UploadForm onAnalyze={handleAnalyze} loading={loading} />
                {error && <div className="error-message">{error}</div>}
              </>
            ) : (
              <Results result={result} onReset={() => setResult(null)} />
            )
          } />

          {/* Game Routes */}
          <Route path="/game" element={<Lobby />} />
          <Route path="/game/:roomCode" element={<Game />} />
          
          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
};

function App() {
  return (
    <Router basename="/Mahjong-Winner">
      <AppContent />
    </Router>
  );
}

export default App;

