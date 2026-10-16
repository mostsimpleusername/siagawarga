import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Home, FileText, Map, LogOut, LayoutDashboard, User } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function Sidebar({ role: propRole }) {
  const location = useLocation()
  const navigate = useNavigate()
  const { userRole, isOfficer: authIsOfficer, logout } = useAuth()

  // Prioritaskan context/localStorage agar tidak pernah flash default 'warga'
  const storedRole = (localStorage.getItem('siagawarga_role') || userRole || '').toUpperCase()
  const isOfficer = propRole === 'petugas' || authIsOfficer || storedRole === 'PETUGAS' || storedRole === 'ADMIN'
  const activeRole = isOfficer ? 'petugas' : 'warga'

  function handleLogout() {
    logout()
    navigate('/login')
  }

  const menuItems = isOfficer
    ? [
        { to: '/dashboard-petugas', icon: <LayoutDashboard size={20} />, label: 'Dashboard' },
        { to: '/peta', icon: <Map size={20} />, label: 'Peta Laporan' },
        { to: '/profil', icon: <User size={20} />, label: 'Profil' },
      ]
    : [
        { to: '/beranda', icon: <Home size={20} />, label: 'Beranda' },
        { to: '/buat-laporan', icon: <FileText size={20} />, label: 'Laporan' },
        { to: '/peta', icon: <Map size={20} />, label: 'Peta Laporan' },
        { to: '/profil', icon: <User size={20} />, label: 'Profil' },
      ]


  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="app-sidebar">
        <div>
          <div className="sidebar-header">
            <Link to="/" className="sidebar-brand">
              <img src="/assets/logo-siagawarga.png" alt="SiagaWarga" />
              <span className="sidebar-brand-name">SiagaWarga</span>
            </Link>
          </div>
          <ul className="sidebar-menu">
            {menuItems.map((item) => (
              <li key={item.to} className="sidebar-menu-item">
                <Link
                  to={item.to}
                  className={location.pathname === item.to ? 'active' : ''}
                >
                  {item.icon}
                  <span>{item.label}</span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
        <div className="sidebar-footer">
          <button onClick={handleLogout} className="sidebar-logout-btn">
            <LogOut size={20} />
            <span>Keluar</span>
          </button>
        </div>
      </aside>

      {/* Mobile Bottom Navigation Bar (Figma Mobile App Spec) */}
      <nav className="mobile-bottom-nav">
        {menuItems.map((item) => {
          const isActive = location.pathname === item.to
          return (
            <Link
              key={item.to}
              to={item.to}
              className={`mobile-nav-item ${isActive ? 'active' : ''}`}
            >
              <div className="mobile-nav-icon-wrap">
                {item.icon}
              </div>
              <span className="mobile-nav-label">{item.label}</span>
            </Link>
          )
        })}
      </nav>
    </>
  )
}
