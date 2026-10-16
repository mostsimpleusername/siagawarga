import { Link } from 'react-router-dom'
import { Bell } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function Topbar({ roleLabel, userInitials: propInitials, avatarBg }) {
  const { userInitials: contextInitials, userRole, isOfficer: authIsOfficer } = useAuth()
  
  const storedRole = (localStorage.getItem('siagawarga_role') || userRole || '').toUpperCase()
  const isPetugas = authIsOfficer || storedRole === 'PETUGAS' || storedRole === 'ADMIN'
  const displayLabel = roleLabel || (isPetugas ? 'Dashboard Petugas' : 'Layanan Warga')
  const storedInitials = localStorage.getItem('siagawarga_initials')
  const defaultInitials = isPetugas ? 'PT' : 'SW'
  const displayInitials = propInitials || contextInitials || storedInitials || defaultInitials
  const defaultBg = isPetugas ? '#1e3a5f' : '#e8f6f4'
  const defaultTextColor = isPetugas ? '#ffffff' : '#0c504c'


  return (
    <header className="app-topbar">
      <div className="topbar-left">
        <Link to="/" className="topbar-mobile-brand">
          <img src="/assets/logo-siagawarga.png" alt="SiagaWarga" />
          <span className="topbar-mobile-name">SiagaWarga</span>
        </Link>
        <div className="topbar-role-label">{displayLabel}</div>
      </div>
      <div className="topbar-actions">
        <button className="topbar-bell-btn" title="Notifikasi">
          <Bell size={20} fill="currentColor" />
        </button>
        <Link to="/profil" style={{ textDecoration: 'none' }}>
          <div
            className="user-avatar-circle"
            style={{
              backgroundColor: avatarBg || defaultBg,
              color: isPetugas ? '#ffffff' : defaultTextColor,
            }}
            title="Profil Pengguna"
          >
            {displayInitials}
          </div>
        </Link>
      </div>
    </header>
  )
}
