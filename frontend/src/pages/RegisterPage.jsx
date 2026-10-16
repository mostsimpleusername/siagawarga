import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { API_BASE } from '../config'

export default function RegisterPage() {
  const navigate = useNavigate()
  const [nama, setNama] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [registeredEmail, setRegisteredEmail] = useState('')
  const [successInfo, setSuccessInfo] = useState('')
  const [resendLoading, setResendLoading] = useState(false)
  const [resendMessage, setResendMessage] = useState('')

  async function handleKirimUlang() {
    if (!registeredEmail) return
    setResendLoading(true)
    setResendMessage('')
    try {
      const res = await fetch(`${API_BASE}/auth/kirim-ulang-verifikasi`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: registeredEmail }),
      })
      const data = await res.json()
      setResendMessage(data.detail || 'Tautan verifikasi baru telah dikirim.')
    } catch {
      setResendMessage('Gagal menghubungi server untuk mengirim ulang verifikasi.')
    } finally {
      setResendLoading(false)
    }
  }

  async function handleRegister(e) {
    e.preventDefault()
    if (!email && !phone) {
      setError('Harap isi minimal email atau nomor HP.')
      return
    }
    setLoading(true)
    setError('')
    setSuccessInfo('')
    setResendMessage('')
    const payload = { nama, kata_sandi: password }
    if (email) payload.email = email
    if (phone) payload.nomor_hp = phone
    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await res.json()
      if (!res.ok) {
        const msg = Array.isArray(data.detail)
          ? data.detail.map(d => d.msg || d.message || String(d)).join(', ')
          : data.detail || 'Pendaftaran gagal.'
        setError(msg)
        return
      }

      if (email) {
        setRegisteredEmail(email)
        setSuccessInfo(data.pesan || 'Registrasi berhasil! Tautan verifikasi telah dikirimkan ke email Anda.')
      } else {
        alert('✅ Pendaftaran berhasil! Silakan masuk.')
        navigate('/login')
      }
    } catch {
      setError('Tidak dapat terhubung ke server.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page-wrapper">
      <header className="auth-header-bar">
        <Link to="/" className="brand-wrapper">
          <img src="/assets/logo-siagawarga.png" alt="SiagaWarga" className="brand-logo-img" />
          <span className="brand-text">SiagaWarga</span>
        </Link>
      </header>

      <main className="auth-center-container">
        <div className="auth-card-duo">
          <div className="auth-left-hero">
            <div className="auth-pattern-overlay"></div>
            <div className="auth-left-content">
              <span className="auth-left-badge">DAFTAR SEBAGAI WARGA</span>
              <h2 className="auth-left-title">Bergabung dan Mulai Berkontribusi</h2>
              <p className="auth-left-desc">Buat akun warga untuk mulai melaporkan permasalahan lingkungan di sekitar Anda.</p>
            </div>
          </div>

          <div className="auth-right-form">
            <h1 className="auth-form-title">Daftar akun warga</h1>
            <p className="auth-form-subtitle">Isi data diri untuk membuat akun baru.</p>

            {successInfo ? (
              <div style={{ padding: '24px 20px', background: '#ecfdf5', border: '1px solid #a7f3d0', borderRadius: 12, marginBottom: 20 }}>
                <div style={{ fontSize: 24, marginBottom: 8 }}>📩</div>
                <h3 style={{ margin: '0 0 8px 0', color: '#065f46', fontSize: 18, fontWeight: 700 }}>Pendaftaran Berhasil!</h3>
                <p style={{ margin: '0 0 16px 0', color: '#047857', fontSize: 14, lineHeight: 1.5 }}>
                  {successInfo} Silakan cek inbox atau folder spam email Anda (<strong>{registeredEmail}</strong>) untuk mengaktifkan akun.
                </p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  <button
                    type="button"
                    onClick={handleKirimUlang}
                    disabled={resendLoading}
                    style={{
                      background: '#047857',
                      color: '#ffffff',
                      border: 'none',
                      padding: '10px 16px',
                      borderRadius: 8,
                      fontSize: 13,
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    {resendLoading ? 'Mengirim ulang...' : 'Kirim Ulang Email Verifikasi'}
                  </button>

                  <Link
                    to="/login"
                    style={{
                      display: 'inline-block',
                      textAlign: 'center',
                      padding: '10px 16px',
                      borderRadius: 8,
                      background: '#ffffff',
                      color: '#047857',
                      border: '1px solid #a7f3d0',
                      textDecoration: 'none',
                      fontSize: 13,
                      fontWeight: 600,
                    }}
                  >
                    Menuju Halaman Masuk
                  </Link>
                </div>

                {resendMessage && (
                  <div style={{ marginTop: 12, fontSize: 13, color: '#065f46', background: '#d1fae5', padding: '8px 12px', borderRadius: 6 }}>
                    {resendMessage}
                  </div>
                )}
              </div>
            ) : (
              <form onSubmit={handleRegister}>
                <div className="auth-input-group">
                  <label>Nama lengkap *</label>
                  <input type="text" value={nama} onChange={e => setNama(e.target.value)} placeholder="Nama lengkap Anda" required />
                </div>
                <div className="auth-input-group">
                  <label>Email</label>
                  <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="nama@email.com" />
                </div>
                <div className="auth-input-group">
                  <label>Nomor HP</label>
                  <input type="tel" value={phone} onChange={e => setPhone(e.target.value)} placeholder="0812xxxxxxxx" />
                </div>
                <div className="auth-input-group">
                  <label>Kata sandi *</label>
                  <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Minimal 8 karakter" required minLength={8} />
                </div>
                {error && (
                  <div style={{color:'#dc2626',fontSize:13,marginBottom:12,padding:'10px 14px',background:'#fef2f2',borderRadius:8}}>
                    {error}
                  </div>
                )}
                <button type="submit" className="btn-auth-submit" disabled={loading}>
                  <span>{loading ? 'Mendaftarkan...' : 'Buat Akun'}</span>
                </button>
              </form>
            )}

            <div className="auth-switch-link">
              Sudah punya akun? <Link to="/login">Masuk</Link>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
