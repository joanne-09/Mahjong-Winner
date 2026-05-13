import { useMemo, useState } from 'react';
import type { ChangeEvent, FormEvent } from 'react';
import type { Wind } from '../App';

export interface AnalysisSettings {
  round: Wind;
  dealer: Wind;
  continues: number;
  dice: number;
  seat: Wind;
  wins: Wind | 'self';
  base: number;
  bonus: number;
  concealed: boolean;
  ready: boolean;
  heavenly_win: boolean;
  heavenly_win_tai: number;
  human_win: boolean;
  human_win_tai: number;
  earthly_win: boolean;
  earthly_win_tai: number;
  heavenly_ready: boolean;
  heavenly_ready_tai: number;
  earthly_ready: boolean;
  earthly_ready_tai: number;
  seven_robbing_one: boolean;
  seven_robbing_one_tai: number;
  rob_kong: boolean;
  rob_kong_tai: number;
  single_wait: boolean;
  half_qiu: boolean;
  kong_draw: boolean;
  kong_draw_tai: number;
  last_discard: boolean;
  last_discard_tai: number;
  last_tile: boolean;
  last_tile_tai: number;
  quan_qiu: boolean;
  see_flower_word: boolean;
  open_kongs: number;
  concealed_kongs: number;
  concealed_triplets: number;
}

interface UploadFormProps {
  onAnalyze: (formData: FormData) => void;
  loading: boolean;
  compact?: boolean;
  presetSettings?: Partial<AnalysisSettings>;
}

const DEFAULT_SETTINGS: AnalysisSettings = {
  round: 'east',
  dealer: 'east',
  continues: 0,
  dice: 18,
  seat: 'east',
  wins: 'east',
  base: 100,
  bonus: 30,
  concealed: false,
  ready: false,
  heavenly_win: false,
  heavenly_win_tai: 24,
  human_win: false,
  human_win_tai: 16,
  earthly_win: false,
  earthly_win_tai: 16,
  heavenly_ready: false,
  heavenly_ready_tai: 16,
  earthly_ready: false,
  earthly_ready_tai: 8,
  seven_robbing_one: false,
  seven_robbing_one_tai: 8,
  rob_kong: false,
  rob_kong_tai: 1,
  single_wait: false,
  half_qiu: false,
  kong_draw: false,
  kong_draw_tai: 1,
  last_discard: false,
  last_discard_tai: 1,
  last_tile: false,
  last_tile_tai: 1,
  quan_qiu: false,
  see_flower_word: false,
  open_kongs: 0,
  concealed_kongs: 0,
  concealed_triplets: 0,
};

const windOptions: Array<{ value: Wind; label: string; tile: string }> = [
  { value: 'east', label: '東風', tile: '東' },
  { value: 'south', label: '南風', tile: '南' },
  { value: 'west', label: '西風', tile: '西' },
  { value: 'north', label: '北風', tile: '北' },
];

const numberFields = new Set<keyof AnalysisSettings>([
  'continues',
  'dice',
  'base',
  'bonus',
  'heavenly_win_tai',
  'human_win_tai',
  'earthly_win_tai',
  'heavenly_ready_tai',
  'earthly_ready_tai',
  'seven_robbing_one_tai',
  'rob_kong_tai',
  'kong_draw_tai',
  'last_discard_tai',
  'last_tile_tai',
  'open_kongs',
  'concealed_kongs',
  'concealed_triplets',
]);

const quickFlags: Array<{ key: keyof AnalysisSettings; label: string; hint: string }> = [
  { key: 'concealed', label: '門清', hint: '未吃碰明槓' },
  { key: 'single_wait', label: '獨聽', hint: '單張等待' },
  { key: 'quan_qiu', label: '全求人', hint: '全靠他人放銃' },
  { key: 'see_flower_word', label: '見花見字', hint: '花牌與字牌條件' },
];

