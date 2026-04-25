# Flamboyance UX Friction Report

- **Run ID:** `96d9ef83-heuristic`
- **Target URL:** http://localhost:5173
- **Status:** done
- **Agents:** 8
- **Total frustration events:** 24
- **Generated:** 2026-04-25 17:08:13 UTC

## Summary

| Persona | Status | Events | Elapsed |
|---------|--------|--------|---------|
| frustrated_exec | done | 2 | 9.2s |
| non_tech_senior | done | 11 | 60.3s |
| power_user | done | 1 | 43.1s |
| casual_browser | done | 2 | 3.6s |
| anxious_newbie | done | 2 | 4.9s |
| methodical_tester | done | 2 | 4.3s |
| mobile_commuter | done | 2 | 3.2s |
| accessibility_user | done | 2 | 6.0s |

## Agent: frustrated_exec

- **Status:** done
- **Elapsed:** 9.2s

### Navigation Path

1. http://localhost:5173
2. http://localhost:5173/stress/edge-cases/
3. http://localhost:5173/features/premium-dashboard/
4. http://localhost:5173/stress/hidden-menu/
5. http://localhost:5173/
6. http://localhost:5173/order-status/

### Frustration Events

- **dead_end**: Dead end: no clickable elements found on page
- **unmet_goal**: Unmet goal (gave up): Complete a purchase flow quickly

## Agent: non_tech_senior

- **Status:** done
- **Elapsed:** 60.3s

### Navigation Path

1. http://localhost:5173
2. http://localhost:5173/stress/broken-forms/
3. http://localhost:5173/
4. http://localhost:5173/stress/long-dwell/
5. http://localhost:5173/
6. http://localhost:5173/stress/rage-decoy/
7. http://localhost:5173/
8. http://localhost:5173/signup/
9. http://localhost:5173/
10. http://localhost:5173/stress/icon-bar/

### Frustration Events

- **circular_navigation**: Circular navigation detected: http://localhost:5173/ → http://localhost:5173/stress/long-dwell/ → http://localhost:5173/
- **rage_decoy**: Rage decoy: element 'div:has-text('Click to Continue')' looks clickable (cursor:pointer, clickable class name) but is not interactive
- **rage_decoy**: Rage decoy: element 'div:has-text('Submit Order')' looks clickable (cursor:pointer, clickable class name) but is not interactive
- **rage_decoy**: Rage decoy: element 'div:has-text('Delete Item')' looks clickable (cursor:pointer, clickable class name) but is not interactive
- **rage_decoy**: Rage decoy: element 'div:has-text('Special Offer!

Click here to ')' looks clickable (cursor:pointer, clickable class name) but is not interactive
- **rage_decoy**: Rage decoy: element 'p:has-text('Click here to claim your disco')' looks clickable (cursor:pointer) but is not interactive
- **rage_decoy**: Rage decoy: element 'span:has-text('click this link')' looks clickable (cursor:pointer) but is not interactive
- **rage_decoy**: Rage decoy: element 'span:has-text('contact support')' looks clickable (cursor:pointer) but is not interactive
- **circular_navigation**: Circular navigation detected: http://localhost:5173/ → http://localhost:5173/stress/rage-decoy/ → http://localhost:5173/
- **circular_navigation**: Circular navigation detected: http://localhost:5173/ → http://localhost:5173/signup/ → http://localhost:5173/
- **unmet_goal**: Unmet goal (timeout): Find and read account settings

## Agent: power_user

- **Status:** done
- **Elapsed:** 43.1s

### Navigation Path

1. http://localhost:5173
2. http://localhost:5173/stress/many-links/
3. http://localhost:5173/stress/many-links/#item-8
4. http://localhost:5173/stress/many-links/#item-1
5. http://localhost:5173/stress/many-links/#item-5
6. http://localhost:5173/stress/many-links/#item-17
7. http://localhost:5173/stress/many-links/#item-2
8. http://localhost:5173/stress/many-links/#item-1
9. http://localhost:5173/stress/many-links/#item-3
10. http://localhost:5173/stress/many-links/#item-4
11. http://localhost:5173/stress/many-links/#item-7
12. http://localhost:5173/stress/many-links/#item-2
13. http://localhost:5173/stress/many-links/#item-5
14. http://localhost:5173/stress/many-links/#item-11
15. http://localhost:5173/stress/many-links/#item-9
16. http://localhost:5173/stress/many-links/#item-7
17. http://localhost:5173/stress/many-links/#item-18
18. http://localhost:5173/stress/many-links/#item-14
19. http://localhost:5173/stress/many-links/#item-4
20. http://localhost:5173/stress/many-links/#item-20
21. http://localhost:5173/stress/many-links/#item-5
22. http://localhost:5173/stress/many-links/#item-15
23. http://localhost:5173/stress/many-links/#item-17
24. http://localhost:5173/stress/many-links/#item-12
25. http://localhost:5173/stress/many-links/#item-8
26. http://localhost:5173/stress/many-links/#item-13
27. http://localhost:5173/stress/many-links/#item-10
28. http://localhost:5173/stress/many-links/#item-4
29. http://localhost:5173/
30. http://localhost:5173/shop/

### Frustration Events

- **unmet_goal**: Unmet goal (gave up): Navigate all features and check edge cases

## Agent: casual_browser

- **Status:** done
- **Elapsed:** 3.6s

### Navigation Path

1. http://localhost:5173
2. http://localhost:5173/stress/slow/

### Frustration Events

- **dead_end**: Dead end: no clickable elements found on page
- **unmet_goal**: Unmet goal (gave up): Browse around and see what's available

## Agent: anxious_newbie

- **Status:** done
- **Elapsed:** 4.9s

### Navigation Path

1. http://localhost:5173
2. http://localhost:5173/stress/long-dwell/
3. http://localhost:5173/stress/slow/

### Frustration Events

- **dead_end**: Dead end: no clickable elements found on page
- **unmet_goal**: Unmet goal (gave up): Sign up for an account without getting confused

## Agent: methodical_tester

- **Status:** done
- **Elapsed:** 4.3s

### Navigation Path

1. http://localhost:5173
2. http://localhost:5173/stress/long-dwell/
3. http://localhost:5173/stress/slow/

### Frustration Events

- **dead_end**: Dead end: no clickable elements found on page
- **unmet_goal**: Unmet goal (gave up): Systematically check every link and form

## Agent: mobile_commuter

- **Status:** done
- **Elapsed:** 3.2s

### Navigation Path

1. http://localhost:5173
2. http://localhost:5173/order-status/

### Frustration Events

- **dead_end**: Dead end: no clickable elements found on page
- **unmet_goal**: Unmet goal (gave up): Quickly check order status while on the go

## Agent: accessibility_user

- **Status:** done
- **Elapsed:** 6.0s

### Navigation Path

1. http://localhost:5173
2. http://localhost:5173/stress/circular/
3. http://localhost:5173/
4. http://localhost:5173/stress/dead-end/

### Frustration Events

- **dead_end**: Dead end: no clickable elements found on page
- **unmet_goal**: Unmet goal (gave up): Navigate using visible labels and clear affordances
