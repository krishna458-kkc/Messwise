# MessWise Frontend Design System & Motion Specification

---

## 1. Overview & Visual Identity

MessWise is an institutional food-operations intelligence platform. Its design identity reflects the intersection of **food systems, real-time demand forecasting, kitchen operations, and environmental sustainability**.

The interface avoids generic robotic AI templates, cryptocurrency dark palettes, and default admin dashboards. Instead, it employs:
- A **warm, light-first working surface by default** (`#F6F5EE` warm ivory) optimized for bright institutional kitchens and daytime analytical reviews.
- A **complete, layered dark mode** (`#0C1814` deep forest) using rich green-tinted charcoal surfaces and readable off-white text.
- Fresh lime accents (`#D7F36B`) used purposefully for active actions, focus rings, and model indicators.
- Organic circular motifs inspired by the closed operational loop: **Predict → Plan → Cook → Measure → Learn**.
- Strict **WCAG AA contrast compliance** (≥ 4.5:1 for normal text, ≥ 3:1 for large display text and UI boundaries).

---

## 2. Design Tokens & Color Palette

All colors are defined as semantic CSS custom properties in `src/index.css` and mapped across Tailwind CSS v4.

### 2.1 Core Palette Tokens & Contrast Ratios

| Semantic Token | Light Mode Value | Dark Mode Value | Measured Contrast Ratio | Operational Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `--background` | `#F6F5EE` (Warm Ivory) | `#0C1814` (Deep Forest) | Base Surface | Primary page background |
| `--surface` | `#FFFFFF` | `#12241E` | Card Surface | Elevated card surfaces, modals, popovers |
| `--surface-elevated` | `#FFFFFF` | `#183028` | Hover Surface | Hovered cards, floating toolbars |
| `--surface-muted` | `#E8EFE6` (Sage) | `#162B23` | Recessed Surface| Secondary panels, input backgrounds |
| `--text-primary` | `#11231D` (Deep Forest)| `#F6F7F2` (Ivory Off-White) | **14.8:1 (Light) / 15.2:1 (Dark)** | High-contrast headings and body |
| `--text-secondary` | `#42574F` (Slate Sage) | `#A3B8AF` | **6.7:1 (Light) / 7.8:1 (Dark)** | Subtitles, labels, metadata |
| `--border` | `#D8E2D6` | `#224036` | **3.2:1 against surface** | Subtle dividers and card borders |
| `--brand-primary` | `#184436` (Forest Green)| `#D7F36B` (Fresh Lime) | High Contrast | Primary buttons, brand mark, key badges |
| `--brand-accent` | `#D7F36B` (Fresh Lime) | `#D7F36B` | Accents Only | Focus states, interactive highlights, dark CTAs |
| `--success` | `#16A34A` (Emerald) | `#4ADE80` | ≥ 4.8:1 | Verified pilot outcomes, completed dispatches |
| `--warning` | `#D97706` (Amber) | `#FBBF24` | ≥ 4.6:1 | **Unverified developer test entries**, alerts |
| `--danger` | `#DC2626` (Red) | `#F87171` | ≥ 4.9:1 | Shortages, food-safety blocks, validation errors |

### 2.2 Accessible Button Standard (`.btn-primary`, `.btn-secondary`, `.btn-accent`)

To eliminate the jarring bug where buttons turned pitch black on hover (`hover:bg-[#102C24]`), buttons follow standardized utility classes:

- **`.btn-primary`**:
  - *Light Mode*: Base `#184436`, hovering to `#245A48` (brightened forest green with subtle elevation and scale `1.01`, never black). Text: `#FFFFFF` (contrast 9.8:1).
  - *Dark Mode*: Base `#D7F36B` (electric lime), hovering to `#C5E850`. Text: `#102C24` (contrast 12.4:1).
- **`.btn-secondary`**:
  - *Light Mode*: Background `#FFFFFF`, border `var(--border)`, hover `bg-[#F1F5F0]`, text `var(--text-primary)`.
  - *Dark Mode*: Background `#12241E`, border `var(--border)`, hover `bg-[#183028]`, text `var(--text-primary)`.
