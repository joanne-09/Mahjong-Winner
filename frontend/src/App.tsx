import { useState } from 'react';
import axios from 'axios';
import './App.css';
import UploadForm from './components/UploadForm';
import Results from './components/Results';

export interface AnalysisResult {
  money: number;
  breakdown: string;
  uploaded_image_url: string;
  generated_image_url: string;
}

function App() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (formData: FormData) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post('http://localhost:5000/api/analyze', formData, {
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

  return (
    <div className="app-container">
      <nav className="navbar">
        <div className="brand">Mahjong Winner</div>
        <div className="nav-links">
          <a href="/">Home</a>
          <a href="#">About</a>
          <a href="#">Contact</a>
        </div>
      </nav>

      <main className="content">
        {!result ? (
          <>
            <h1>Analyze Your Hand</h1>
            <p>Upload an image of your Mahjong hand to see the results.</p>
            <UploadForm onAnalyze={handleAnalyze} loading={loading} />
            {error && <div className="error-message">{error}</div>}
          </>
        ) : (
          <Results result={result} onReset={() => setResult(null)} />
        )}
      </main>
    </div>
  );
}

export default App;