const eventFlags: Array<{
  key: keyof AnalysisSettings;
  taiKey: keyof AnalysisSettings;
  label: string;
  hint: string;
  defaultTai: number;
}> = [
  { key: 'heavenly_win', taiKey: 'heavenly_win_tai', label: '天胡', hint: '莊家起手胡', defaultTai: 24 },
  { key: 'human_win', taiKey: 'human_win_tai', label: '人胡', hint: '閒家首巡胡', defaultTai: 16 },
  { key: 'earthly_win', taiKey: 'earthly_win_tai', label: '地胡', hint: '閒家起手自摸', defaultTai: 16 },
  { key: 'heavenly_ready', taiKey: 'heavenly_ready_tai', label: '天聽', hint: '莊家起手聽', defaultTai: 16 },
  { key: 'earthly_ready', taiKey: 'earthly_ready_tai', label: '地聽', hint: '閒家起手聽', defaultTai: 8 },
  { key: 'seven_robbing_one', taiKey: 'seven_robbing_one_tai', label: '七搶一', hint: '七花搶最後一花', defaultTai: 8 },
  { key: 'rob_kong', taiKey: 'rob_kong_tai', label: '搶槓', hint: '搶明槓胡牌', defaultTai: 1 },
  { key: 'kong_draw', taiKey: 'kong_draw_tai', label: '槓上開花', hint: '槓後補牌自摸', defaultTai: 1 },
  { key: 'last_discard', taiKey: 'last_discard_tai', label: '河底撈魚', hint: '最後打出放銃', defaultTai: 1 },
  { key: 'last_tile', taiKey: 'last_tile_tai', label: '海底撈月', hint: '最後一張自摸', defaultTai: 1 },
];

const tileBase = `${import.meta.env.BASE_URL}mahjong-tiles/`;

