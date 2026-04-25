# Phase 1 Results Summary

This document summarizes what the earlier iterations of Flamboyance tracked during Phase 1 development.

## Overview

Phase 1 focused on building the core UX friction detection system with multiple agent personas and heuristic-based event detection.

---

## Event Types Tracked

### 1. **rage_decoy** (Most Common)
Elements that visually appear clickable but are not interactive.
- **Detection criteria:**
  - `cursor: pointer` CSS property
  - Button-like styling (rounded corners, shadows, hover effects)
  - Clickable class names in the DOM
  - Text suggesting interactivity ("Click here", "Submit", etc.)
- **Coordinates captured:** x, y position of element center for screenshot annotation
- **Example:** `div:has-text('Click to Continue')` with cursor:pointer but no click handler

### 2. **circular_navigation**
User navigates in loops without making progress.
- **Detection:** Tracks URL history and flags when user returns to a previously visited page within a short sequence
- **Pattern:** `URL A → URL B → URL A` detected as circular
- **Example:** `/checkout/shipping/ → /cart/ → /checkout/shipping/`

### 3. **dead_end**
Pages with no clickable elements or navigation options.
- **Detection:** Page analysis finds zero interactive elements
- **Severity:** High
- **Example:** `/order-status/` page with no buttons or links

### 4. **unmet_goal**
Agent failed to complete their assigned persona goal.
- **Triggers:**
  - `gave_up`: Agent explicitly abandoned the task
  - `timeout`: Time limit exceeded
- **Severity:** Critical
- **Example:** "Unmet goal (gave up): Complete a purchase flow quickly"

### 5. **js_error**
JavaScript errors captured from browser console.
- **Severity:** High
- **Example:** "Failed to load resource: 404 (Not Found)" for favicon.ico

### 6. **slow_load**
Pages that take too long to load.
- **Threshold:** Configurable (default ~3 seconds)
- **Captures:** Load time in milliseconds

### 7. **broken_image**
Images that fail to load on the page.
- **Captures:** Image src URL and CSS selector

### 8. **long_dwell**
User spends excessive time on a single page without action.
- **Detection:** Timer tracks time since last meaningful action

---

## Agent Personas Tracked

| Persona | Patience | Tech Level | Goal |
|---------|----------|------------|------|
| **frustrated_exec** | Low | Medium | Complete a purchase flow quickly |
| **non_tech_senior** | High | Low | Find and read account settings |
| **power_user** | Medium | High | Navigate all features and check edge cases |
| **casual_browser** | Medium | Medium | Browse around and see what's available |
| **anxious_newbie** | Low | Low | Sign up for an account without getting confused |
| **methodical_tester** | High | High | Systematically check every link and form |
| **mobile_commuter** | Low | Medium | Quickly check order status while on the go |
| **accessibility_user** | High | Medium | Navigate using visible labels and clear affordances |

---

## Report Generation Features

### Severity Classification
- 🔴 **Critical:** unmet_goal
- 🟠 **High:** js_error, dead_end
- 🟡 **Medium:** rage_decoy, circular_navigation, slow_load
- 🟢 **Low:** informational events

### Report Sections
1. **Executive Summary:** Issue counts by severity, top issues
2. **Recommendations:** Aggregated fixes with occurrence counts
3. **Issues by Severity:** Tables grouped by critical/high/medium
4. **Agent Summary:** Per-persona status, event counts, elapsed time
5. **Agent Details:**
   - Navigation path (URL sequence)
   - Frustration events with descriptions
   - Action history (for LLM mode)
   - Visual evidence (annotated screenshots)

---

## Screenshot Annotation System

### Markers
- **AnnotationMarker dataclass:** x, y, label, color, radius
- **Color mapping by severity:**
  - Critical → Red
  - High → Orange
  - Medium → Yellow
  - Low → Green

### Annotation Process
1. Capture screenshot at each page visit
2. Group frustration events by URL
3. Extract coordinates from events (x, y or target tuple)
4. Draw circle markers with numbered labels
5. Save annotated PNG to `results/screenshots/{run_id}/`

---

## Run Modes

### Heuristic Mode (Default)
- Uses Playwright to navigate and detect friction
- No LLM calls required
- Faster execution (~3-60 seconds per agent)

### LLM Mode
- Vision-based decision making
- LLM analyzes screenshots to decide next action
- Tracks: call count, token usage
- Slower but more human-like navigation

---

## Key Metrics Tracked

- **Total friction events** per run
- **Events per persona**
- **Elapsed time** per agent
- **Navigation depth** (URL count)
- **Event distribution** by type and severity

---

## Test Pages Used

Stress test pages under `/stress/`:
- `/stress/rage-decoy/` - Fake clickable elements
- `/stress/dead-end/` - No navigation options
- `/stress/circular/` - A↔B loop pages
- `/stress/many-links/` - 20+ links to test navigation
- `/stress/long-dwell/` - Terms requiring reading time
- `/stress/slow/` - Artificially slow loading
- `/stress/broken-forms/` - Form validation issues
- `/stress/hidden-menu/` - Discoverable UI patterns
- `/stress/icon-bar/` - Icon-only interfaces
- `/stress/edge-cases/` - Various edge case scenarios

---

## Iteration History

| Run ID | Agents | Events | Notes |
|--------|--------|--------|-------|
| Early runs | 8 | 0 | Playwright not installed errors |
| `15776b16` | 8 | 41 | First successful heuristic run |
| `96d9ef83-heuristic` | 8 | 24 | Heuristic mode comparison |
| `96d9ef83-llm` | 8 | 8 | LLM mode comparison (all gave_up) |
| `04899ec9` | 1 | 32 | Single agent test |
| `09c9960d` | 8 | 297 | Full run with screenshots |
| `a31ac265` | 8 | 331 | Full heuristics run (largest) |

---

## Phase 1 Conclusions

1. **rage_decoy** is the most frequently detected event (~90% of all events)
2. All 8 personas consistently fail their goals (unmet_goal is universal)
3. Circular navigation is common when agents can't find their target
4. Dead ends are reliably detected on pages without interactive elements
5. Screenshot annotation coordinates are captured for rage_decoy events
6. LLM mode agents give up faster than heuristic mode agents
