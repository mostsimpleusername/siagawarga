const hostname = window.location.hostname
const port = window.location.port
const isViteStandalone = (hostname === 'localhost' || hostname === '127.0.0.1') && port === '5173'

export const API_BASE = import.meta.env.VITE_API_BASE || "https://siagawarga-production.up.railway.app/api/v1";
