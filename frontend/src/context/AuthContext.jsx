import React, { createContext, useContext, useState, useEffect } from 'react'
import { API_BASE } from '../config'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('siagawarga_token') || null)
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('siagawarga_user')
      if (saved) {
        const parsed = JSON.parse(saved)
        if (parsed?.peran && !localStorage.getItem('siagawarga_role')) {
          localStorage.setItem('siagawarga_role', String(parsed.peran).toUpperCase())
        }
        if (parsed?.nama && !localStorage.getItem('siagawarga_initials')) {
          const inits = parsed.nama.trim().split(' ').filter(Boolean).slice(0, 2).map(w => w[0]).join('').toUpperCase()
          localStorage.setItem('siagawarga_initials', inits)
        }
        return parsed
      }
      return null
    } catch {
      return null
    }
  })
  const [loading, setLoading] = useState(!user && !!token)

  useEffect(() => {
    let isMounted = true

    async function fetchMe() {
      if (!token) {
        setUser(null)
        setLoading(false)
        return
      }

      try {
        const res = await fetch(`${API_BASE}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (res.ok) {
          const data = await res.json()
          if (isMounted) {
            setUser(data)
            localStorage.setItem('siagawarga_user', JSON.stringify(data))
            if (data.peran) {
              localStorage.setItem('siagawarga_role', String(data.peran).toUpperCase())
            }
            if (data.nama) {
              const inits = data.nama.trim().split(' ').filter(Boolean).slice(0, 2).map(w => w[0]).join('').toUpperCase()
              localStorage.setItem('siagawarga_initials', inits)
            }
          }
        } else if (res.status === 401) {
          if (isMounted) {
            setUser(null)
            setToken(null)
            localStorage.removeItem('siagawarga_token')
            localStorage.removeItem('siagawarga_user')
            localStorage.removeItem('siagawarga_role')
            localStorage.removeItem('siagawarga_initials')
          }
        }
      } catch (err) {
        console.error('Auth check error:', err)
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    fetchMe()

    return () => {
      isMounted = false
    }
  }, [token])

  function login(accessToken, userData = null) {
    localStorage.setItem('siagawarga_token', accessToken)
    setToken(accessToken)
    if (userData) {
      localStorage.setItem('siagawarga_user', JSON.stringify(userData))
      setUser(userData)
      if (userData.peran) {
        localStorage.setItem('siagawarga_role', String(userData.peran).toUpperCase())
      }
      if (userData.nama) {
        const inits = userData.nama.trim().split(' ').filter(Boolean).slice(0, 2).map(w => w[0]).join('').toUpperCase()
        localStorage.setItem('siagawarga_initials', inits)
      }
    }
  }

  function logout() {
    localStorage.removeItem('siagawarga_token')
    localStorage.removeItem('siagawarga_user')
    localStorage.removeItem('siagawarga_role')
    localStorage.removeItem('siagawarga_initials')
    setToken(null)
    setUser(null)
  }

  const storedRole = localStorage.getItem('siagawarga_role')
  const userRole = (user?.peran || storedRole || 'WARGA').toUpperCase()
  const isOfficer = userRole === 'PETUGAS' || userRole === 'ADMIN'

  const userInitials = user?.nama
    ? user.nama.trim().split(' ').filter(Boolean).slice(0, 2).map(w => w[0]).join('').toUpperCase()
    : (localStorage.getItem('siagawarga_initials') || (isOfficer ? 'PT' : 'SW'))

  return (
    <AuthContext.Provider value={{ token, user, userInitials, userRole, isOfficer, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return ctx
}

