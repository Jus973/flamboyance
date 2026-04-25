# Flamboyance UX Friction Report

- **Run ID:** `a31ac265-726a-41e4-b929-bf72d4fc4927`
- **Target URL:** http://localhost:5173
- **Status:** done
- **Agents:** 8
- **Total friction events:** 331
- **Generated:** 2026-04-25 20:51:54 UTC

## Executive Summary

**Issues found:** 🔴 8 critical | 🟠 12 high | 🟡 311 medium

**Top issues to address:**

1. 🔴 **unmet_goal**: Unmet goal (gave up): Complete a purchase flow quickly
2. 🔴 **unmet_goal**: Unmet goal (timeout): Find and read account settings
3. 🔴 **unmet_goal**: Unmet goal (gave up): Navigate all features and check edge cases

## Recommendations

- **rage_decoy** (302x): Either make this element interactive or remove clickable styling (cursor:pointer, hover effects).
- **circular_navigation** (9x): Improve navigation flow to prevent users from going in circles.
- **js_error** (8x): Fix the JavaScript error. Check the browser console for stack traces.
- **unmet_goal** (8x): Review the user flow for this goal and remove friction points.
- **dead_end** (4x): Add navigation options or call-to-action buttons to this page.

## Issues by Severity

### 🔴 Critical (8)

| Event | Description | URL | Persona |
|-------|-------------|-----|---------|
| unmet_goal | Unmet goal (gave up): Complete a purchase flow quickly |  | frustrated_exec |
| unmet_goal | Unmet goal (timeout): Find and read account settings |  | non_tech_senior |
| unmet_goal | Unmet goal (gave up): Navigate all features and check edge cases |  | power_user |
| unmet_goal | Unmet goal (gave up): Browse around and see what's available |  | casual_browser |
| unmet_goal | Unmet goal (gave up): Sign up for an account without getting confused |  | anxious_newbie |
| unmet_goal | Unmet goal (gave up): Systematically check every link and form |  | methodical_tester |
| unmet_goal | Unmet goal (gave up): Quickly check order status while on the go |  | mobile_commuter |
| unmet_goal | Unmet goal (timeout): Navigate using visible labels and clear affordances |  | accessibility_user |

### 🟠 High (12)

| Event | Description | URL | Persona |
|-------|-------------|-----|---------|
| js_error | JavaScript error: Failed to load resource: the server responded with a status of | http://localhost:5173/ | frustrated_exec |
| js_error | JavaScript error: Failed to load resource: the server responded with a status of | http://localhost:5173/ | non_tech_senior |
| js_error | JavaScript error: Failed to load resource: the server responded with a status of | http://localhost:5173/ | power_user |
| dead_end | Dead end: no clickable elements found on page | http://localhost:5173/order-status/ | power_user |
| js_error | JavaScript error: Failed to load resource: the server responded with a status of | http://localhost:5173/ | casual_browser |
| dead_end | Dead end: no clickable elements found on page | http://localhost:5173/stress/dead-end/ | casual_browser |
| js_error | JavaScript error: Failed to load resource: the server responded with a status of | http://localhost:5173/ | anxious_newbie |
| dead_end | Dead end: no clickable elements found on page | http://localhost:5173/stress/slow/ | anxious_newbie |
| js_error | JavaScript error: Failed to load resource: the server responded with a status of | http://localhost:5173/ | methodical_tester |
| dead_end | Dead end: no clickable elements found on page | http://localhost:5173/order-status/ | methodical_tester |
| js_error | JavaScript error: Failed to load resource: the server responded with a status of | http://localhost:5173/ | mobile_commuter |
| js_error | JavaScript error: Failed to load resource: the server responded with a status of | http://localhost:5173/ | accessibility_user |

### 🟡 Medium (311)

