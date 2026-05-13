import type { AnalysisResult, MoneyBreakdown, Wind } from '../App';
import { API_URL } from '../config';

interface ResultsProps {
  result: AnalysisResult;
  onReset: () => void;
}

const windLabels: Record<Wind, string> = {
  east: '東家',
  south: '南家',
  west: '西家',
  north: '北家',
};

const windOrder: Wind[] = ['east', 'south', 'west', 'north'];

const isMoneyBreakdown = (money: AnalysisResult['money']): money is MoneyBreakdown => (
  typeof money === 'object' && money !== null
);

const formatMoney = (value: number) => (
  `${value > 0 ? '+' : ''}${value.toLocaleString()}`
);

const formatBreakdown = (item: unknown) => {
  if (Array.isArray(item)) {
    return item.map((part) => String(part)).join(' / ');
  }

  if (typeof item === 'object' && item !== null) {
    return JSON.stringify(item);
  }

  return String(item);
};

const getTopDelta = (money: AnalysisResult['money']) => {
  if (typeof money === 'number') {
    return money;
  }

  if (!isMoneyBreakdown(money)) {
    return null;
  }

  const values = Object.values(money).filter((value): value is number => typeof value === 'number');
  return values.length ? Math.max(...values) : null;
};

const toAbsoluteUrl = (url: string) => (
  url.startsWith('http') ? url : `${API_URL}${url}`
);

const Results = ({ result, onReset }: ResultsProps) => {
  const uploadedImage = toAbsoluteUrl(result.uploaded_image_url);
  const generatedImage = result.generated_image_url ? toAbsoluteUrl(result.generated_image_url) : null;
  const topDelta = getTopDelta(result.money);
  const moneyBreakdown = isMoneyBreakdown(result.money) ? result.money : null;

  if (result.is_winning === false) {
    return (
      <section className="results-container">
        <header className="result-header">
          <span className="status-pill danger">未胡牌</span>
          <h1>這張手牌尚未構成胡牌。</h1>
          <p>{result.message || 'The uploaded hand does not form a winning condition.'}</p>
        </header>

        <div className="results-grid single">
          <article className="result-card">
            <h2>上傳照片</h2>
            <img src={uploadedImage} alt="上傳的麻將手牌" />
          </article>
        </div>

        <button onClick={onReset} className="reset-btn">重新分析</button>
      </section>
    );
  }

  return (
    <section className="results-container">
      <header className="result-header">
        <span className="status-pill success">胡牌成立</span>
        <h1>分析完成</h1>
        {topDelta !== null && (
          <div className="money-hero">
            <span>最大進帳</span>
            <strong>{formatMoney(topDelta)}</strong>
          </div>
        )}
      </header>

      <div className="results-grid">
        <article className="result-card">
          <h2>上傳照片</h2>
          <img src={uploadedImage} alt="上傳的麻將手牌" />
        </article>
        {generatedImage && (
          <article className="result-card">
            <h2>辨識結果</h2>
            <img src={generatedImage} alt="後端產生的麻將辨識結果" />
          </article>
        )}
      </div>

      <div className="result-details">
        <article className="detail-card">
          <div className="detail-card-heading">
            <span className="section-kicker">Tai</span>
            <h2>台數明細</h2>
          </div>
          {result.tai_log && result.tai_log.length > 0 ? (
            <ul className="tai-list">
              {result.tai_log.map((log, index) => (
                <li key={`${log}-${index}`}>{log}</li>
              ))}
            </ul>
          ) : (
            <p className="empty-state">後端沒有回傳台數紀錄。</p>
          )}
        </article>

        <article className="detail-card">
          <div className="detail-card-heading">
            <span className="section-kicker">Money</span>
            <h2>得失分</h2>
          </div>
          {moneyBreakdown ? (
            <div className="money-table">
              {windOrder.map((wind) => {
                const value = moneyBreakdown[wind] ?? 0;
                return (
                  <div className="money-row" key={wind}>
                    <span>{windLabels[wind]}</span>
                    <strong className={value >= 0 ? 'positive' : 'negative'}>{formatMoney(value)}</strong>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="single-money">{typeof result.money === 'number' ? formatMoney(result.money) : '0'}</div>
          )}
        </article>

        <article className="detail-card breakdown-card">
          <div className="detail-card-heading">
            <span className="section-kicker">Melds</span>
            <h2>牌型拆解</h2>
          </div>
          {result.breakdown && result.breakdown.length > 0 ? (
            <ul className="breakdown-list">
              {result.breakdown.map((item, index) => (
                <li key={index}>{formatBreakdown(item)}</li>
              ))}
            </ul>
          ) : (
            <p className="empty-state">後端沒有回傳牌型拆解。</p>
          )}
        </article>
      </div>

      <button onClick={onReset} className="reset-btn">分析另一副牌</button>
    </section>
  );
};

export default Results;
