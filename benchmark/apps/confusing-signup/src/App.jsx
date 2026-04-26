import { Routes, Route, Link, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'

function SignupForm() {
  const [step, setStep] = useState(1)
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: '',
    phone: '',
    country: '',
    agreeTerms: false,
    agreeMarketing: false,
    captcha: '',
  })
  const [errors, setErrors] = useState({})
  const [showPasswordReqs, setShowPasswordReqs] = useState(false)
  const [loading, setLoading] = useState(false)
  const [showModal, setShowModal] = useState(false)
  const navigate = useNavigate()

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
    // Clear error when user types
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }))
    }
  }

  const validateStep1 = () => {
    const newErrors = {}
    
    if (!formData.email) {
      newErrors.email = 'Email is required'
    } else if (!formData.email.includes('@')) {
      newErrors.email = 'Invalid email format'
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required'
    } else if (formData.password.length < 8) {
      // BUG: Show requirements AFTER error, not before
      setShowPasswordReqs(true)
      newErrors.password = 'Password does not meet requirements'
    }
    
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const validateStep2 = () => {
    const newErrors = {}
    
    if (!formData.firstName) {
      newErrors.firstName = 'First name is required'
    }
    
    if (!formData.lastName) {
      newErrors.lastName = 'Last name is required'
    }
    
    // BUG: Phone validation is overly strict and unclear
    if (formData.phone && !/^\+\d{1,3}\s?\d{10}$/.test(formData.phone)) {
      newErrors.phone = 'Invalid phone number'
    }
    
    if (!formData.country) {
      newErrors.country = 'Please select a country'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const validateStep3 = () => {
    const newErrors = {}
    
    if (!formData.agreeTerms) {
      newErrors.agreeTerms = 'You must agree to the terms'
    }
    
    // BUG: Captcha is impossible - the "correct" answer changes
    const correctCaptcha = 'XK7M9P' // But displayed text is distorted
    if (formData.captcha.toUpperCase() !== correctCaptcha) {
      newErrors.captcha = 'Incorrect captcha'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleNext = () => {
    if (step === 1 && validateStep1()) {
      setStep(2)
    } else if (step === 2 && validateStep2()) {
      setStep(3)
    }
  }

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!validateStep3()) {
      return
    }
    
    setLoading(true)
    
    // BUG: Simulate slow submission
    await new Promise(resolve => setTimeout(resolve, 4000))
    
    // BUG: Random failure with unhelpful message
    if (Math.random() > 0.3) {
      setLoading(false)
      setShowModal(true) // Show uncloseable modal
      return
    }
    
    setLoading(false)
    navigate('/success')
  }

  const handleSocialLogin = (provider) => {
    // BUG: Social login just shows an error
    alert(`${provider} login is temporarily unavailable. Please use email signup.`)
  }

  return (
    <div className="container">
      <div className="card">
        <h1>Create Account</h1>
        <p className="subtitle">Join thousands of happy users</p>
        
        <div className="progress-bar">
          <div className={`step-indicator ${step >= 1 ? 'active' : ''} ${step > 1 ? 'completed' : ''}`}>1</div>
          <div className={`step-indicator ${step >= 2 ? 'active' : ''} ${step > 2 ? 'completed' : ''}`}>2</div>
          <div className={`step-indicator ${step >= 3 ? 'active' : ''}`}>3</div>
        </div>

        <form onSubmit={handleSubmit}>
          {step === 1 && (
            <>
              <div className="form-group">
                <label>
                  Email <span className="required">(required)</span>
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className={errors.email ? 'error' : ''}
                  placeholder="you@example.com"
                />
                {errors.email && <div className="error-text">{errors.email}</div>}
              </div>
              
              <div className="form-group">
                <label>
                  Password <span className="required">(required)</span>
                </label>
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  className={errors.password ? 'error' : ''}
                  placeholder="••••••••"
                />
                {errors.password && <div className="error-text">{errors.password}</div>}
                {/* BUG: Requirements only shown after error */}
                {showPasswordReqs && (
                  <div className="password-requirements visible">
                    Password must be at least 8 characters with 1 uppercase, 
                    1 lowercase, 1 number, and 1 special character.
                  </div>
                )}
              </div>
              
              <div className="form-group">
                <label>
                  Confirm Password <span className="required">(required)</span>
                </label>
                <input
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  className={errors.confirmPassword ? 'error' : ''}
                  placeholder="••••••••"
                />
                {errors.confirmPassword && <div className="error-text">{errors.confirmPassword}</div>}
              </div>
              
              <button type="button" className="btn btn-primary" onClick={handleNext}>
                Continue
              </button>
            </>
          )}

          {step === 2 && (
            <>
              <div className="form-group">
                <label>
                  First Name <span className="required">(required)</span>
                </label>
                <input
                  type="text"
                  name="firstName"
                  value={formData.firstName}
                  onChange={handleChange}
                  className={errors.firstName ? 'error' : ''}
                  placeholder="John"
                />
                {errors.firstName && <div className="error-text">{errors.firstName}</div>}
              </div>
              
              <div className="form-group">
                <label>
                  Last Name <span className="required">(required)</span>
                </label>
                <input
                  type="text"
                  name="lastName"
                  value={formData.lastName}
                  onChange={handleChange}
                  className={errors.lastName ? 'error' : ''}
                  placeholder="Doe"
                />
                {errors.lastName && <div className="error-text">{errors.lastName}</div>}
              </div>
              
              <div className="form-group">
                <label>Phone Number (optional)</label>
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  className={errors.phone ? 'error' : ''}
                  placeholder="Phone number"
                />
                {/* BUG: No hint about required format */}
                {errors.phone && <div className="error-text">{errors.phone}</div>}
              </div>
              
              <div className="form-group">
                <label>
                  Country <span className="required">(required)</span>
                </label>
                <select
                  name="country"
                  value={formData.country}
                  onChange={handleChange}
                  className={errors.country ? 'error' : ''}
                >
                  <option value="">Select a country</option>
                  {/* BUG: List is not alphabetized, hard to find countries */}
                  <option value="US">United States</option>
                  <option value="ZW">Zimbabwe</option>
                  <option value="CA">Canada</option>
                  <option value="MX">Mexico</option>
                  <option value="UK">United Kingdom</option>
                  <option value="AU">Australia</option>
                  <option value="DE">Germany</option>
                  <option value="FR">France</option>
                  <option value="JP">Japan</option>
                  <option value="BR">Brazil</option>
                </select>
                {errors.country && <div className="error-text">{errors.country}</div>}
              </div>
              
              <div className="btn-row">
                <button type="button" className="btn btn-secondary" onClick={handleBack}>
                  Back
                </button>
                <button type="button" className="btn btn-primary" onClick={handleNext}>
                  Continue
                </button>
              </div>
            </>
          )}

          {step === 3 && (
            <>
              {/* BUG: Impossible captcha */}
              <div className="captcha-box">
                <div className="captcha-image">XK7M9P</div>
                <input
                  type="text"
                  name="captcha"
                  value={formData.captcha}
                  onChange={handleChange}
                  placeholder="Enter the text above"
                  style={{ marginTop: '10px' }}
                />
                {errors.captcha && <div className="error-text">{errors.captcha}</div>}
              </div>
              
              <div className="checkbox-group">
                <input
                  type="checkbox"
                  name="agreeTerms"
                  checked={formData.agreeTerms}
                  onChange={handleChange}
                  id="agreeTerms"
                />
                <label htmlFor="agreeTerms">
                  I agree to the{' '}
                  {/* BUG: Link looks like disabled text */}
                  <a href="/terms" className="terms-link">Terms of Service</a>
                  {' '}and{' '}
                  <a href="/privacy" className="terms-link">Privacy Policy</a>
                </label>
              </div>
              {errors.agreeTerms && <div className="error-text">{errors.agreeTerms}</div>}
              
              <div className="checkbox-group">
                <input
                  type="checkbox"
                  name="agreeMarketing"
                  checked={formData.agreeMarketing}
                  onChange={handleChange}
                  id="agreeMarketing"
                />
                <label htmlFor="agreeMarketing">
                  Send me marketing emails (optional)
                </label>
              </div>
              
              <div className="btn-row">
                <button type="button" className="btn btn-secondary" onClick={handleBack}>
                  Back
                </button>
                {/* BUG: Button looks enabled when disabled */}
                <button 
                  type="submit" 
                  className="btn btn-primary"
                  disabled={loading}
                >
                  {loading ? 'Creating Account...' : 'Create Account'}
                </button>
              </div>
            </>
          )}
        </form>

        <div className="social-login">
          <p>Or sign up with</p>
          <div className="social-buttons">
            {/* BUG: Social login doesn't work */}
            <button 
              type="button" 
              className="social-btn"
              onClick={() => handleSocialLogin('Google')}
            >
              Google
            </button>
            <button 
              type="button" 
              className="social-btn"
              onClick={() => handleSocialLogin('Facebook')}
            >
              Facebook
            </button>
          </div>
        </div>
      </div>

      {/* BUG: Modal that can't be closed */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal" style={{ position: 'relative' }}>
            <button className="modal-close">×</button>
            <h2>Oops!</h2>
            <p>Something went wrong. Please try again later.</p>
            {/* No working close button or way to dismiss */}
          </div>
        </div>
      )}
    </div>
  )
}

function Success() {
  return (
    <div className="container">
      <div className="card success-page">
        <div className="success-icon">🎉</div>
        <h1>Welcome!</h1>
        <p>Your account has been created successfully.</p>
        <p className="success-text">Check your email for verification.</p>
        <Link to="/" className="login-link">Back to signup</Link>
      </div>
    </div>
  )
}

function Terms() {
  // BUG: Dead end - no actual terms content
  return (
    <div className="container">
      <div className="card">
        <h1>Terms of Service</h1>
        <div className="loading-spinner"></div>
        <p style={{ textAlign: 'center', color: '#999', marginTop: '20px' }}>
          Loading terms...
        </p>
        {/* Content never loads - dead end */}
      </div>
    </div>
  )
}

function Privacy() {
  // BUG: Dead end - no actual privacy content
  return (
    <div className="container">
      <div className="card">
        <h1>Privacy Policy</h1>
        <div className="loading-spinner"></div>
        <p style={{ textAlign: 'center', color: '#999', marginTop: '20px' }}>
          Loading privacy policy...
        </p>
        {/* Content never loads - dead end */}
      </div>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<SignupForm />} />
      <Route path="/success" element={<Success />} />
      <Route path="/terms" element={<Terms />} />
      <Route path="/privacy" element={<Privacy />} />
    </Routes>
  )
}
