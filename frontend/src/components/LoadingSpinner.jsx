import React from 'react'

export function LoadingSpinner({ size = 32, message = 'Memuat data...', fullPage = false }) {
  const content = (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: fullPage ? '80px 20px' : '40px 20px',
      gap: 14,
      color: '#64748b',
      fontSize: 14,
      fontWeight: 500,
    }}>
      <div
        style={{
          width: size,
          height: size,
          border: '3px solid #e2e8f0',
          borderTopColor: '#0d9488',
          borderRadius: '50%',
          animation: 'sw-spin 0.8s linear infinite',
        }}
      />
      {message && <span>{message}</span>}
      <style>{`
        @keyframes sw-spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )

  if (fullPage) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: '100%',
        minHeight: '50vh',
      }}>
        {content}
      </div>
    )
  }

  return content
}

export function SkeletonBox({ width = '100%', height = 20, borderRadius = 8, style = {} }) {
  return (
    <div
      style={{
        width,
        height,
        borderRadius,
        backgroundColor: '#e2e8f0',
        animation: 'sw-pulse 1.5s ease-in-out infinite',
        ...style,
      }}
    >
      <style>{`
        @keyframes sw-pulse {
          0%, 100% { opacity: 0.6; }
          50% { opacity: 0.25; }
        }
      `}</style>
    </div>
  )
}
