# MessWise Frontend Design System & Motion Specification

---

## 1. Overview & Visual Identity

MessWise is an institutional food-operations intelligence platform. Its design identity reflects the intersection of **food systems, real-time demand forecasting, kitchen operations, and environmental sustainability**.

The interface avoids generic robotic AI templates, cryptocurrency dark palettes, and default admin dashboards. Instead, it employs:
- A **warm, light-first working surface by default** (`#F6F5EE` warm ivory) optimized for bright institutional kitchens and daytime analytical reviews.
- A **complete, layered dark mode** (`#0B1914` forest-black) using deep green surfaces and readable off-white text.
- Fresh lime accents (`#D7F36B`) used purposefully for active actions, focus rings, and model indicators.
- Organic circular motifs inspired by the closed operational loop: **Predict → Plan → Cook → Measure → Learn**.

---

## 2. Design Tokens & Color Palette

All colors are defined as semantic CSS custom properties in `src/index.css` and mapped across Tailwind CSS v4.

### 2.1 Core Palette Tokens

| Semantic Token | Light Mode Value | Dark Mode Value | Operational Purpose |
| :--- | :--- | :--- | :--- |
| `--background` | `#F6F5EE` (Warm Ivory) | `#0B1914` (Deep Forest) | Primary page background |
| `--surface` | `#FFFFFF` | `#12241E` | Card surfaces, modals, popovers |
| `--surface-elevated` | `#FFFFFF` | `#183028` | Hovered cards, floating toolbars |
| `--surface-muted` | `#E7EEE5` (Sage) | `#162B23` | Secondary panels, input backgrounds |
| `--text-primary` | `#102C24` (Forest Black)| `#F6F5EE` (Ivory Off-White) | High-contrast headings and body |
| `--text-secondary` | `#4A5D53` (Slate Sage) | `#9DB0A6` | Subtitles, labels, metadata |
| `--border` | `#DFE7DD` | `#224036` | Subtle dividers and card borders |
| `--brand-primary` | `#173D32` (Forest Green)| `#D7F36B` (Fresh Lime) | Primary buttons, brand mark, key badges |
| `--brand-accent` | `#D7F36B` (Fresh Lime) | `#D7F36B` | Focus states, interactive highlights |
| `--success` | `#16A34A` (Emerald) | `#4ADE80` | Verified pilot outcomes, completed dispatches |
| `--warning` | `#D97706` (Amber) | `#FBBF24` | **Unverified developer test entries**, alerts |
| `--danger` | `#DC2626` (Red) | `#F87171` | Shortages, food-safety blocks, validation errors |

### 2.2 Semantic Data Provenance Palette

- **Verified Operational Pilot:** Emerald (`#16A34A` / `#4ADE80`) — applied **strictly** when `verification_status == 'verified_pilot'`.
- **Unverified Test Entries (Non-Pilot):** Amber (`#D97706` / `#FBBF24`) — applied to manual entries (`is_synthetic == 0`) that lack supervisory verification.
- **Synthetic Benchmark Demonstration:** Violet (`#7C3AED` / `#A78BFA`) — applied to synthetic onboarding datasets (`is_synthetic == 1`).

---

## 3. Typography System

The typography pairs editorial display fonts with high-legibility tabular workhorses:
- **Headings & Display Typography:** `Sora`, `Outfit`, sans-serif. Letter spacing: `-0.02em`. Used for landing page hero, section titles, and page headers.
- **Body & Operational Data:** `Inter`, `DM Sans`, system-ui. Optimized for dense tables, forms, and kitchen touch targets.
- **Numbers & KPI Values:** Tabular numerals enabled (`tabular-nums`) across all forecast intervals, kilograms, percentages, and timestamps to eliminate layout jitter.

---

## 4. Reusable Component Inventory

Located in `src/components/common/`:

1. **`AppShell`**: Workspace layout with collapsible navigation rail, top sticky header, breadcrumbs, search, environment badge pill, persona role selector, language selector, and mobile navigation drawer.
2. **`PublicNavbar`**: Branded navigation for the public landing page with custom SVG logo, anchor links, theme toggle, and "Launch Workspace" CTA.
3. **`PublicFooter`**: Designed footer with closed-loop philosophy, methodology links, SDG 12.3 alignment, and responsible disclosures.
4. **`PageHeader`**: Standardized header with display title, descriptive subtitle, icon pill, environment badge, and contextual action buttons.
5. **`KpiCard`**: Metric presentation card with count-up animation, tabular numerals, delta badges, and hover lift.
6. **`StatusBadge`**: Semantic badge pill supporting `real`, `unverified`, `synthetic`, `success`, `warning`, `danger`, and `info` states with indicator dots.
7. **`DataProvenanceBanner`**: Honest top banner explicitly alerting operators when unverified test entries or synthetic demo records are active.
8. **`BentoCard`**: Asymmetric card container with pointer spotlight ambient glow (inspired by Aceternity UI).
9. **`StaggerText`**: Word-by-word motion entrance for headlines and section markers with spring physics.
10. **`LoadingSkeleton`**: Shimmering placeholder animations during async data fetching.
11. **`EmptyState`**: Centered illustration, informative text, and call-to-action button for empty query states.

---

## 5. Motion Design & Accessibility

- **Motion Library:** `framer-motion` v12 with spring physics (`damping: 15, stiffness: 100`).
- **Reduced Motion Support:** All animated components query `useReducedMotion()`. When `prefers-reduced-motion` is enabled by the OS, elements render immediately without transform or blur transitions.
- **Restrained Animation Rules:** Motion is used strictly to guide visual hierarchy and provide feedback. Operational forms and tables maintain instant, zero-delay rendering to prevent workflow drag.

---

## 6. Responsive Breakpoints

| Breakpoint | Target Viewport | Layout Adaptations |
| :--- | :--- | :--- |
| `sm: 640px` | Small Mobile / Phablet | Stacked KPI grids, touch-friendly 44px button hit targets |
| `md: 768px` | Tablet | 2-column bento grids, collapsed navigation rail, slide-out drawer |
| `lg: 1024px` | Laptop | 3-column bento grids, sticky top summary bars, full tables |
| `xl: 1280px` | Desktop | Complete multi-column operational command center with sidebar |
| `2xl: 1536px`| Ultra-Wide Display | Max-width container (`max-w-7xl`) preventing horizontal eye-strain |

---

## 7. How to Extend the Design System

1. Always use semantic CSS variables (`var(--surface)`, `var(--text-primary)`, `var(--border)`) rather than hard-coded hex colors.
2. Ensure every new metric card wraps numerical values with `tabular-nums`.
3. Include both light mode and dark mode styling (`dark:...`) for all new components.
4. Guard all data displays with the active data provenance tier (`isSynthetic`, `isVerifiedPilot`, `isUnverifiedTest`).
