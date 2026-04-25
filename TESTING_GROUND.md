# Flamboyance Testing Ground

A specification for a **deliberately broken web application** designed to fully exercise Flamboyance's UX friction detection capabilities.

---

## Overview

This document describes an ideal test app—a mock e-commerce site called **"BrokenMart"**—with intentionally poor UX patterns that trigger every frustration event Flamboyance can detect.

**Stack recommendation:** React + Vite (or plain HTML/JS) with TailwindCSS for quick styling.

---

## Page Structure

```
/                   → Home (hero, featured products, promos)
/products           → Product listing (grid with filters)
/products/:id       → Product detail page
/cart               → Shopping cart
/checkout           → Checkout flow (multi-step)
/checkout/confirm   → Order confirmation
/account            → Account settings (login required)
/search             → Search results page
/help               → Help/FAQ page
```

---

## Frustration Events to Trigger

### Notice Tier (Passive UX Friction)

| Event | Implementation |
|-------|----------------|
| **slow_load** | Add artificial `setTimeout(3500)` before rendering `/products` page |
| **dead_end** | Create `/help/empty` page with only static text, no links or buttons |
| **long_dwell** | `/products/:id` has confusing layout requiring 10+ seconds to find "Add to Cart" |
| **rage_decoy** | Non-button `<div>` elements styled like buttons with `cursor: pointer` and hover effects |
| **js_error** | Throw `TypeError: Cannot read property 'price' of undefined` on `/products/999` |
| **broken_image** | Product images with invalid `src="/images/missing-product.jpg"` |
| **network_error** | `/api/recommendations` returns 500; `/api/inventory` returns 404 |
| **error_message_visible** | Show red error banners: "Something went wrong", "Failed to load" |
| **accessibility_failure** | Images without `alt`, inputs without `<label>`, icon-only buttons |
| **mobile_tap_target** | Tiny 24x24px buttons, links with 8px font size |
| **confusing_navigation** | 6-level deep breadcrumbs, unclear CTA labels like "Go" or "Click Here" |
| **modal_frustration** | Auto-popup newsletter modal on page load, tiny X button to close |
| **copy_paste_failure** | `user-select: none` on product descriptions and prices |
| **infinite_scroll_trap** | Product listing that loads forever, footer never reachable |

### Frustration Tier (Active User Struggle)

| Event | Implementation |
|-------|----------------|
| **circular_navigation** | "Back to Products" link on detail page goes to home, home links back to detail |
| **rage_click** | Fake "Add to Cart" button that does nothing (no event handler) |
| **scroll_rage** | Important content hidden below fold with no visual indicator to scroll |
| **form_abandonment** | Long checkout form that clears on any navigation |
| **session_timeout** | Show "Session expired" modal after 30 seconds of inactivity |
| **slow_interaction** | "Submit Order" button takes 4 seconds to respond |
| **search_frustration** | Search returns "0 results" for common terms, no suggestions |
| **cart_abandonment** | Cart page with confusing "Continue Shopping" as primary CTA |
| **back_button_abuse** | Multi-step checkout that breaks on browser back button |
| **unmet_goal** | Checkout flow that fails silently on final step |

---

## Detailed Page Specifications

### Home Page (`/`)

```html
<!-- Rage decoy: looks like a button but isn't -->
<div class="fake-button" style="cursor: pointer; padding: 12px 24px; 
     background: #3b82f6; color: white; border-radius: 8px;">
  Shop Now
</div>

<!-- Intrusive modal on load -->
<div id="newsletter-modal" class="fixed inset-0 bg-black/50 z-50">
  <div class="modal-content">
    <button class="close-btn" style="width: 16px; height: 16px; font-size: 8px;">×</button>
    <h2>Subscribe to our newsletter!</h2>
    <!-- No way to dismiss by clicking outside -->
  </div>
</div>

<!-- Broken image -->
<img src="/images/hero-banner-TYPO.jpg" alt="">  <!-- Missing alt AND broken src -->

<!-- Confusing navigation -->
<nav>
  <a href="/products">Stuff</a>
  <a href="/account">Things</a>
  <a href="/help">???</a>
</nav>
```

### Product Listing (`/products`)