| Event | Description | URL | Persona |
|-------|-------------|-----|---------|
| rage_decoy | Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks click | http://localhost:5173 | frustrated_exec |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: Complete the wo')' looks click | http://localhost:5173/stress/icon-bar/ | frustrated_exec |
| rage_decoy | Rage decoy: element 'div:has-text('📄 📂 💾 ✂️ 📋 📌 ↩️ ↪️ B I U')' looks clickable ( | http://localhost:5173/stress/icon-bar/ | frustrated_exec |
| rage_decoy | Rage decoy: element 'div:has-text('Critical Actions (Icon-Only)  ')' looks click | http://localhost:5173/stress/icon-bar/ | frustrated_exec |
| rage_decoy | Rage decoy: element 'div:has-text('✓ → 👍 👎 ✕')' looks clickable (button-like sty | http://localhost:5173/stress/icon-bar/ | frustrated_exec |
| rage_decoy | Rage decoy: element 'div:has-text('💾 Save (text) 📂 Open (text) ')' looks clickab | http://localhost:5173/stress/icon-bar/ | frustrated_exec |
| rage_decoy | Rage decoy: element 'div:has-text('Document: Report_Q4_2024.docx ')' looks click | http://localhost:5173/stress/icon-bar/ | frustrated_exec |
| rage_decoy | Rage decoy: element 'div:has-text('Action performed:')' looks clickable (button- | http://localhost:5173/stress/icon-bar/ | frustrated_exec |
| rage_decoy | Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks click | http://localhost:5173/ | frustrated_exec |
| rage_decoy | Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks click | http://localhost:5173 | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Full Name * Address Line 1 * A')' looks click | http://localhost:5173/checkout/shipping/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Order Summary Widget Pro × 1 $')' looks click | http://localhost:5173/checkout/shipping/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Widget Pro Qty: 1 $49.99 Remov')' looks click | http://localhost:5173/cart/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Categories All Products Widget')' looks click | http://localhost:5173/shop/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Filter By Price Range Any Pric')' looks click | http://localhost:5173/shop/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('HOT Widget Pro  The ultimate w')' looks click | http://localhost:5173/shop/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'span:has-text('HOT')' looks clickable (button-like styling) | http://localhost:5173/shop/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('SALE Gadget Plus  Enhanced gad')' looks click | http://localhost:5173/shop/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'span:has-text('SALE')' looks clickable (button-like styling | http://localhost:5173/shop/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Doohickey Basic  Essential doo')' looks click | http://localhost:5173/shop/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('NEW Thingamajig XL  Extra larg')' looks click | http://localhost:5173/shop/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'span:has-text('NEW')' looks clickable (button-like styling) | http://localhost:5173/shop/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Gizmo Deluxe  Premium gizmo wi')' looks click | http://localhost:5173/shop/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks click | http://localhost:5173/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| circular_navigation | Circular navigation detected: http://localhost:5173/stress/many-links/#item-15 → | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks click | http://localhost:5173/stress/many-links/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks click | http://localhost:5173/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Dwell: 0s')' looks clickable (button-like sty | http://localhost:5173/stress/long-dwell/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The record_long')' looks click | http://localhost:5173/stress/long-dwell/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Section 1: Terms and Condition')' looks click | http://localhost:5173/stress/long-dwell/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('1. ACCEPTANCE OF TERMS  By acc')' looks click | http://localhost:5173/stress/long-dwell/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Section 2: Comprehension Quiz ')' looks click | http://localhost:5173/stress/long-dwell/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Question 1: What happens if yo')' looks click | http://localhost:5173/stress/long-dwell/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Question 2: What type of warra')' looks click | http://localhost:5173/stress/long-dwell/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Question 3: Who owns the intel')' looks click | http://localhost:5173/stress/long-dwell/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Section 3: Understanding Long ')' looks click | http://localhost:5173/stress/long-dwell/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Reading Progress:  Keep readin')' looks click | http://localhost:5173/stress/long-dwell/ | non_tech_senior |
| circular_navigation | Circular navigation detected: http://localhost:5173/ → http://localhost:5173/str | http://localhost:5173/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks click | http://localhost:5173/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Basic Mode Advanced Mode')' looks clickable ( | http://localhost:5173/account/settings/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Notification Preferences  Emai')' looks click | http://localhost:5173/account/settings/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Change Password Current Passwo')' looks click | http://localhost:5173/account/settings/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Looking for more options?  Swi')' looks click | http://localhost:5173/account/settings/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Settings Categories         Ex')' looks click | http://localhost:5173/account/settings/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Danger Zone             ▼     ')' looks click | http://localhost:5173/account/settings/ | non_tech_senior |
| rage_decoy | Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks click | http://localhost:5173 | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: Complete the wo')' looks click | http://localhost:5173/stress/icon-bar/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('📄 📂 💾 ✂️ 📋 📌 ↩️ ↪️ B I U')' looks clickable ( | http://localhost:5173/stress/icon-bar/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Critical Actions (Icon-Only)  ')' looks click | http://localhost:5173/stress/icon-bar/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('✓ → 👍 👎 ✕')' looks clickable (button-like sty | http://localhost:5173/stress/icon-bar/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('💾 Save (text) 📂 Open (text) ')' looks clickab | http://localhost:5173/stress/icon-bar/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Document: Report_Q4_2024.docx ')' looks click | http://localhost:5173/stress/icon-bar/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Action performed:')' looks clickable (button- | http://localhost:5173/stress/icon-bar/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks click | http://localhost:5173/ | power_user |
| circular_navigation | Circular navigation detected: http://localhost:5173/stress/icon-bar/ → http://lo | http://localhost:5173/stress/icon-bar/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: Complete the wo')' looks click | http://localhost:5173/stress/icon-bar/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('📄 📂 💾 ✂️ 📋 📌 ↩️ ↪️ B I U')' looks clickable ( | http://localhost:5173/stress/icon-bar/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Critical Actions (Icon-Only)  ')' looks click | http://localhost:5173/stress/icon-bar/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('✓ → 👍 👎 ✕')' looks clickable (button-like sty | http://localhost:5173/stress/icon-bar/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('💾 Save (text) 📂 Open (text) ')' looks clickab | http://localhost:5173/stress/icon-bar/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Document: Report_Q4_2024.docx ')' looks click | http://localhost:5173/stress/icon-bar/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Action performed:')' looks clickable (button- | http://localhost:5173/stress/icon-bar/ | power_user |
| circular_navigation | Circular navigation detected: http://localhost:5173/ → http://localhost:5173/str | http://localhost:5173/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks click | http://localhost:5173/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Basic Mode Advanced Mode')' looks clickable ( | http://localhost:5173/account/settings/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Notification Preferences  Emai')' looks click | http://localhost:5173/account/settings/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Change Password Current Passwo')' looks click | http://localhost:5173/account/settings/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Looking for more options?  Swi')' looks click | http://localhost:5173/account/settings/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Settings Categories         Ex')' looks click | http://localhost:5173/account/settings/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Danger Zone             ▼     ')' looks click | http://localhost:5173/account/settings/ | power_user |
| circular_navigation | Circular navigation detected: http://localhost:5173/ → http://localhost:5173/acc | http://localhost:5173/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks click | http://localhost:5173/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The decoy eleme')' looks click | http://localhost:5173/stress/rage-decoy/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Click to Continue')' looks clickable (cursor: | http://localhost:5173/stress/rage-decoy/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Submit Order')' looks clickable (cursor:point | http://localhost:5173/stress/rage-decoy/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Delete Item')' looks clickable (cursor:pointe | http://localhost:5173/stress/rage-decoy/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Special Offer!  Click here to ')' looks click | http://localhost:5173/stress/rage-decoy/ | power_user |
| rage_decoy | Rage decoy: element 'p:has-text('Click here to claim your disco')' looks clickab | http://localhost:5173/stress/rage-decoy/ | power_user |
| rage_decoy | Rage decoy: element 'span:has-text('click this link')' looks clickable (cursor:p | http://localhost:5173/stress/rage-decoy/ | power_user |
| rage_decoy | Rage decoy: element 'span:has-text('contact support')' looks clickable (cursor:p | http://localhost:5173/stress/rage-decoy/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Categories All Products Widget')' looks click | http://localhost:5173/shop/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Filter By Price Range Any Pric')' looks click | http://localhost:5173/shop/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('HOT Widget Pro  The ultimate w')' looks click | http://localhost:5173/shop/ | power_user |
| rage_decoy | Rage decoy: element 'span:has-text('HOT')' looks clickable (button-like styling) | http://localhost:5173/shop/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('SALE Gadget Plus  Enhanced gad')' looks click | http://localhost:5173/shop/ | power_user |
| rage_decoy | Rage decoy: element 'span:has-text('SALE')' looks clickable (button-like styling | http://localhost:5173/shop/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Doohickey Basic  Essential doo')' looks click | http://localhost:5173/shop/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('NEW Thingamajig XL  Extra larg')' looks click | http://localhost:5173/shop/ | power_user |
| rage_decoy | Rage decoy: element 'span:has-text('NEW')' looks clickable (button-like styling) | http://localhost:5173/shop/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Gizmo Deluxe  Premium gizmo wi')' looks click | http://localhost:5173/shop/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks click | http://localhost:5173/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Special Offer for Returning Cu')' looks click | http://localhost:5173/order-status/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Look Up Order       ↓ Scroll d')' looks click | http://localhost:5173/order-status/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Order Details       ← Scroll h')' looks click | http://localhost:5173/order-status/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Order #FP-2024-8847 - Tracking')' looks click | http://localhost:5173/order-status/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('✓')' looks clickable (button-like styling) bu | http://localhost:5173/order-status/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('✓')' looks clickable (button-like styling) bu | http://localhost:5173/order-status/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('✓')' looks clickable (button-like styling) bu | http://localhost:5173/order-status/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('4')' looks clickable (button-like styling) bu | http://localhost:5173/order-status/ | power_user |
| rage_decoy | Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks click | http://localhost:5173 | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: Each form has a')' looks click | http://localhost:5173/stress/broken-form | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('Contact Form (Broken Labels)  ')' looks click | http://localhost:5173/stress/broken-form | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('Terms Agreement (Scroll to Ena')' looks click | http://localhost:5173/stress/broken-form | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('Subscription Form (Hidden Requ')' looks click | http://localhost:5173/stress/broken-form | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('Newsletter Preferences (Self-U')' looks click | http://localhost:5173/stress/broken-form | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('Shipping Options (Bad Default)')' looks click | http://localhost:5173/stress/broken-form | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('Payment Method (Broken Radio G')' looks click | http://localhost:5173/stress/broken-form | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks click | http://localhost:5173/ | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('Dwell: 0s')' looks clickable (button-like sty | http://localhost:5173/stress/long-dwell/ | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The record_long')' looks click | http://localhost:5173/stress/long-dwell/ | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('Section 1: Terms and Condition')' looks click | http://localhost:5173/stress/long-dwell/ | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('1. ACCEPTANCE OF TERMS  By acc')' looks click | http://localhost:5173/stress/long-dwell/ | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('Section 2: Comprehension Quiz ')' looks click | http://localhost:5173/stress/long-dwell/ | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('Question 1: What happens if yo')' looks click | http://localhost:5173/stress/long-dwell/ | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('Question 2: What type of warra')' looks click | http://localhost:5173/stress/long-dwell/ | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('Question 3: Who owns the intel')' looks click | http://localhost:5173/stress/long-dwell/ | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('Section 3: Understanding Long ')' looks click | http://localhost:5173/stress/long-dwell/ | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('Reading Progress:  Keep readin')' looks click | http://localhost:5173/stress/long-dwell/ | casual_browser |
| circular_navigation | Circular navigation detected: http://localhost:5173/ → http://localhost:5173/str | http://localhost:5173/ | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks click | http://localhost:5173/ | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: Complete the wo')' looks click | http://localhost:5173/stress/icon-bar/ | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('📄 📂 💾 ✂️ 📋 📌 ↩️ ↪️ B I U')' looks clickable ( | http://localhost:5173/stress/icon-bar/ | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('Critical Actions (Icon-Only)  ')' looks click | http://localhost:5173/stress/icon-bar/ | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('✓ → 👍 👎 ✕')' looks clickable (button-like sty | http://localhost:5173/stress/icon-bar/ | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('💾 Save (text) 📂 Open (text) ')' looks clickab | http://localhost:5173/stress/icon-bar/ | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('Document: Report_Q4_2024.docx ')' looks click | http://localhost:5173/stress/icon-bar/ | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('Action performed:')' looks clickable (button- | http://localhost:5173/stress/icon-bar/ | casual_browser |
| circular_navigation | Circular navigation detected: http://localhost:5173/ → http://localhost:5173/str | http://localhost:5173/ | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks click | http://localhost:5173/ | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('Dead End Detection  The record')' looks click | http://localhost:5173/stress/dead-end/ | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('How to Escape  Since there are')' looks click | http://localhost:5173/stress/dead-end/ | casual_browser |
| rage_decoy | Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks click | http://localhost:5173 | anxious_newbie |
| rage_decoy | Rage decoy: element 'div:has-text('Categories All Products Widget')' looks click | http://localhost:5173/shop/ | anxious_newbie |
| rage_decoy | Rage decoy: element 'div:has-text('Filter By Price Range Any Pric')' looks click | http://localhost:5173/shop/ | anxious_newbie |
| rage_decoy | Rage decoy: element 'div:has-text('HOT Widget Pro  The ultimate w')' looks click | http://localhost:5173/shop/ | anxious_newbie |
| rage_decoy | Rage decoy: element 'span:has-text('HOT')' looks clickable (button-like styling) | http://localhost:5173/shop/ | anxious_newbie |
| rage_decoy | Rage decoy: element 'div:has-text('SALE Gadget Plus  Enhanced gad')' looks click | http://localhost:5173/shop/ | anxious_newbie |
| rage_decoy | Rage decoy: element 'span:has-text('SALE')' looks clickable (button-like styling | http://localhost:5173/shop/ | anxious_newbie |
| rage_decoy | Rage decoy: element 'div:has-text('Doohickey Basic  Essential doo')' looks click | http://localhost:5173/shop/ | anxious_newbie |
| rage_decoy | Rage decoy: element 'div:has-text('NEW Thingamajig XL  Extra larg')' looks click | http://localhost:5173/shop/ | anxious_newbie |
| rage_decoy | Rage decoy: element 'span:has-text('NEW')' looks clickable (button-like styling) | http://localhost:5173/shop/ | anxious_newbie |
| rage_decoy | Rage decoy: element 'div:has-text('Gizmo Deluxe  Premium gizmo wi')' looks click | http://localhost:5173/shop/ | anxious_newbie |
| rage_decoy | Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks click | http://localhost:5173/ | anxious_newbie |
| rage_decoy | Rage decoy: element 'div:has-text('Load time: calculating...')' looks clickable  | http://localhost:5173/stress/slow/ | anxious_newbie |
| rage_decoy | Rage decoy: element 'div:has-text('slow_load Signal: The record_s')' looks click | http://localhost:5173/stress/slow/ | anxious_newbie |
| rage_decoy | Rage decoy: element 'div:has-text('Test Different Load Times     ')' looks click | http://localhost:5173/stress/slow/ | anxious_newbie |
| rage_decoy | Rage decoy: element 'div:has-text('2s (under threshold)         4')' looks click | http://localhost:5173/stress/slow/ | anxious_newbie |
| rage_decoy | Rage decoy: element 'div:has-text('Content Loaded!               ')' looks click | http://localhost:5173/stress/slow/ | anxious_newbie |
| rage_decoy | Rage decoy: element 'div:has-text('Slow Page Information         ')' looks click | http://localhost:5173/stress/slow/ | anxious_newbie |
| rage_decoy | Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks click | http://localhost:5173 | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Categories All Products Widget')' looks click | http://localhost:5173/shop/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Filter By Price Range Any Pric')' looks click | http://localhost:5173/shop/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('HOT Widget Pro  The ultimate w')' looks click | http://localhost:5173/shop/ | methodical_tester |
| rage_decoy | Rage decoy: element 'span:has-text('HOT')' looks clickable (button-like styling) | http://localhost:5173/shop/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('SALE Gadget Plus  Enhanced gad')' looks click | http://localhost:5173/shop/ | methodical_tester |
| rage_decoy | Rage decoy: element 'span:has-text('SALE')' looks clickable (button-like styling | http://localhost:5173/shop/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Doohickey Basic  Essential doo')' looks click | http://localhost:5173/shop/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('NEW Thingamajig XL  Extra larg')' looks click | http://localhost:5173/shop/ | methodical_tester |
| rage_decoy | Rage decoy: element 'span:has-text('NEW')' looks clickable (button-like styling) | http://localhost:5173/shop/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Gizmo Deluxe  Premium gizmo wi')' looks click | http://localhost:5173/shop/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks click | http://localhost:5173/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Your session will expire in: 5')' looks click | http://localhost:5173/signup/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Full Name * Email Address * Pa')' looks click | http://localhost:5173/signup/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('⚠️ This email may already be r')' looks click | http://localhost:5173/signup/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('I'm not a robot')' looks clickable (button-li | http://localhost:5173/signup/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Important: By creating an acco')' looks click | http://localhost:5173/signup/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Account Created!              ')' looks click | http://localhost:5173/signup/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Your session will expire in: 5')' looks click | http://localhost:5173/signup/# | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Full Name * Email Address * Pa')' looks click | http://localhost:5173/signup/# | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('⚠️ This email may already be r')' looks click | http://localhost:5173/signup/# | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('I'm not a robot')' looks clickable (button-li | http://localhost:5173/signup/# | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Important: By creating an acco')' looks click | http://localhost:5173/signup/# | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Account Created!              ')' looks click | http://localhost:5173/signup/# | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks click | http://localhost:5173/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Basic Mode Advanced Mode')' looks clickable ( | http://localhost:5173/account/settings/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Notification Preferences  Emai')' looks click | http://localhost:5173/account/settings/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Change Password Current Passwo')' looks click | http://localhost:5173/account/settings/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Looking for more options?  Swi')' looks click | http://localhost:5173/account/settings/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Settings Categories         Ex')' looks click | http://localhost:5173/account/settings/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Danger Zone             ▼     ')' looks click | http://localhost:5173/account/settings/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Quick Actions 📦 ✏️ 🔔 🔒 ❓')' looks clickable ( | http://localhost:5173/account/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Profile Information  Name: Dem')' looks click | http://localhost:5173/account/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Recent Orders  Order #FP-2024-')' looks click | http://localhost:5173/account/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Quick Settings Fast access to ')' looks click | http://localhost:5173/account/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Quick Settings is currently un')' looks click | http://localhost:5173/account/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Account Options Advanced Accou')' looks click | http://localhost:5173/account/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Need help finding something?  ')' looks click | http://localhost:5173/account/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Special Offer for Returning Cu')' looks click | http://localhost:5173/order-status/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Look Up Order       ↓ Scroll d')' looks click | http://localhost:5173/order-status/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Order Details       ← Scroll h')' looks click | http://localhost:5173/order-status/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Order #FP-2024-8847 - Tracking')' looks click | http://localhost:5173/order-status/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('✓')' looks clickable (button-like styling) bu | http://localhost:5173/order-status/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('✓')' looks clickable (button-like styling) bu | http://localhost:5173/order-status/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('✓')' looks clickable (button-like styling) bu | http://localhost:5173/order-status/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('4')' looks clickable (button-like styling) bu | http://localhost:5173/order-status/ | methodical_tester |
| rage_decoy | Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks click | http://localhost:5173 | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| circular_navigation | Circular navigation detected: http://localhost:5173/stress/many-links/#item-12 → | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks click | http://localhost:5173/stress/many-links/ | mobile_commuter |
| rage_decoy | Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks click | http://localhost:5173 | accessibility_user |
| rage_decoy | Rage decoy: element 'div:has-text('Full Name * Address Line 1 * A')' looks click | http://localhost:5173/checkout/shipping/ | accessibility_user |
| rage_decoy | Rage decoy: element 'div:has-text('Order Summary Widget Pro × 1 $')' looks click | http://localhost:5173/checkout/shipping/ | accessibility_user |
| rage_decoy | Rage decoy: element 'div:has-text('Categories All Products Widget')' looks click | http://localhost:5173/shop/ | accessibility_user |
| rage_decoy | Rage decoy: element 'div:has-text('Filter By Price Range Any Pric')' looks click | http://localhost:5173/shop/ | accessibility_user |
| rage_decoy | Rage decoy: element 'div:has-text('HOT Widget Pro  The ultimate w')' looks click | http://localhost:5173/shop/ | accessibility_user |
| rage_decoy | Rage decoy: element 'span:has-text('HOT')' looks clickable (button-like styling) | http://localhost:5173/shop/ | accessibility_user |
| rage_decoy | Rage decoy: element 'div:has-text('SALE Gadget Plus  Enhanced gad')' looks click | http://localhost:5173/shop/ | accessibility_user |
| rage_decoy | Rage decoy: element 'span:has-text('SALE')' looks clickable (button-like styling | http://localhost:5173/shop/ | accessibility_user |
| rage_decoy | Rage decoy: element 'div:has-text('Doohickey Basic  Essential doo')' looks click | http://localhost:5173/shop/ | accessibility_user |
| rage_decoy | Rage decoy: element 'div:has-text('NEW Thingamajig XL  Extra larg')' looks click | http://localhost:5173/shop/ | accessibility_user |
| rage_decoy | Rage decoy: element 'span:has-text('NEW')' looks clickable (button-like styling) | http://localhost:5173/shop/ | accessibility_user |
| rage_decoy | Rage decoy: element 'div:has-text('Gizmo Deluxe  Premium gizmo wi')' looks click | http://localhost:5173/shop/ | accessibility_user |
| rage_decoy | Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks click | http://localhost:5173/ | accessibility_user |
| rage_decoy | Rage decoy: element 'div:has-text('Scenario Goal: The decoy eleme')' looks click | http://localhost:5173/stress/rage-decoy/ | accessibility_user |
| rage_decoy | Rage decoy: element 'div:has-text('Click to Continue')' looks clickable (cursor: | http://localhost:5173/stress/rage-decoy/ | accessibility_user |
| rage_decoy | Rage decoy: element 'div:has-text('Submit Order')' looks clickable (cursor:point | http://localhost:5173/stress/rage-decoy/ | accessibility_user |
| rage_decoy | Rage decoy: element 'div:has-text('Delete Item')' looks clickable (cursor:pointe | http://localhost:5173/stress/rage-decoy/ | accessibility_user |
| rage_decoy | Rage decoy: element 'div:has-text('Special Offer!  Click here to ')' looks click | http://localhost:5173/stress/rage-decoy/ | accessibility_user |
| rage_decoy | Rage decoy: element 'p:has-text('Click here to claim your disco')' looks clickab | http://localhost:5173/stress/rage-decoy/ | accessibility_user |
| rage_decoy | Rage decoy: element 'span:has-text('click this link')' looks clickable (cursor:p | http://localhost:5173/stress/rage-decoy/ | accessibility_user |
| rage_decoy | Rage decoy: element 'span:has-text('contact support')' looks clickable (cursor:p | http://localhost:5173/stress/rage-decoy/ | accessibility_user |
| circular_navigation | Circular navigation detected: http://localhost:5173/ → http://localhost:5173/str | http://localhost:5173/ | accessibility_user |
| rage_decoy | Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks click | http://localhost:5173/ | accessibility_user |
| rage_decoy | Rage decoy: element 'div:has-text('Categories All Products Widget')' looks click | http://localhost:5173/shop/ | accessibility_user |
| rage_decoy | Rage decoy: element 'div:has-text('Filter By Price Range Any Pric')' looks click | http://localhost:5173/shop/ | accessibility_user |
| rage_decoy | Rage decoy: element 'div:has-text('HOT Widget Pro  The ultimate w')' looks click | http://localhost:5173/shop/ | accessibility_user |
| rage_decoy | Rage decoy: element 'span:has-text('HOT')' looks clickable (button-like styling) | http://localhost:5173/shop/ | accessibility_user |
| rage_decoy | Rage decoy: element 'div:has-text('SALE Gadget Plus  Enhanced gad')' looks click | http://localhost:5173/shop/ | accessibility_user |
| rage_decoy | Rage decoy: element 'span:has-text('SALE')' looks clickable (button-like styling | http://localhost:5173/shop/ | accessibility_user |
| rage_decoy | Rage decoy: element 'div:has-text('Doohickey Basic  Essential doo')' looks click | http://localhost:5173/shop/ | accessibility_user |
| rage_decoy | Rage decoy: element 'div:has-text('NEW Thingamajig XL  Extra larg')' looks click | http://localhost:5173/shop/ | accessibility_user |
| rage_decoy | Rage decoy: element 'span:has-text('NEW')' looks clickable (button-like styling) | http://localhost:5173/shop/ | accessibility_user |
| rage_decoy | Rage decoy: element 'div:has-text('Gizmo Deluxe  Premium gizmo wi')' looks click | http://localhost:5173/shop/ | accessibility_user |

## Agent Summary

| Persona | Status | Events | Critical | High | Elapsed |
|---------|--------|--------|----------|------|---------|
| frustrated_exec | gave_up | 11 | 1 | 1 | 18.5s |
| non_tech_senior | done | 70 | 1 | 1 | 60.6s |
| power_user | done | 57 | 1 | 2 | 35.6s |
| casual_browser | done | 35 | 1 | 2 | 16.4s |
| anxious_newbie | done | 21 | 1 | 2 | 12.3s |
| methodical_tester | done | 49 | 1 | 2 | 10.8s |
| mobile_commuter | gave_up | 52 | 1 | 1 | 18.1s |
| accessibility_user | done | 36 | 1 | 1 | 61.0s |

## Agent: frustrated_exec

- **Status:** gave_up
- **Elapsed:** 18.5s

### Navigation Path

1. http://localhost:5173
2. http://localhost:5173/stress/icon-bar/
3. http://localhost:5173/

### Frustration Events

- 🔴 **unmet_goal** (critical): Unmet goal (gave up): Complete a purchase flow quickly
- 🟠 **js_error** (high): JavaScript error: Failed to load resource: the server responded with a status of 404 (Not Found) (source: http://localhost:5173/favicon.ico)
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: Complete the wo')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('📄 📂 💾 ✂️ 📋 📌 ↩️ ↪️ B I U')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Critical Actions (Icon-Only)  ')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('✓ → 👍 👎 ✕')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('💾 Save (text) 📂 Open (text) ')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Document: Report_Q4_2024.docx ')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Action performed:')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks clickable (clickable class name, button-like styling) but is not interactive

## Agent: non_tech_senior

- **Status:** done
- **Elapsed:** 60.6s

### Navigation Path

1. http://localhost:5173
2. http://localhost:5173/checkout/shipping/
3. http://localhost:5173/cart/
4. http://localhost:5173/shop/
5. http://localhost:5173/
6. http://localhost:5173/stress/many-links/
7. http://localhost:5173/stress/many-links/#item-7
8. http://localhost:5173/stress/many-links/#item-9
9. http://localhost:5173/stress/many-links/#item-15
10. http://localhost:5173/stress/many-links/#item-3
11. http://localhost:5173/stress/many-links/#item-15
12. http://localhost:5173/stress/many-links/#item-17
13. http://localhost:5173/stress/many-links/#item-20
14. http://localhost:5173/stress/many-links/#item-12
15. http://localhost:5173/stress/many-links/#item-5
16. http://localhost:5173/stress/many-links/#item-6
17. http://localhost:5173/
18. http://localhost:5173/stress/long-dwell/
19. http://localhost:5173/
20. http://localhost:5173/account/settings/

### Frustration Events

- 🔴 **unmet_goal** (critical): Unmet goal (timeout): Find and read account settings
- 🟠 **js_error** (high): JavaScript error: Failed to load resource: the server responded with a status of 404 (Not Found) (source: http://localhost:5173/favicon.ico)
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Full Name * Address Line 1 * A')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Order Summary Widget Pro × 1 $')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Widget Pro Qty: 1 $49.99 Remov')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Categories All Products Widget')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Filter By Price Range Any Pric')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('HOT Widget Pro  The ultimate w')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'span:has-text('HOT')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('SALE Gadget Plus  Enhanced gad')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'span:has-text('SALE')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Doohickey Basic  Essential doo')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('NEW Thingamajig XL  Extra larg')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'span:has-text('NEW')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Gizmo Deluxe  Premium gizmo wi')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **circular_navigation** (medium): Circular navigation detected: http://localhost:5173/stress/many-links/#item-15 → http://localhost:5173/stress/many-links/#item-3 → http://localhost:5173/stress/many-links/#item-15
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Dwell: 0s')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The record_long')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Section 1: Terms and Condition')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('1. ACCEPTANCE OF TERMS  By acc')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Section 2: Comprehension Quiz ')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Question 1: What happens if yo')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Question 2: What type of warra')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Question 3: Who owns the intel')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Section 3: Understanding Long ')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Reading Progress:  Keep readin')' looks clickable (button-like styling) but is not interactive
- 🟡 **circular_navigation** (medium): Circular navigation detected: http://localhost:5173/ → http://localhost:5173/stress/long-dwell/ → http://localhost:5173/
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Basic Mode Advanced Mode')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Notification Preferences  Emai')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Change Password Current Passwo')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Looking for more options?  Swi')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Settings Categories         Ex')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Danger Zone             ▼     ')' looks clickable (clickable class name, button-like styling) but is not interactive

## Agent: power_user

- **Status:** done
- **Elapsed:** 35.6s

### Navigation Path

1. http://localhost:5173
2. http://localhost:5173/stress/icon-bar/
3. http://localhost:5173/
4. http://localhost:5173/stress/icon-bar/
5. http://localhost:5173/
6. http://localhost:5173/account/settings/
7. http://localhost:5173/
8. http://localhost:5173/stress/rage-decoy/
9. http://localhost:5173/shop/
10. http://localhost:5173/
11. http://localhost:5173/order-status/

### Frustration Events

- 🔴 **unmet_goal** (critical): Unmet goal (gave up): Navigate all features and check edge cases
- 🟠 **js_error** (high): JavaScript error: Failed to load resource: the server responded with a status of 404 (Not Found) (source: http://localhost:5173/favicon.ico)
- 🟠 **dead_end** (high): Dead end: no clickable elements found on page
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: Complete the wo')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('📄 📂 💾 ✂️ 📋 📌 ↩️ ↪️ B I U')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Critical Actions (Icon-Only)  ')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('✓ → 👍 👎 ✕')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('💾 Save (text) 📂 Open (text) ')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Document: Report_Q4_2024.docx ')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Action performed:')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **circular_navigation** (medium): Circular navigation detected: http://localhost:5173/stress/icon-bar/ → http://localhost:5173/ → http://localhost:5173/stress/icon-bar/
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: Complete the wo')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('📄 📂 💾 ✂️ 📋 📌 ↩️ ↪️ B I U')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Critical Actions (Icon-Only)  ')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('✓ → 👍 👎 ✕')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('💾 Save (text) 📂 Open (text) ')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Document: Report_Q4_2024.docx ')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Action performed:')' looks clickable (button-like styling) but is not interactive
- 🟡 **circular_navigation** (medium): Circular navigation detected: http://localhost:5173/ → http://localhost:5173/stress/icon-bar/ → http://localhost:5173/
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Basic Mode Advanced Mode')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Notification Preferences  Emai')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Change Password Current Passwo')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Looking for more options?  Swi')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Settings Categories         Ex')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Danger Zone             ▼     ')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **circular_navigation** (medium): Circular navigation detected: http://localhost:5173/ → http://localhost:5173/account/settings/ → http://localhost:5173/
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The decoy eleme')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Click to Continue')' looks clickable (cursor:pointer, clickable class name, box-shadow with pointer, interactive transition) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Submit Order')' looks clickable (cursor:pointer, clickable class name, box-shadow with pointer, interactive transition) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Delete Item')' looks clickable (cursor:pointer, clickable class name, box-shadow with pointer, interactive transition) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Special Offer!  Click here to ')' looks clickable (cursor:pointer, clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'p:has-text('Click here to claim your disco')' looks clickable (cursor:pointer) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'span:has-text('click this link')' looks clickable (cursor:pointer, clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'span:has-text('contact support')' looks clickable (cursor:pointer, clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Categories All Products Widget')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Filter By Price Range Any Pric')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('HOT Widget Pro  The ultimate w')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'span:has-text('HOT')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('SALE Gadget Plus  Enhanced gad')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'span:has-text('SALE')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Doohickey Basic  Essential doo')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('NEW Thingamajig XL  Extra larg')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'span:has-text('NEW')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Gizmo Deluxe  Premium gizmo wi')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Special Offer for Returning Cu')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Look Up Order       ↓ Scroll d')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Order Details       ← Scroll h')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Order #FP-2024-8847 - Tracking')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('✓')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('✓')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('✓')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('4')' looks clickable (button-like styling) but is not interactive

