import React from 'react';
import type { AnalysisResult } from '../App';
import { API_URL } from '../config';

interface ResultsProps {
  result: AnalysisResult;
  onReset: () => void;
}

const Results: React.FC<ResultsProps> = ({ result, onReset }) => {
  return (
    <div className="results-container">
      <h1>Analysis Results</h1>
      
      <div className="results-grid">
        <div className="result-card">
          <h3>Your Hand</h3>
          <img src={`${API_URL}${result.uploaded_image_url}`} alt="Uploaded Hand" />
        </div>
        <div className="result-card">
          <h3>Winning Breakdown</h3>
          <img src={`${API_URL}${result.generated_image_url}`} alt="Generated Winning Hand" />
        </div>
      </div>

      <div className="result-details">
        <div className="detail-card">
          <h3>Breakdown Data</h3>
          <pre>{result.breakdown}</pre>
        </div>
        <div className="detail-card">
          <h3>Final Money</h3>
          <pre>{result.money}</pre>
        </div>
      </div>

      <button onClick={onReset} className="reset-btn">Analyze Another Hand</button>
    </div>
  );
};

export default Results;