```javascript
// Artificial slow load
useEffect(() => {
  setTimeout(() => {
    setProducts(data);
    setLoading(false);
  }, 4000); // Triggers slow_load event
}, []);

// Infinite scroll trap - never stops loading
const loadMore = () => {
  setPage(page + 1);
  // Footer is pushed down infinitely
};
```

```html
<!-- Tiny tap targets -->
<button class="filter-btn" style="width: 20px; height: 20px; font-size: 10px;">
  <svg><!-- filter icon --></svg>
</button>

<!-- Copy-paste blocked -->
<p class="product-price" style="user-select: none;">$99.99</p>

<!-- Missing labels -->
<input type="text" placeholder="Search..." id="search">  <!-- No <label for="search"> -->
```

### Product Detail (`/products/:id`)

```javascript
// JS error on invalid product
const product = products.find(p => p.id === id);
console.log(product.price); // TypeError when product is undefined

// Network error
fetch('/api/recommendations')
  .then(res => {
    if (!res.ok) throw new Error('500 Internal Server Error');
  });
```

```html
<!-- Rage decoy - styled div, not a button -->
<div class="add-to-cart-decoy" onclick="">
  Add to Cart
</div>

<!-- Real button hidden below fold with no scroll indicator -->
<div style="margin-top: 2000px;">
  <button id="real-add-to-cart">Add to Cart</button>
</div>

<!-- Accessibility failures -->
<img src="/product.jpg">  <!-- No alt text -->
<button><svg><!-- heart icon --></svg></button>  <!-- No accessible name -->

<!-- Circular navigation -->
<a href="/">← Back to Products</a>  <!-- Actually goes to home, not /products -->
```

### Cart (`/cart`)

```html
<!-- Confusing CTAs -->
<button class="primary-btn">Continue Shopping</button>  <!-- Looks like main action -->
<a href="/checkout" class="text-sm text-gray-500">proceed to checkout →</a>  <!-- Tiny, hard to find -->

<!-- Error message visible -->
<div class="error-banner" style="background: #fee; color: #c00; padding: 16px;">
  ⚠️ Some items in your cart may be out of stock
</div>

<!-- Cart abandonment trigger: no clear path to checkout -->
```

### Checkout (`/checkout`)

```javascript
// Session timeout
useEffect(() => {
  const timer = setTimeout(() => {
    setShowSessionExpired(true);
  }, 30000);
  return () => clearTimeout(timer);
}, []);

// Slow interaction
const handleSubmit = async () => {
  await new Promise(resolve => setTimeout(resolve, 4000)); // 4 second delay
  // Then fail silently
};

// Form abandonment - clear on navigation
useEffect(() => {
  return () => {
    // Form data lost on unmount
  };
}, []);
```

```html
<!-- Multi-step form that breaks on back button -->
<form id="checkout-form">
  <!-- Step 1: Shipping -->
  <!-- Step 2: Payment -->
  <!-- Step 3: Review -->
  <!-- Browser back resets everything -->
</form>

<!-- Unlabeled inputs -->
<input type="text" name="cc" placeholder="Card Number">
<input type="text" name="exp">  <!-- No placeholder, no label -->
<input type="text" name="cvv">

<!-- Tiny submit button -->
<button type="submit" style="padding: 4px 8px; font-size: 10px;">
  Place Order
</button>
```

### Search (`/search`)

```javascript
// Search frustration
const handleSearch = (query) => {
  // Returns empty for everything except exact matches
  if (query !== "Widget Pro X-2000") {
    setResults([]);
    setMessage("No results found"); // No suggestions, no "did you mean?"
  }
};
```

```html
<!-- No search feedback -->
<div class="search-results">
  <p>0 results for "laptop"</p>
  <!-- No suggestions, no filters, no help -->
</div>
```

### Help Page (`/help`)

```html
<!-- Dead end page -->
<div class="help-content">
  <h1>Help & FAQ</h1>
  <p>For assistance, please contact support.</p>
  <!-- No links, no buttons, no way forward -->
</div>
```

### Account (`/account`)

```html
<!-- Deep breadcrumbs -->
<nav class="breadcrumbs">
  Home > Account > Settings > Preferences > Notifications > Email > Frequency
</nav>

<!-- Horizontal scroll on mobile -->
<div style="width: 1200px; overflow-x: visible;">
  <!-- Content wider than viewport -->
</div>
```