## Agent: casual_browser

- **Status:** done
- **Elapsed:** 16.4s

### Navigation Path

1. http://localhost:5173
2. http://localhost:5173/stress/broken-forms/
3. http://localhost:5173/
4. http://localhost:5173/stress/long-dwell/
5. http://localhost:5173/
6. http://localhost:5173/stress/icon-bar/
7. http://localhost:5173/
8. http://localhost:5173/stress/dead-end/

### Frustration Events

- 🔴 **unmet_goal** (critical): Unmet goal (gave up): Browse around and see what's available
- 🟠 **js_error** (high): JavaScript error: Failed to load resource: the server responded with a status of 404 (Not Found) (source: http://localhost:5173/favicon.ico)
- 🟠 **dead_end** (high): Dead end: no clickable elements found on page
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: Each form has a')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Contact Form (Broken Labels)  ')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Terms Agreement (Scroll to Ena')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Subscription Form (Hidden Requ')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Newsletter Preferences (Self-U')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Shipping Options (Bad Default)')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Payment Method (Broken Radio G')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Dwell: 0s')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The record_long')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Section 1: Terms and Condition')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('1. ACCEPTANCE OF TERMS  By acc')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Section 2: Comprehension Quiz ')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Question 1: What happens if yo')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Question 2: What type of warra')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Question 3: Who owns the intel')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Section 3: Understanding Long ')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Reading Progress:  Keep readin')' looks clickable (button-like styling) but is not interactive
- 🟡 **circular_navigation** (medium): Circular navigation detected: http://localhost:5173/ → http://localhost:5173/stress/long-dwell/ → http://localhost:5173/
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: Complete the wo')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('📄 📂 💾 ✂️ 📋 📌 ↩️ ↪️ B I U')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Critical Actions (Icon-Only)  ')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('✓ → 👍 👎 ✕')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('💾 Save (text) 📂 Open (text) ')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Document: Report_Q4_2024.docx ')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Action performed:')' looks clickable (button-like styling) but is not interactive
- 🟡 **circular_navigation** (medium): Circular navigation detected: http://localhost:5173/ → http://localhost:5173/stress/icon-bar/ → http://localhost:5173/
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Dead End Detection  The record')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('How to Escape  Since there are')' looks clickable (button-like styling) but is not interactive

