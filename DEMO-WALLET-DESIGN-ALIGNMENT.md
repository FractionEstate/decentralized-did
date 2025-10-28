# Demo-Wallet Design System Alignment

## Objective
Update the demo-wallet UI to match the presentation's modern, professional design with cyan/purple accents and glassmorphic styling.

## Current Status
- **Presentation:** ✅ Complete with mobile phone frame (Oct 27, 2025)
- **Demo-Wallet:** 🔄 Needs design system alignment

## Design Tokens to Implement

### Colors (from presentation globals.css)
```scss
// Primary Colors
$cardano-blue: #0033AD;        // Primary background
$cardano-cyan: #00D4FF;        // Accent/highlights
$cardano-purple: #7B3FF2;      // Secondary accent

// Backgrounds
$background-primary: linear-gradient(135deg, #0033AD 0%, #1a1a2e 100%);
$background-alt: linear-gradient(to-b, #0f0f1e, #1a1a2e);

// Semantic Colors
$success: #10b981;             // Emerald green
$error: #ef4444;               // Red
$warning: #f59e0b;             // Amber
$info: #3b82f6;                // Blue
```

### Glass-Morphism
```scss
.card-glass {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
}

// Variants
.card-glass-strong {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.card-glass-subtle {
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(5px);
  border: 1px solid rgba(255, 255, 255, 0.05);
}
```

### Typography
```scss
// Gradient text (like presentation)
.gradient-text {
  background: linear-gradient(90deg, #00D4FF, #7B3FF2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

// Glow effect
.glow {
  text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
}
```

## Implementation Roadmap

### Phase 1: Design System (Week 1)
- [ ] Update `design-tokens.scss` with presentation colors
- [ ] Add glass-morphic card styles
- [ ] Implement gradient text utility
- [ ] Create color variables in SCSS

### Phase 2: Core Components (Week 2)
- [ ] Update App.tsx background gradient
- [ ] Redesign Card components with glass-morphism
- [ ] Update Button styles (cyan primary, purple secondary)
- [ ] Implement gradient text in headers

### Phase 3: Page Layouts (Week 3)
- [ ] Update Wallet page layout
- [ ] Redesign Transaction list
- [ ] Update Forms with new input styling
- [ ] Implement QR code display frame

### Phase 4: Mobile Optimization (Week 4)
- [ ] Add safe area insets for notch
- [ ] Optimize touch targets (48px minimum)
- [ ] Implement bottom sheet modals
- [ ] Add status bar theming

### Phase 5: Interactive Elements (Week 5)
- [ ] Add smooth transitions (Framer Motion)
- [ ] Implement hover/active states
- [ ] Add loading animations
- [ ] Create success/error feedback

## File-by-File Changes

### `/src/ui/design-tokens.scss`
```diff
+ Add presentation color variables
+ Add glass-morphism classes
+ Update background gradients
+ Add gradient-text and glow utilities
```

### `/src/ui/App.tsx`
```diff
- background: /* old color */
+ background: linear-gradient(135deg, #0033AD 0%, #1a1a2e 100%);
+ Add className modifications for glass styling
```

### `/src/ui/components/Card.tsx`
```diff
- className="card"
+ className="card card-glass"
+ Add border: 1px solid rgba(255, 255, 255, 0.1)
+ Add backdrop-filter: blur(10px)
```

### `/src/ui/components/Button.tsx`
```diff
- Background: /* old color */
+ Background: #00D4FF (cyan)
+ Hover: #00D4FF with opacity
+ Secondary: #7B3FF2 (purple)
+ Text: black (on cyan), white (on purple)
```

### `/src/ui/pages/WalletPage.tsx`
```diff
+ Apply glass-morphic cards
+ Update transaction list styling
+ Add gradient headers
+ Improve spacing and alignment
```

## Color Application Guide

### Primary Actions
- **Button Background:** Cyan (#00D4FF)
- **Button Text:** Black
- **Button Hover:** Cyan with 80% opacity

### Secondary Actions
- **Button Background:** Purple (#7B3FF2)
- **Button Text:** White
- **Button Hover:** Purple with 80% opacity

### Accents & Highlights
- **Highlights:** Cyan (#00D4FF)
- **Links:** Cyan with glow effect
- **Success:** Emerald green (#10b981)
- **Errors:** Red (#ef4444)

### Backgrounds
- **Page Background:** Blue gradient (0033AD → 1a1a2e)
- **Card Background:** Glass-morphic overlay
- **Input Background:** Transparent with border

## Responsive Breakpoints (align with presentation)

```scss
// Mobile First
$sm: 640px;   // Small phones
$md: 768px;   // Tablets
$lg: 1024px;  // Large tablets
$xl: 1280px;  // Desktops
$2xl: 1536px; // Large desktops

// Apply to demo-wallet components
```

## Motion & Animations

### Transitions
```scss
$transition-fast: 150ms ease-out;
$transition-base: 250ms ease-in-out;
$transition-slow: 350ms ease-in-out;
```

### Examples
- **Card entrance:** Scale 0.95 → 1.0, opacity 0 → 1 (250ms)
- **Button click:** Scale 0.98 → 1.0 (100ms)
- **Loading:** Continuous spin, 1s/rotation
- **Success:** Bounce animation with green pulse

## Validation Checklist

### Visual Design
- [ ] All colors match presentation palette
- [ ] Glass-morphic cards render correctly
- [ ] Gradient text displays without artifacts
- [ ] Typography matches presentation scale
- [ ] Spacing is consistent (8px base unit)

### Responsiveness
- [ ] Mobile (375px) - Clean layout, readable text
- [ ] Tablet (768px) - Balanced spacing
- [ ] Desktop (1024px+) - Professional appearance
- [ ] Landscape orientation - Proper adaptation

### Accessibility
- [ ] Color contrast ≥ 4.5:1 (WCAG AA)
- [ ] Touch targets ≥ 44px
- [ ] Font sizes ≥ 14px mobile
- [ ] Focus states visible

### Performance
- [ ] No CSS layout shifts
- [ ] Animations 60fps
- [ ] Load time < 2s
- [ ] Bundle size impact < 5KB

## Success Metrics

1. **Visual Alignment:** Demo-wallet looks like native app version of presentation
2. **Color Consistency:** All cyan/purple accents match exactly
3. **User Experience:** Smooth animations, responsive at all sizes
4. **Code Quality:** No console warnings, proper TypeScript types
5. **Performance:** Fast load, smooth 60fps animations

## Timeline

- **Phase 1-2:** Oct 28-Nov 3 (2 weeks)
- **Phase 3-4:** Nov 4-17 (2 weeks)
- **Phase 5:** Nov 18-24 (1 week)
- **Testing & QA:** Nov 25-Dec 1 (1 week)
- **Launch Ready:** Dec 2, 2025

## Dependencies
- Framer Motion (already in project)
- SCSS for styling (already in project)
- TailwindCSS for utilities (optional enhancement)
- No new library dependencies needed

---

**Owner:** Design System Implementation Team
**Status:** Planning & Initial Scoping
**Priority:** HIGH - Critical for stage presentation
**Date Created:** October 27, 2025