---

## API Endpoints (Mock Failures)

| Endpoint | Behavior |
|----------|----------|
| `GET /api/products` | Works, but slow (2s delay) |
| `GET /api/products/999` | Returns 404 |
| `GET /api/recommendations` | Returns 500 Internal Server Error |
| `GET /api/inventory` | Returns 404 Not Found |
| `POST /api/checkout` | Returns 200 but silently fails (no order created) |
| `GET /api/user/session` | Returns 401 after 30 seconds |

---

## CSS for Rage Decoys

```css
/* Elements that LOOK clickable but aren't */
.fake-button,
.decoy-link,
.clickable-looking {
  cursor: pointer;
  transition: all 0.2s;
}

.fake-button:hover {
  background: #2563eb;
  transform: scale(1.02);
}

/* But they have no role="button", no onclick, no href */

/* Copy-paste blocking */
.no-select {
  user-select: none;
  -webkit-user-select: none;
}

/* Tiny tap targets */
.tiny-btn {
  width: 24px;
  height: 24px;
  padding: 2px;
  font-size: 8px;
}
```

---

## Test Scenarios by Persona

| Persona | Expected Triggers |
|---------|-------------------|
| **frustrated_exec** | slow_load, rage_click, unmet_goal (gives up early) |
| **non_tech_senior** | rage_decoy, confusing_navigation, accessibility_failure |
| **power_user** | dead_end, js_error, network_error (explores edge cases) |
| **casual_browser** | modal_frustration, infinite_scroll_trap |
| **anxious_newbie** | form_abandonment, session_timeout, unmet_goal |
| **methodical_tester** | ALL events (systematic exploration) |
| **mobile_commuter** | mobile_tap_target, horizontal_scroll, slow_load |
| **accessibility_user** | accessibility_failure, missing labels, icon-only buttons |

---

## Mutation Testing Compatibility

The app should use standard selectors that work with Flamboyance's mutation scenarios:

```html
<!-- For broken_checkout mutation -->
<button id="checkout-btn">Checkout</button>
<button class="checkout-button">Proceed</button>
<button data-testid="checkout">Complete Order</button>

<!-- For no_nav mutation -->
<nav class="main-nav">...</nav>
<div id="navigation">...</div>
<nav class="navbar">...</nav>

<!-- For slow_submit mutation -->
<button type="submit">Submit</button>
<button class="submit-btn">Send</button>

<!-- For hidden_cta mutation -->
<button class="cta">Sign Up</button>
<div class="call-to-action">Get Started</div>
<button class="primary-button">Buy Now</button>
```

---

## Quick Start Template

```bash
# Create the test app
npm create vite@latest brokenmart -- --template react-ts
cd brokenmart
npm install

# Add intentional bugs as described above
# Run on port 5173 (Vite default)
npm run dev

# Test with Flamboyance
python -m agents.runner_local --url http://localhost:5173 --full --no-headless
```

---

## Verification Checklist

Run Flamboyance and verify these events appear in reports:

- [ ] `slow_load` on `/products`
- [ ] `dead_end` on `/help/empty`
- [ ] `rage_decoy` on home page fake buttons
- [ ] `js_error` on `/products/999`
- [ ] `broken_image` on home page hero
- [ ] `network_error` from `/api/recommendations`
- [ ] `accessibility_failure` (missing alt, labels)
- [ ] `mobile_tap_target` (tiny buttons)
- [ ] `modal_frustration` (newsletter popup)
- [ ] `circular_navigation` (product → home → product)
- [ ] `rage_click` on non-functional "Add to Cart"
- [ ] `form_abandonment` on checkout
- [ ] `search_frustration` (zero results)
- [ ] `cart_abandonment` (confusing CTAs)
- [ ] `unmet_goal` (checkout fails silently)

---

## Notes

- Keep the app **visually appealing** despite being broken—this tests whether Flamboyance detects UX issues that users might actually encounter in production apps
- All bugs should be **realistic**—patterns commonly seen in real websites
- Include some **working paths** so agents don't immediately fail; the friction should be discoverable through exploration
