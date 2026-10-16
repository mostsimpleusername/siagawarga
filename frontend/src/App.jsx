import { Routes, Route, Navigate } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import BerandaPage from './pages/BerandaPage'
import BuatLaporanPage from './pages/BuatLaporanPage'
import LaporanSayaPage from './pages/LaporanSayaPage'
import DetailLaporanPage from './pages/DetailLaporanPage'
import PetaPage from './pages/PetaPage'
import ProfilPage from './pages/ProfilPage'
import DashboardPetugasPage from './pages/DashboardPetugasPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/beranda" element={<BerandaPage />} />
      <Route path="/buat-laporan" element={<BuatLaporanPage />} />
      <Route path="/laporan-saya" element={<LaporanSayaPage />} />
      <Route path="/detail-laporan" element={<DetailLaporanPage />} />
      <Route path="/peta" element={<PetaPage />} />

      <Route path="/profil" element={<ProfilPage />} />
      <Route path="/me" element={<Navigate to="/profil" replace />} />
      <Route path="/dashboard" element={<Navigate to="/dashboard-petugas" replace />} />
      <Route path="/dashboard-petugas" element={<DashboardPetugasPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>

  )
}
