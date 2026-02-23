import React, { useState } from 'react';

interface UploadFormProps {
  onAnalyze: (formData: FormData) => void;
  loading: boolean;
}

const UploadForm: React.FC<UploadFormProps> = ({ onAnalyze, loading }) => {
  const [file, setFile] = useState<File | null>(null);
  const [settings, setSettings] = useState({
    round: 'east',
    dealer: 'east',
    continues: 1,
    dice: 18,
    seat: 'east',
    wins: 'east',
    base: 100,
    bonus: 30,
  });

  const handleSettingChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setSettings((prev) => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    Object.entries(settings).forEach(([key, value]) => {
      formData.append(key, String(value));
    });

    onAnalyze(formData);
  };

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <div className="settings-group">
        <h3>Game Settings</h3>
        
        <div className="setting-item">
          <label htmlFor="round">Round:</label>
          <select name="round" id="round" value={settings.round} onChange={handleSettingChange}>
            <option value="east">East</option>
            <option value="south">South</option>
            <option value="west">West</option>
            <option value="north">North</option>
          </select>
        </div>

        <div className="setting-item">
          <label htmlFor="dealer">Dealer:</label>
          <select name="dealer" id="dealer" value={settings.dealer} onChange={handleSettingChange}>
            <option value="east">East</option>
            <option value="south">South</option>
            <option value="west">West</option>
            <option value="north">North</option>
          </select>
        </div>

        <div className="setting-item">
          <label htmlFor="continues">Continues:</label>
          <input type="number" name="continues" id="continues" value={settings.continues} min="0" onChange={handleSettingChange} />
        </div>

        <div className="setting-item">
          <label htmlFor="dice">Dice:</label>
          <input type="number" name="dice" id="dice" value={settings.dice} min="2" max="18" onChange={handleSettingChange} />
        </div>

        <div className="setting-item">
          <label htmlFor="seat">Your Seat:</label>
          <select name="seat" id="seat" value={settings.seat} onChange={handleSettingChange}>
            <option value="east">East</option>
            <option value="south">South</option>
            <option value="west">West</option>
            <option value="north">North</option>
          </select>
        </div>

        <div className="setting-item">
          <label htmlFor="wins">Winning From:</label>
          <select name="wins" id="wins" value={settings.wins} onChange={handleSettingChange}>
            <option value="east">East</option>
            <option value="south">South</option>
            <option value="west">West</option>
            <option value="north">North</option>
            <option value="self">Self-Drawn</option>
          </select>
        </div>

        <div className="setting-item">
          <label htmlFor="base">Base Money:</label>
          <input type="number" name="base" id="base" value={settings.base} min="0" onChange={handleSettingChange} />
        </div>

        <div className="setting-item">
          <label htmlFor="bonus">Bonus Money:</label>
          <input type="number" name="bonus" id="bonus" value={settings.bonus} min="0" onChange={handleSettingChange} />
        </div>
      </div>

      <div className="upload-group">
        <label htmlFor="file">Upload Hand Image:</label>
        <input type="file" name="file" id="file" required onChange={handleFileChange} accept=".png,.jpg,.jpeg" />
      </div>
      
      <button type="submit" disabled={!file || loading} className="submit-btn">
        {loading ? 'Analyzing...' : 'Analyze'}
      </button>
    </form>
  );
};

export default UploadForm;