## Agent: anxious_newbie

- **Status:** done
- **Elapsed:** 12.3s

### Navigation Path

1. http://localhost:5173
2. http://localhost:5173/shop/
3. http://localhost:5173/
4. http://localhost:5173/stress/slow/

### Frustration Events

- 🔴 **unmet_goal** (critical): Unmet goal (gave up): Sign up for an account without getting confused
- 🟠 **js_error** (high): JavaScript error: Failed to load resource: the server responded with a status of 404 (Not Found) (source: http://localhost:5173/favicon.ico)
- 🟠 **dead_end** (high): Dead end: no clickable elements found on page
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Categories All Products Widget')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Filter By Price Range Any Pric')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('HOT Widget Pro  The ultimate w')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'span:has-text('HOT')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('SALE Gadget Plus  Enhanced gad')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'span:has-text('SALE')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Doohickey Basic  Essential doo')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('NEW Thingamajig XL  Extra larg')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'span:has-text('NEW')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Gizmo Deluxe  Premium gizmo wi')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Load time: calculating...')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('slow_load Signal: The record_s')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Test Different Load Times     ')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('2s (under threshold)         4')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Content Loaded!               ')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Slow Page Information         ')' looks clickable (clickable class name, button-like styling) but is not interactive

## Agent: methodical_tester

