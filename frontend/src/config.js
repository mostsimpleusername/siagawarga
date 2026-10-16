const hostname = window.location.hostname
const isLocal = hostname === 'localhost' || hostname === '127.0.0.1'
export const API_BASE = isLocal
  ? 'http://127.0.0.1:8000/api/v1'
  : window.location.origin + '/api/v1'