const UploadForm = ({ onAnalyze, loading, compact = false, presetSettings }: UploadFormProps) => {
  const initialSettings = useMemo(
    () => ({ ...DEFAULT_SETTINGS, ...presetSettings }),
    [presetSettings],
  );
  const [file, setFile] = useState<File | null>(null);
  const [settings, setSettings] = useState<AnalysisSettings>(initialSettings);

  const handleSettingChange = (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = event.target;
    const settingName = name as keyof AnalysisSettings;
    const nextValue = event.target instanceof HTMLInputElement && event.target.type === 'checkbox'
      ? event.target.checked
      : numberFields.has(settingName)
        ? Number(value)
        : value;

    setSettings((current) => ({
      ...current,
      [settingName]: nextValue,
    }) as AnalysisSettings);
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      setFile(event.target.files[0]);
    }
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    Object.entries(settings).forEach(([key, value]) => {
      formData.append(key, String(value));
    });

    onAnalyze(formData);
  };

  return (
    <form className={`upload-form ${compact ? 'compact' : ''}`} onSubmit={handleSubmit}>
      <section className="upload-panel file-panel">
        <div className="panel-heading-row">
          <div>
            <span className="section-kicker">Photo</span>
            <h2>手牌照片</h2>
          </div>
          <div className="mini-tiles" aria-hidden="true">
            <img src={`${tileBase}b_one.png`} alt="" />
            <img src={`${tileBase}b_five.png`} alt="" />
            <img src={`${tileBase}w_nine.png`} alt="" />
          </div>
        </div>

        <label className={`drop-zone ${file ? 'has-file' : ''}`} htmlFor="file">
          <input type="file" name="file" id="file" required onChange={handleFileChange} accept=".png,.jpg,.jpeg" />
          <span className="drop-icon" aria-hidden="true">+</span>
          <span className="drop-title">{file ? file.name : '選擇 JPG / PNG 手牌照片'}</span>
          <span className="drop-meta">{file ? `${Math.ceil(file.size / 1024)} KB` : '支援後端 /api/analyze 的 file 欄位'}</span>
        </label>
      </section>

      <section className="upload-panel">
        <div className="panel-heading-row">
          <div>
            <span className="section-kicker">Round</span>
            <h2>牌局設定</h2>
          </div>
          <div className="wind-strip" aria-hidden="true">
            {windOptions.map((wind) => (
              <span key={wind.value}>{wind.tile}</span>
            ))}
          </div>
        </div>

        <div className="form-grid">
          <label className="field">
            <span>圈風</span>
            <select name="round" value={settings.round} onChange={handleSettingChange}>
              {windOptions.map((wind) => (
                <option key={wind.value} value={wind.value}>{wind.label}</option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>莊家門風</span>
            <select name="dealer" value={settings.dealer} onChange={handleSettingChange}>
              {windOptions.map((wind) => (
                <option key={wind.value} value={wind.value}>{wind.label}</option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>胡牌者座風</span>
            <select name="seat" value={settings.seat} onChange={handleSettingChange}>
              {windOptions.map((wind) => (
                <option key={wind.value} value={wind.value}>{wind.label}</option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>胡牌來源</span>
            <select name="wins" value={settings.wins} onChange={handleSettingChange}>
              {windOptions.map((wind) => (
                <option key={wind.value} value={wind.value}>{wind.label}放槍</option>
              ))}
              <option value="self">自摸</option>
            </select>
          </label>

          <label className="field">
            <span>連莊</span>
            <input type="number" name="continues" value={settings.continues} min="0" onChange={handleSettingChange} />
          </label>

          <label className="field">
            <span>骰子點數</span>
            <input type="number" name="dice" value={settings.dice} min="2" max="18" onChange={handleSettingChange} />
          </label>
        </div>
      </section>

      <section className="upload-panel">
        <div>
          <span className="section-kicker">Money</span>
          <h2>底台金額</h2>
        </div>
        <div className="form-grid two-columns">
          <label className="field">
            <span>底</span>
            <input type="number" name="base" value={settings.base} min="0" onChange={handleSettingChange} />
          </label>

          <label className="field">
            <span>台</span>
            <input type="number" name="bonus" value={settings.bonus} min="0" onChange={handleSettingChange} />
          </label>
        </div>
      </section>

      <section className="upload-panel">
        <div>
          <span className="section-kicker">Hand</span>
          <h2>手牌狀態</h2>
        </div>
        <div className="toggle-grid">
          {quickFlags.map((flag) => (
            <label className="toggle-chip" key={flag.key}>
              <input
                type="checkbox"
                name={flag.key}
                checked={Boolean(settings[flag.key])}
                onChange={handleSettingChange}
              />
              <span>
                <strong>{flag.label}</strong>
                <small>{flag.hint}</small>
              </span>
            </label>
          ))}
        </div>
      </section>

      <section className="upload-panel">
        <div>
          <span className="section-kicker">Events</span>
          <h2>特殊狀況</h2>
        </div>
        <div className="toggle-grid event-grid">
          {eventFlags.map((flag) => (
            <div className={`event-card ${settings[flag.key] ? 'selected' : ''}`} key={flag.key}>
              <label className="event-toggle">
                <input
                  type="checkbox"
                  name={flag.key}
                  checked={Boolean(settings[flag.key])}
                  onChange={handleSettingChange}
                />
                <span>
                  <strong>{flag.label}</strong>
                  <small>{flag.hint}</small>
                </span>
              </label>
              <label className="event-tai-field">
                <span>台數</span>
                <input
                  type="number"
                  name={flag.taiKey}
                  value={Number(settings[flag.taiKey])}
                  min="0"
                  onChange={handleSettingChange}
                  disabled={!settings[flag.key]}
                  aria-label={`${flag.label} 台數，預設 ${flag.defaultTai} 台`}
                />
              </label>
            </div>
          ))}
        </div>
      </section>

      <section className="upload-panel">
        <div>
          <span className="section-kicker">Kongs</span>
          <h2>槓與暗刻</h2>
        </div>
        <div className="form-grid three-columns">
          <label className="field">
            <span>明槓 / 加槓</span>
            <input type="number" name="open_kongs" value={settings.open_kongs} min="0" max="4" onChange={handleSettingChange} />
          </label>

          <label className="field">
            <span>暗槓</span>
            <input type="number" name="concealed_kongs" value={settings.concealed_kongs} min="0" max="4" onChange={handleSettingChange} />
          </label>

          <label className="field">
            <span>暗刻數</span>
            <select name="concealed_triplets" value={settings.concealed_triplets} onChange={handleSettingChange}>
              <option value="0">0</option>
              <option value="1">1</option>
              <option value="2">2</option>
              <option value="3">3</option>
              <option value="4">4</option>
              <option value="5">5</option>
            </select>
          </label>
        </div>
      </section>

      <button type="submit" disabled={!file || loading} className="submit-btn">
        {loading ? '辨識中...' : '開始分析'}
      </button>
    </form>
  );
};

export default UploadForm;