- **Status:** done
- **Elapsed:** 10.8s

### Navigation Path

1. http://localhost:5173
2. http://localhost:5173/shop/
3. http://localhost:5173/
4. http://localhost:5173/signup/
5. http://localhost:5173/signup/#
6. http://localhost:5173/
7. http://localhost:5173/account/settings/
8. http://localhost:5173/account/
9. http://localhost:5173/order-status/

### Frustration Events

- 🔴 **unmet_goal** (critical): Unmet goal (gave up): Systematically check every link and form
- 🟠 **js_error** (high): JavaScript error: Failed to load resource: the server responded with a status of 404 (Not Found) (source: http://localhost:5173/favicon.ico)
- 🟠 **dead_end** (high): Dead end: no clickable elements found on page
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Categories All Products Widget')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Filter By Price Range Any Pric')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('HOT Widget Pro  The ultimate w')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'span:has-text('HOT')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('SALE Gadget Plus  Enhanced gad')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'span:has-text('SALE')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Doohickey Basic  Essential doo')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('NEW Thingamajig XL  Extra larg')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'span:has-text('NEW')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Gizmo Deluxe  Premium gizmo wi')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Your session will expire in: 5')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Full Name * Email Address * Pa')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('⚠️ This email may already be r')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('I'm not a robot')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Important: By creating an acco')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Account Created!              ')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Your session will expire in: 5')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Full Name * Email Address * Pa')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('⚠️ This email may already be r')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('I'm not a robot')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Important: By creating an acco')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Account Created!              ')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Basic Mode Advanced Mode')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Notification Preferences  Emai')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Change Password Current Passwo')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Looking for more options?  Swi')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Settings Categories         Ex')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Danger Zone             ▼     ')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Quick Actions 📦 ✏️ 🔔 🔒 ❓')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Profile Information  Name: Dem')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Recent Orders  Order #FP-2024-')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Quick Settings Fast access to ')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Quick Settings is currently un')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Account Options Advanced Accou')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Need help finding something?  ')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Special Offer for Returning Cu')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Look Up Order       ↓ Scroll d')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Order Details       ← Scroll h')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Order #FP-2024-8847 - Tracking')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('✓')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('✓')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('✓')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('4')' looks clickable (button-like styling) but is not interactive

