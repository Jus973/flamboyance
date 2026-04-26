import { Routes, Route, Link, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'

const PRODUCTS = [
  { id: 1, name: 'Wireless Headphones', price: 149.99, image: 'https://picsum.photos/seed/headphones/400/300' },
  { id: 2, name: 'Smart Watch', price: 299.99, image: 'https://picsum.photos/seed/watch/400/300' },
  { id: 3, name: 'Laptop Stand', price: 79.99, image: '/broken-image.jpg' }, // BUG: Broken image
  { id: 4, name: 'USB-C Hub', price: 59.99, image: 'https://picsum.photos/seed/hub/400/300' },
]

function Header({ cartCount }) {
  return (
    <header>
      <h1>TechShop</h1>
      <nav>
        <Link to="/">Home</Link>
        <Link to="/products">Products</Link>
        <Link to="/cart">Cart ({cartCount})</Link>
        {/* BUG: Dead link - goes nowhere */}
        <Link to="/support">Support</Link>
      </nav>
    </header>
  )
}

function Home() {
  return (
    <div className="container">
      <h2>Welcome to TechShop</h2>
      <p>Your one-stop shop for tech accessories.</p>
      
      {/* BUG: Hidden CTA button */}
      <button className="btn btn-primary btn-hidden-cta" style={{ marginTop: '20px' }}>
        Shop Now
      </button>
      
      <div style={{ marginTop: '30px' }}>
        <Link to="/products" className="btn btn-primary">Browse Products</Link>
      </div>
    </div>
  )
}

function Products({ addToCart }) {
  return (
    <div className="container">
      <h2>Our Products</h2>
      <div className="product-grid">
        {PRODUCTS.map(product => (
          <div key={product.id} className="product-card">
            {product.id === 3 ? (
              // BUG: Broken image
              <div className="broken-image">Image not found</div>
            ) : (
              <img src={product.image} alt={product.name} />
            )}
            <h3>{product.name}</h3>
            <div className="price">${product.price}</div>
            <button 
              className="btn btn-primary"
              onClick={() => addToCart(product)}
            >
              Add to Cart
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

function Cart({ cart, removeFromCart }) {
  const total = cart.reduce((sum, item) => sum + item.price * item.quantity, 0)
  const navigate = useNavigate()
  
  if (cart.length === 0) {
    return (
      <div className="container">
        <div className="cart-page">
          <h2>Your Cart</h2>
          <p>Your cart is empty.</p>
          <Link to="/products" className="btn btn-primary" style={{ marginTop: '20px', display: 'inline-block' }}>
            Continue Shopping
          </Link>
        </div>
      </div>
    )
  }
  
  return (
    <div className="container">
      <div className="cart-page">
        <h2>Your Cart</h2>
        {cart.map(item => (
          <div key={item.id} className="cart-item">
            <div>
              <h3>{item.name}</h3>
              <p>Qty: {item.quantity}</p>
            </div>
            <div>
              <span style={{ marginRight: '20px' }}>${(item.price * item.quantity).toFixed(2)}</span>
              {/* BUG: Tiny remove button - hard to tap on mobile */}
              <button 
                className="btn btn-tiny"
                onClick={() => removeFromCart(item.id)}
              >
                ×
              </button>
            </div>
          </div>
        ))}
        <div className="cart-total">
          Total: ${total.toFixed(2)}
        </div>
        <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
          <Link to="/products" className="btn btn-primary">Continue Shopping</Link>
          <button 
            className="btn btn-success"
            onClick={() => navigate('/checkout')}
          >
            Proceed to Checkout
          </button>
        </div>
      </div>
    </div>
  )
}

function Checkout({ cart, clearCart }) {
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [formData, setFormData] = useState({
    email: '',
    name: '',
    address: '',
    city: '',
    zip: '',
    cardNumber: '',
    expiry: '',
    cvv: '',
  })
  const navigate = useNavigate()
  const total = cart.reduce((sum, item) => sum + item.price * item.quantity, 0)

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
    setError('')
  }

  const handleSubmitStep1 = (e) => {
    e.preventDefault()
    if (!formData.email || !formData.name) {
      // BUG: Error message with poor contrast (light red on light pink)
      setError('Please fill in all required fields')
      return
    }
    setStep(2)
  }

  const handleSubmitStep2 = (e) => {
    e.preventDefault()
    if (!formData.address || !formData.city || !formData.zip) {
      setError('Please fill in all shipping fields')
      return
    }
    setStep(3)
  }

  const handleSubmitStep3 = async (e) => {
    e.preventDefault()
    
    // BUG: Form validation that doesn't tell you what's wrong
    if (!formData.cardNumber || !formData.expiry || !formData.cvv) {
      setError('Invalid payment information')
      return
    }

    // BUG: Extremely slow checkout - 5 second delay
    setLoading(true)
    await new Promise(resolve => setTimeout(resolve, 5000))
    
    // BUG: 50% chance of random failure
    if (Math.random() > 0.5) {
      setLoading(false)
      setError('Payment failed. Please try again.')
      return
    }

    setLoading(false)
    clearCart()
    navigate('/confirmation')
  }

  if (cart.length === 0) {
    return (
      <div className="container">
        <div className="checkout-page">
          <h2>Checkout</h2>
          <p>Your cart is empty. Add some items first.</p>
          <Link to="/products" className="btn btn-primary">Browse Products</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="container">
      {loading && (
        <div className="loading-overlay">
          <div className="spinner"></div>
        </div>
      )}
      
      <div className="checkout-page">
        <h2>Checkout</h2>
        
        <div className="checkout-steps">
          <div className={`step ${step >= 1 ? 'active' : ''} ${step > 1 ? 'completed' : ''}`}>
            1. Contact
          </div>
          <div className={`step ${step >= 2 ? 'active' : ''} ${step > 2 ? 'completed' : ''}`}>
            2. Shipping
          </div>
          <div className={`step ${step >= 3 ? 'active' : ''}`}>
            3. Payment
          </div>
        </div>

        {error && <div className="error-message">{error}</div>}

        {step === 1 && (
          <form onSubmit={handleSubmitStep1}>
            <div className="form-group">
              <label>Email *</label>
              <input 
                type="email" 
                name="email" 
                value={formData.email}
                onChange={handleChange}
                placeholder="your@email.com"
              />
            </div>
            <div className="form-group">
              <label>Full Name *</label>
              <input 
                type="text" 
                name="name" 
                value={formData.name}
                onChange={handleChange}
                placeholder="John Doe"
              />
            </div>
            <button type="submit" className="btn btn-primary">Continue to Shipping</button>
          </form>
        )}

        {step === 2 && (
          <form onSubmit={handleSubmitStep2}>
            <div className="form-group">
              <label>Address *</label>
              <input 
                type="text" 
                name="address" 
                value={formData.address}
                onChange={handleChange}
                placeholder="123 Main St"
              />
            </div>
            <div className="form-group">
              <label>City *</label>
              <input 
                type="text" 
                name="city" 
                value={formData.city}
                onChange={handleChange}
                placeholder="San Francisco"
              />
            </div>
            <div className="form-group">
              <label>ZIP Code *</label>
              <input 
                type="text" 
                name="zip" 
                value={formData.zip}
                onChange={handleChange}
                placeholder="94102"
              />
            </div>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button type="button" className="btn" onClick={() => setStep(1)}>Back</button>
              <button type="submit" className="btn btn-primary">Continue to Payment</button>
            </div>
          </form>
        )}

        {step === 3 && (
          <form onSubmit={handleSubmitStep3}>
            <div className="form-group">
              <label>Card Number *</label>
              <input 
                type="text" 
                name="cardNumber" 
                value={formData.cardNumber}
                onChange={handleChange}
                placeholder="4242 4242 4242 4242"
              />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              <div className="form-group">
                <label>Expiry *</label>
                <input 
                  type="text" 
                  name="expiry" 
                  value={formData.expiry}
                  onChange={handleChange}
                  placeholder="MM/YY"
                />
              </div>
              <div className="form-group">
                <label>CVV *</label>
                <input 
                  type="text" 
                  name="cvv" 
                  value={formData.cvv}
                  onChange={handleChange}
                  placeholder="123"
                />
              </div>
            </div>
            
            <div className="cart-total" style={{ marginBottom: '20px' }}>
              Total: ${total.toFixed(2)}
            </div>
            
            <div style={{ display: 'flex', gap: '10px' }}>
              <button type="button" className="btn" onClick={() => setStep(2)}>Back</button>
              {/* BUG: Submit button that sometimes doesn't work */}
              <button 
                type="submit" 
                className="btn btn-success"
                id="submit-order"
              >
                Place Order
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}

function Confirmation() {
  return (
    <div className="container">
      <div className="checkout-page" style={{ textAlign: 'center' }}>
        <h2>🎉 Order Confirmed!</h2>
        <p style={{ fontSize: '18px', margin: '20px 0' }}>
          Thank you for your purchase. You will receive a confirmation email shortly.
        </p>
        <Link to="/" className="btn btn-primary">Continue Shopping</Link>
      </div>
    </div>
  )
}

function Support() {
  // BUG: Dead end - no actual support content, just a broken page
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    // Simulate loading that never completes properly
    const timer = setTimeout(() => {
      setLoading(false)
    }, 3000)
    return () => clearTimeout(timer)
  }, [])

  if (loading) {
    return (
      <div className="container">
        <div className="loading-overlay" style={{ position: 'relative', height: '300px' }}>
          <div className="spinner"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="container">
      <div className="checkout-page">
        <h2>Support</h2>
        {/* BUG: No actual support options, dead end */}
        <p>Our support team is currently unavailable.</p>
        <p style={{ color: '#999', marginTop: '20px' }}>
          Please try again later or email us at{' '}
          {/* BUG: Sneaky link that looks like text */}
          <span className="sneaky-link">support@techshop.fake</span>
        </p>
      </div>
    </div>
  )
}

function NotFound() {
  return (
    <div className="container">
      <div className="checkout-page" style={{ textAlign: 'center' }}>
        <h2>404 - Page Not Found</h2>
        <p>The page you're looking for doesn't exist.</p>
        <Link to="/" className="btn btn-primary" style={{ marginTop: '20px', display: 'inline-block' }}>
          Go Home
        </Link>
      </div>
    </div>
  )
}

export default function App() {
  const [cart, setCart] = useState([])

  const addToCart = (product) => {
    setCart(prev => {
      const existing = prev.find(item => item.id === product.id)
      if (existing) {
        return prev.map(item => 
          item.id === product.id 
            ? { ...item, quantity: item.quantity + 1 }
            : item
        )
      }
      return [...prev, { ...product, quantity: 1 }]
    })
  }

  const removeFromCart = (productId) => {
    setCart(prev => prev.filter(item => item.id !== productId))
  }

  const clearCart = () => {
    setCart([])
  }

  const cartCount = cart.reduce((sum, item) => sum + item.quantity, 0)

  return (
    <>
      <Header cartCount={cartCount} />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/products" element={<Products addToCart={addToCart} />} />
        <Route path="/cart" element={<Cart cart={cart} removeFromCart={removeFromCart} />} />
        <Route path="/checkout" element={<Checkout cart={cart} clearCart={clearCart} />} />
        <Route path="/confirmation" element={<Confirmation />} />
        <Route path="/support" element={<Support />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
      <footer>
        <p>© 2024 TechShop - A buggy demo store</p>
      </footer>
    </>
  )
}
