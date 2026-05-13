const defaultApiUrl = import.meta.env.DEV ? 'http://localhost:5000' : '';
const rawBasePath = import.meta.env.VITE_BASE_PATH || '/Mahjong-Winner/';

export const API_URL = import.meta.env.VITE_API_URL || defaultApiUrl;
export const APP_BASENAME = rawBasePath === '/' ? undefined : rawBasePath.replace(/\/$/, '');