## Agent: mobile_commuter

- **Status:** gave_up
- **Elapsed:** 18.1s

### Navigation Path

1. http://localhost:5173
2. http://localhost:5173/stress/many-links/
3. http://localhost:5173/stress/many-links/#item-12
4. http://localhost:5173/stress/many-links/#item-18
5. http://localhost:5173/stress/many-links/#item-12
6. http://localhost:5173/stress/many-links/#item-10
7. http://localhost:5173/stress/many-links/#item-9
8. http://localhost:5173/stress/many-links/#item-11
9. http://localhost:5173/stress/many-links/#item-2
10. http://localhost:5173/stress/many-links/#item-7
11. http://localhost:5173/stress/many-links/#item-20
12. http://localhost:5173/stress/many-links/#item-5
13. http://localhost:5173/stress/many-links/#item-19
14. http://localhost:5173/stress/many-links/#item-20
15. http://localhost:5173/stress/many-links/#item-11
16. http://localhost:5173/stress/many-links/#item-14
17. http://localhost:5173/stress/many-links/#item-5

### Frustration Events

- 🔴 **unmet_goal** (critical): Unmet goal (gave up): Quickly check order status while on the go
- 🟠 **js_error** (high): JavaScript error: Failed to load resource: the server responded with a status of 404 (Not Found) (source: http://localhost:5173/favicon.ico)
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **circular_navigation** (medium): Circular navigation detected: http://localhost:5173/stress/many-links/#item-12 → http://localhost:5173/stress/many-links/#item-18 → http://localhost:5173/stress/many-links/#item-12
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The agent can o')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Link 1 Link 2 Link 3 Link 4 Li')' looks clickable (clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Total Interactive Elements  Th')' looks clickable (clickable class name, button-like styling) but is not interactive

