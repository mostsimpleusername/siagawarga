/**
 * SiagaWarga - Runtime Configuration Helper
 * Mengatur endpoint API secara dinamis:
 * - Localhost / 127.0.0.1: Mengarah ke http://127.0.0.1:8000/api/v1
 * - Vercel / Production: Mengarah ke /api/v1 (karena API di-host di domain yang sama via Vercel Serverless)
 * - Custom override: Dapat diset manual via localStorage.setItem("SIAGAWARGA_API_BASE", "...")
 */
(function() {
  const hostname = window.location.hostname;
  const isLocal = hostname === "localhost" || 
                  hostname === "127.0.0.1" || 
                  hostname === "0.0.0.0" || 
                  window.location.protocol === "file:";

  const customBase = localStorage.getItem("SIAGAWARGA_API_BASE");

  if (customBase) {
    window.API_BASE = customBase.replace(/\/$/, "");
  } else if (isLocal) {
    window.API_BASE = "http://127.0.0.1:8000/api/v1";
  } else {
    // Pada deployment Vercel dengan rewrites, backend berada pada domain yang sama
    window.API_BASE = window.location.origin + "/api/v1";
  }

  console.log("[SiagaWarga] API Base URL:", window.API_BASE);
})();