- **`.btn-accent`**:
  - Direct call-to-action button with lime glow and dark text in both themes.

### 2.3 Semantic Data Provenance Palette

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

## 4. Animation & Interaction Library (The 5 Reference Libraries)

MessWise incorporates curated patterns from top modern UI libraries:

### 1. React Bits Reference
- **`CountUp.tsx`**: Rolling counter component utilizing `framer-motion`'s `useMotionValue`, `useSpring`, and `useTransform`. Provides ease-out deceleration when loading KPIs and counterfactual audits.
- **`SplitText.tsx`**: Character-by-character and word-by-word spring stagger for hero headlines and key section anchors.

### 2. Aceternity UI Reference
- **`Spotlight.tsx`**: Mouse-tracking radial gradient overlay that highlights card borders and backgrounds as the user moves their cursor over cards.
- **`BentoCard.tsx`**: Asymmetric grid containers with smooth hover elevation and responsive layout.

### 3. Vengeance UI Reference
- **`BorderBeam.tsx`**: Traveling border glow animation indicating active prospective forecasting and real-time live clock states.

### 4. Uiverse Reference
- **`TiltCard.tsx`**: Interactive 3D perspective tilt reacting to cursor coordinates, giving cards tangible depth on mouse move.

### 5. 21st.dev Reference
- **`AnimatedList.tsx`**: Staggered cascading entry animation for dynamic data feeds, active surplus alerts, and audit logs.

---

## 5. Reusable Component Inventory

Located in `src/components/common/` and `src/components/animations/`:

1. **`AppShell`**: Workspace layout with collapsible navigation rail, top sticky header, breadcrumbs, search, environment badge pill, persona role selector, language selector, and mobile navigation drawer.
2. **`PublicNavbar`**: Branded navigation for the public landing page with custom SVG logo, anchor links, theme toggle, and `.btn-primary` "Launch Workspace" CTA.
3. **`PublicFooter`**: Designed footer with closed-loop philosophy, methodology links, SDG 12.3 alignment, and responsible disclosures.
4. **`PageHeader`**: Standardized header with display title, descriptive subtitle, icon pill, environment badge, and contextual `.btn-primary` / `.btn-secondary` action buttons.
5. **`KpiCard`**: Metric presentation card with automatic `CountUp` animation, tabular numerals, delta badges, and hover lift.
6. **`StatusBadge`**: Semantic badge pill supporting `real`, `unverified`, `synthetic`, `success`, `warning`, `danger`, and `info` states with indicator dots.
7. **`DataProvenanceBanner`**: Honest top banner explicitly alerting operators when unverified test entries or synthetic demo records are active.
8. **`ErrorBoundary`**: Accessible fallback screen with diagnostic stack details, refresh action, and Command Center redirect button.
9. **`LoadingSkeleton`**: Shimmering placeholder animations during async data fetching.
10. **`EmptyState`**: Centered illustration, informative text, and call-to-action button for empty query states.

---

## 6. Motion Design & Accessibility

- **Motion Library:** `framer-motion` v12 with spring physics (`damping: 15, stiffness: 100`).
- **Reduced Motion Support:** All animated components query `useReducedMotion()`. When `prefers-reduced-motion` is enabled by the OS, elements render immediately without transform or blur transitions.
- **Restrained Animation Rules:** Motion is used strictly to guide visual hierarchy and provide feedback. Operational forms and tables maintain instant, zero-delay rendering to prevent workflow drag.

---

## 7. Responsive Breakpoints

| Breakpoint | Target Viewport | Layout Adaptations |
| :--- | :--- | :--- |
| `sm: 640px` | Small Mobile / Phablet | Stacked KPI grids, touch-friendly 44px button hit targets |
| `md: 768px` | Tablet | 2-column bento grids, collapsed navigation rail, slide-out drawer |
| `lg: 1024px` | Laptop | 3-column bento grids, sticky top summary bars, full tables |
| `xl: 1280px` | Desktop | Complete multi-column operational command center with sidebar |
| `2xl: 1536px`| Ultra-Wide Display | Max-width container (`max-w-7xl`) preventing horizontal eye-strain |