## Agent: accessibility_user

- **Status:** done
- **Elapsed:** 61.0s

### Navigation Path

1. http://localhost:5173
2. http://localhost:5173/checkout/shipping/
3. http://localhost:5173/shop/
4. http://localhost:5173/
5. http://localhost:5173/stress/rage-decoy/
6. http://localhost:5173/
7. http://localhost:5173/shop/

### Frustration Events

- 🔴 **unmet_goal** (critical): Unmet goal (timeout): Navigate using visible labels and clear affordances
- 🟠 **js_error** (high): JavaScript error: Failed to load resource: the server responded with a status of 404 (Not Found) (source: http://localhost:5173/favicon.ico)
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Full Name * Address Line 1 * A')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Order Summary Widget Pro × 1 $')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Categories All Products Widget')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Filter By Price Range Any Pric')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('HOT Widget Pro  The ultimate w')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'span:has-text('HOT')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('SALE Gadget Plus  Enhanced gad')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'span:has-text('SALE')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Doohickey Basic  Essential doo')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('NEW Thingamajig XL  Extra larg')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'span:has-text('NEW')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Gizmo Deluxe  Premium gizmo wi')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Scenario Goal: The decoy eleme')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Click to Continue')' looks clickable (cursor:pointer, clickable class name, box-shadow with pointer, interactive transition) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Submit Order')' looks clickable (cursor:pointer, clickable class name, box-shadow with pointer, interactive transition) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Delete Item')' looks clickable (cursor:pointer, clickable class name, box-shadow with pointer, interactive transition) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Special Offer!  Click here to ')' looks clickable (cursor:pointer, clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'p:has-text('Click here to claim your disco')' looks clickable (cursor:pointer) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'span:has-text('click this link')' looks clickable (cursor:pointer, clickable class name) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'span:has-text('contact support')' looks clickable (cursor:pointer, clickable class name) but is not interactive
- 🟡 **circular_navigation** (medium): Circular navigation detected: http://localhost:5173/ → http://localhost:5173/stress/rage-decoy/ → http://localhost:5173/
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Persona	Patience	Tech	Target F')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Categories All Products Widget')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Filter By Price Range Any Pric')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('HOT Widget Pro  The ultimate w')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'span:has-text('HOT')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('SALE Gadget Plus  Enhanced gad')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'span:has-text('SALE')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Doohickey Basic  Essential doo')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('NEW Thingamajig XL  Extra larg')' looks clickable (clickable class name, button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'span:has-text('NEW')' looks clickable (button-like styling) but is not interactive
- 🟡 **rage_decoy** (medium): Rage decoy: element 'div:has-text('Gizmo Deluxe  Premium gizmo wi')' looks clickable (clickable class name, button-like styling) but is not interactive
