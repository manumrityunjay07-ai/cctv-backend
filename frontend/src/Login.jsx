import { useState } from 'react'
import { GoogleLogin } from '@react-oauth/google'
import { jwtDecode } from 'jwt-decode'
import './Login.css'

export default function Login({ onLogin }) {
  const [error, setError] = useState(null)

  const handleSuccess = (credentialResponse) => {
    try {
      const decoded = jwtDecode(credentialResponse.credential)
      onLogin({ 
        username: decoded.name || decoded.email, 
        role: 'Verified User', 
        avatar: decoded.name ? decoded.name.charAt(0).toUpperCase() : 'G'
      })
    } catch (err) {
      console.error('Token decode failed', err)
      setError('Failed to log in.')
    }
  }

  return (
    <div className="login-page">
      {/* Animated background orbs */}
      <div className="orb orb-1" />
      <div className="orb orb-2" />
      <div className="orb orb-3" />

      <div className="login-card">
        {/* Logo / Brand */}
        <div className="login-brand">
          <div className="login-logo">
            <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="20" cy="20" r="18" stroke="url(#grad)" strokeWidth="2"/>
              <circle cx="20" cy="20" r="8" fill="url(#grad)" opacity="0.8"/>
              <circle cx="20" cy="20" r="3" fill="white"/>
              <line x1="20" y1="2" x2="20" y2="8" stroke="url(#grad)" strokeWidth="2" strokeLinecap="round"/>
              <line x1="20" y1="32" x2="20" y2="38" stroke="url(#grad)" strokeWidth="2" strokeLinecap="round"/>
              <line x1="2" y1="20" x2="8" y2="20" stroke="url(#grad)" strokeWidth="2" strokeLinecap="round"/>
              <line x1="32" y1="20" x2="38" y2="20" stroke="url(#grad)" strokeWidth="2" strokeLinecap="round"/>
              <defs>
                <linearGradient id="grad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#38bdf8"/>
                  <stop offset="1" stopColor="#818cf8"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
          <h1 className="login-title">VisionAI<span>CCTV</span></h1>
          <p className="login-subtitle">Natural Language Video Intelligence</p>
        </div>

        {/* Real Google Login Button */}
        <div className="google-login-container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
          <GoogleLogin
            onSuccess={handleSuccess}
            onError={() => {
              console.log('Login Failed')
              setError('Google login failed.')
            }}
            useOneTap
            shape="rectangular"
            theme="filled_blue"
            size="large"
            text="signin_with"
          />
          {error && <div className="login-error" style={{marginTop: '10px'}}>{error}</div>}
        </div>
      </div>
    </div>
  )
}
