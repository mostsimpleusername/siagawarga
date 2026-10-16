import { Link } from 'react-router-dom'

export default function LandingPage() {
  const categories = [
    { name: 'Saluran Air', desc: 'Drainase dan genangan air di area publik.', icon: '/assets/icon-drainase.svg' },
    { name: 'Penerangan', desc: 'Lampu jalan rusak atau tidak berfungsi.', icon: '/assets/icon-penerangan.svg' },
    { name: 'Kebersihan', desc: 'Sampah menumpuk dan masalah kebersihan.', icon: '/assets/icon-kebersihan.svg' },
    { name: 'Fasilitas Umum', desc: 'Kerusakan fasilitas publik lainnya.', icon: '/assets/icon-fasilitas.svg' },
  ]

  const followSteps = [
    { icon: '📩', title: 'Laporan diterima', sub: 'Sistem mencatat dan memverifikasi laporan.' },
    { icon: '🔍', title: 'Verifikasi petugas', sub: 'Tim command center meninjau dan memprioritas.' },
    { icon: '🛠', title: 'Penanganan lapangan', sub: 'Tim teknis diterjunkan ke lokasi masalah.' },
    { icon: '✅', title: 'Selesai & terverifikasi', sub: 'Laporan ditutup dan warga mendapat konfirmasi.' },
  ]

  return (
    <div>
      <header className="header-publik">
        <Link to="/" className="brand-wrapper">
          <img src="/assets/logo-siagawarga.png" alt="Logo SiagaWarga" className="brand-logo-img" />
          <span className="brand-text">SiagaWarga</span>
        </Link>
        <div>
          <Link to="/login" className="header-petugas-link">Masuk</Link>
        </div>
      </header>

      <section className="hero-figma">
        <div className="hero-bg-overlay"></div>
        <div className="hero-gradient-layer"></div>
        <div className="hero-content">
          <span className="hero-label">TENTANG SIAGAWARGA</span>
          <h1 className="hero-h1">Satu Laporan,<br />Langkah Perubahan.</h1>
          <p className="hero-p">Platform pelaporan permasalahan lingkungan warga berbasis AI — mudah, cepat, dan terpantau sampai tuntas.</p>
          <div className="hero-actions">
            <Link to="/register" className="btn-hero-primary">Coba Sekarang</Link>
            <Link to="/login" className="btn-hero-white">Masuk ke Akun</Link>
          </div>
        </div>
      </section>

      <main>
        <div className="page-container">
          <div className="landing-main-col" style={{ maxWidth: 1100, margin: '0 auto' }}>
            <div>
              <p className="section-eyebrow">KATEGORI LAPORAN</p>
              <h2 className="section-heading">Apa yang bisa Anda laporkan?</h2>
              <div className="categories-grid" style={{ marginBottom: 40 }}>
                {categories.map((cat) => (
                  <div key={cat.name} className="cat-card">
                    <div className="cat-icon-wrap">
                      <img src={cat.icon} alt={cat.name} />
                    </div>
                    <div className="cat-name">{cat.name}</div>
                    <div className="cat-desc">{cat.desc}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="follow-and-map-grid">
              <div className="follow-card">
                <p className="section-eyebrow">ALUR PENANGANAN</p>
                <h3 style={{ fontSize: 20, fontWeight: 800, color: 'var(--dark-title)', marginTop: 8 }}>Pantau laporan Anda</h3>
                <div className="follow-steps-list">
                  {followSteps.map((s, i) => (
                    <div key={i} className="follow-step-item">
                      <div className="follow-step-dot">{s.icon}</div>
                      <div>
                        <div className="follow-step-title">{s.title}</div>
                        <div className="follow-step-sub">{s.sub}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="map-visual-card">
                <p className="section-eyebrow">SEBARAN LAPORAN</p>
                <h3 style={{ fontSize: 20, fontWeight: 800, color: 'var(--dark-title)', marginTop: 8 }}>Peta wilayah aktif</h3>
                <div className="map-img-container" style={{ height: 310 }}>
                  <img src="/assets/peta-ilustratif.png" alt="Peta Ilustratif" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer className="footer-figma">
        <div className="footer-brand">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <img src="/assets/logo-siagawarga.png" alt="Logo" style={{ width: 24, height: 24, objectFit: 'contain' }} />
            <span style={{ fontSize: 18, fontWeight: 800, color: 'var(--dark-title)' }}>SiagaWarga</span>
          </div>
          <p style={{ fontSize: 14, color: 'var(--neutral-muted)' }}>Satu Laporan, Langkah Perubahan.</p>
        </div>
        <div className="footer-nav">
          <a href="#">Syarat Layanan</a>
          <a href="#">Kebijakan Privasi</a>
          <Link to="/login" className="accent">Masuk</Link>
        </div>
      </footer>
    </div>
  )
}
