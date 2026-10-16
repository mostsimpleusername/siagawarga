const hostname = window.location.hostname
const port = window.location.port
const isViteStandalone = (hostname === 'localhost' || hostname === '127.0.0.1') && port === '5173'

export const API_BASE = isViteStandalone
  ? 'http://127.0.0.1:8000/api/v1'
  : '/api/v1'

