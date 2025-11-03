# Biovera Wallet UX/UI Audit & Redesign Plan

**Date**: November 3, 2025
**Status**: Critical Issues Identified - Redesign Required
**Priority**: HIGH - Affects User Experience & Adoption

---

## Executive Summary

After comprehensive analysis of the Biovera wallet codebase, **critical UX/UI flaws** have been identified that significantly impact usability, user comprehension, and adoption potential. The wallet suffers from:

1. **Information Architecture Overload** - 8 bottom tabs create cognitive burden
2. **Confusing Terminology** - "Identifiers" tab is unclear for average users
3. **Missing Core Wallet Features** - No clear Send/Receive/Swap functions
4. **Inconsistent Visual Hierarchy** - Poor content structure and spacing
5. **Feature Complexity** - Advanced features (governance, staking, browser) overwhelm core wallet functionality

**Recommendation**: Implement a phased redesign focusing on wallet fundamentals first, then progressive disclosure of advanced features.

---

## 🚨 Critical Issues Identified

### 1. **Navigation Overload - 8 Bottom Tabs**

**Current State**:
```
[Wallet] [Tokens] [Staking] [Governance] [Browser] [Scan] [Notifications] [Settings]
```

**Problems**:
- ❌ **Cognitive overload**: Human short-term memory handles 5-7 items, we have 8
- ❌ **Unclear priorities**: All tabs appear equal, no visual hierarchy
- ❌ **Small touch targets**: 8 tabs means tiny clickable areas on mobile
- ❌ **Feature bloat**: Advanced features (Governance, Staking, Browser) compete with core wallet functions

**User Impact**:
- New users don't know where to start
- Core actions (send, receive) are hidden
- Advanced users confused by feature organization
- High bounce rate expected in onboarding

**Best Practice Comparison**:
- **MetaMask**: 3 tabs (Wallet, Activity, Settings)
- **Coinbase Wallet**: 4 tabs (Home, NFTs, Activity, Settings)
- **Trust Wallet**: 4 tabs (Wallet, NFTs, Browser, Settings)
- **Phantom**: 3 tabs (Home, Collectibles, Settings)

### 2. **Confusing Terminology - "Identifiers" vs "Wallet"**

**Current State**:
```tsx
// First tab labeled "Identifiers" with fingerprint icon
{
  path: TabsRoutePath.IDENTIFIERS,
  component: Identifiers,
  icon: [fingerPrint, fingerPrintOutline],
  i18nKey: "tabsmenu.label.identifiers",
}
```

**Problems**:
- ❌ **Technical jargon**: "Identifiers" is a developer term, not user-facing
- ❌ **Unclear purpose**: Users don't know what "Identifiers" means
- ❌ **Duplicate concepts**: "Identifiers" tab + "Tokens" tab creates confusion
- ❌ **Biometric icon misleading**: Fingerprint suggests biometric auth, not wallet management

**User Impact**:
- First-time users don't understand primary navigation
- Users search for "wallet" or "accounts" and can't find them
- Biometric DID concept is buried in unclear UI

**What Users Expect**:
- "Wallet" or "Home" as primary tab
- "Accounts" or "Assets" for multiple addresses
- Clear visual distinction between identity and assets

### 3. **Missing Core Wallet Actions**

**Current State**: Send/Receive/Swap functions are hidden or non-existent in visible UI

**Problems**:
- ❌ **No prominent Send button** on main screen
- ❌ **No prominent Receive button** for showing address/QR
- ❌ **Scan button relegated to tab** instead of action button
- ❌ **Transaction history buried** under Tokens > History subtab

**User Impact**:
- Users can't figure out how to send ADA
- Users can't quickly receive payments
- Core wallet functionality hidden behind navigation layers

**Expected Behavior** (industry standard):
```
Main Wallet Screen:
┌─────────────────────────┐
│   [Profile]    [QR Scan]│
│                          │
│   Total Balance          │
│   ₳ 1,234.56            │
│                          │
│ [Send]  [Receive]  [Buy] │ ← Primary actions
│                          │
│   Assets                 │
│   ├─ ADA                 │
│   ├─ Token 1             │
│   └─ Token 2             │
│                          │
│   Recent Activity        │
│   ├─ Transaction 1       │
│   └─ Transaction 2       │
└─────────────────────────┘
```

### 4. **Token vs Identifiers Confusion**

**Current State**: Two tabs that seem to overlap:
- Tab 1: "Identifiers" (fingerprint icon) - shows wallet identifiers
- Tab 2: "Tokens" (wallet icon) - shows balance, NFTs, transactions

**Problems**:
- ❌ **Conceptual overlap**: Both deal with wallet content
- ❌ **Split functionality**: Balance in Tokens, but what's in Identifiers?
- ❌ **Inconsistent mental model**: Users expect one unified wallet view

**User Confusion**:
- "Where do I see my balance?" (Tokens tab)
- "Where do I see my wallet?" (Identifiers tab? Tokens tab?)
- "What's the difference between these?"

### 5. **Advanced Features Overwhelm Core Functionality**

**Current State**: Staking, Governance, dApp Browser given equal prominence to core wallet

**Problems**:
- ❌ **Premature feature exposure**: New users see advanced features before understanding basics
- ❌ **No progressive disclosure**: All features visible from day 1
- ❌ **Empty states frequent**: Governance/Staking data often unavailable on testnet
- ❌ **Maintenance burden**: Complex features require ongoing updates

**User Impact**:
- Overwhelmed new users abandon wallet
- Support requests about features they don't need
- Core wallet improvements delayed by feature maintenance

**Progressive Disclosure Pattern** (recommended):
```
Phase 1 (Day 1):      Wallet basics (Send, Receive, View Balance)
Phase 2 (Week 1):     Staking (after user has ADA balance)
Phase 3 (Month 1):    Governance (after user is staking)
Phase 4 (Advanced):   dApp Browser, Multi-sig, etc.
```

### 6. **Poor Visual Hierarchy in Pages**

**Current Issues**:

**Tokens Page** (`src/ui/pages/Tokens/Tokens.tsx`):
```tsx
// Subtabs inside main tab - nested navigation anti-pattern
const [activeTab, setActiveTab] = useState<"balance" | "nfts" | "history">("balance");

// Content sections lack visual hierarchy
<div className="balance-container">
  <div className="ada-balance">...</div>
  <div className="assets-section">...</div>
</div>
```

**Problems**:
- ❌ **Nested tabs**: Tabs within tabs creates confusion
- ❌ **Flat visual hierarchy**: Everything looks equally important
- ❌ **Poor spacing**: Content cramped, hard to scan
- ❌ **No clear focal point**: Eye doesn't know where to look first

**Governance Page** (`src/ui/pages/Governance/Governance.tsx`):
```tsx
// Three subtabs - more nested navigation
<div className="tabs">
  <button>DReps</button>
  <button>Proposals</button>
  <button>My Votes</button>
</div>
```

**Problems**:
- ❌ **Technical terminology**: "DReps" requires explanation
- ❌ **Empty states common**: "Governance data may not be available yet"
- ❌ **No onboarding context**: Users don't know what governance is
- ❌ **Placeholder address hardcoded**: Shows fake data

### 7. **Inconsistent Content & Placeholder Data**

**Examples Found**:

```tsx
// Governance.tsx - Line 18
const DEMO_STAKE_ADDRESS = "stake1ux2fxv2umyhttkxyxp8x0dlpdt3k6cwng5pxj3jhsydzer3qf0000";

// Tokens.tsx - Line 16
const DEMO_ADDRESS = "addr1qx2fxv2umyhttkxyxp8x0dlpdt3k6cwng5pxj3jhsydzer3n0d3vllmyqwsx5wktcd8cc3sq835lu7drv2xwl2wywfgse35a3x";
```

**Problems**:
- ❌ **Hardcoded demo addresses**: Not production-ready
- ❌ **Fake data shown**: Users see fake balances/transactions
- ❌ **Inconsistent states**: Real + fake data mixed
- ❌ **No wallet connection flow**: Missing actual wallet integration

### 8. **Biometric DID Value Proposition Unclear**

**Core Innovation Hidden**:
The wallet's unique selling point (biometric-based DIDs) is buried in technical UI:
- Tab called "Identifiers" doesn't explain biometric DID
- No onboarding explanation of privacy/security benefits
- Biometric enrollment flow exists but not prominently featured
- Users don't understand what makes this wallet different

**Marketing Disconnect**:
- Wallet is called "Biovera" (bio = biometric)
- But biometric features are not visually prominent
- No visual branding around biometric security
- Could be any generic Cardano wallet from UI alone

---

## 📊 Competitive Analysis

### Industry Leaders - Navigation Structure

| Wallet | Main Tabs | Core Actions | Advanced Features |
|--------|-----------|--------------|-------------------|
| **MetaMask** | 3 (Wallet, Activity, Settings) | Send, Receive, Swap (prominent) | Browser, Staking (secondary menu) |
| **Coinbase Wallet** | 4 (Home, NFTs, Activity, Settings) | Send, Receive, Buy (FAB) | dApps, Staking (in-app) |
| **Trust Wallet** | 4 (Wallet, NFTs, Browser, Settings) | Send, Receive, Buy (top bar) | Staking, Swap (in wallet view) |
| **Phantom** | 3 (Home, Collectibles, Settings) | Send, Receive, Swap (cards) | Apps (integrated) |
| **Biovera (Current)** | **8** (Wallet, Tokens, Staking, Gov, Browser, Scan, Notif, Menu) | ❌ Hidden/unclear | ❌ All prominent equally |

### Key Takeaways:
1. **3-4 tabs is optimal** for mobile wallet navigation
2. **Core actions prominently displayed** as buttons/FABs, not tabs
3. **Advanced features progressively disclosed** after onboarding
4. **Clear visual hierarchy** with balance/assets at top

---

## ✅ Recommended Redesign - Phase 1 (Core Wallet)

### New Navigation Structure

**Bottom Navigation (4 tabs)**:
```
┌────────┬────────┬─────────┬──────────┐
│  Home  │  NFTs  │  Scan   │ Settings │
└────────┴────────┴─────────┴──────────┘
```

**Rationale**:
- **Home**: Unified view (balance + assets + transactions)
- **NFTs**: Separate due to visual nature (grid view)
- **Scan**: Quick access to QR scanner (preserved from current)
- **Settings**: Account management, security, advanced features

### Home Screen Redesign

```
┌─────────────────────────────────────┐
│ 👤 John's Wallet       🔔 [3] 📷   │ ← Header
├─────────────────────────────────────┤
│                                     │
│      🪙 Total Balance               │
│      ₳ 1,234.56                    │
│      $2,469.12 USD                 │
│                                     │
│  ┌───────┐  ┌───────┐  ┌───────┐  │
│  │ Send  │  │Receive│  │  Buy  │  │ ← Primary Actions
│  └───────┘  └───────┘  └───────┘  │
│                                     │
│  Your Assets                    ⌄  │ ← Section Header
│  ┌─────────────────────────────┐  │
│  │ ₳ ADA          1,234.56     │  │
│  │ Cardano        $2,469.12    │  │
│  └─────────────────────────────┘  │
│  ┌─────────────────────────────┐  │
│  │ 💎 Token X     100.00       │  │
│  │ Native Token   $50.00       │  │
│  └─────────────────────────────┘  │
│                                     │
│  Recent Activity             View › │
│  ┌─────────────────────────────┐  │
│  │ 📤 Sent to addr1...         │  │
│  │ -50 ₳    2 hours ago        │  │
│  └─────────────────────────────┘  │
│  ┌─────────────────────────────┐  │
│  │ 📥 Received from addr1...   │  │
│  │ +100 ₳   1 day ago          │  │
│  └─────────────────────────────┘  │
│                                     │
│  ⚡ Advanced Features        View › │ ← Progressive Disclosure
│  ┌───┬───┬────┬────┬─────┬─────┐  │
│  │ 💰│ 🏛│ 🌐 │ 🤝 │ 🔗  │ ... │  │
│  │Stak│Gov│dApp│MSig│Conn │More│  │
│  └───┴───┴────┴────┴─────┴─────┘  │
└─────────────────────────────────────┘
```

### File Structure Changes

**Create New Unified Home**:
```
src/ui/pages/Home/
├── Home.tsx                 # Main unified wallet view
├── Home.scss
├── Home.test.tsx
└── components/
    ├── BalanceCard.tsx      # Total balance display
    ├── QuickActions.tsx     # Send/Receive/Buy buttons
    ├── AssetsList.tsx       # Token list
    ├── ActivityFeed.tsx     # Recent transactions
    └── AdvancedFeatures.tsx # Progressive disclosure grid
```

**Simplify Tab Structure**:
```tsx
// src/ui/components/navigation/TabsMenu/TabsMenu.tsx

const tabsRoutesBase: TabConfigBase[] = [
  {
    path: TabsRoutePath.HOME,           // NEW - Unified view
    component: Home,
    icon: [wallet, walletOutline],
    i18nKey: "tabsmenu.label.home",
  },
  {
    path: TabsRoutePath.NFTS,           // Extracted from Tokens
    component: NFTs,
    icon: [images, imagesOutline],
    i18nKey: "tabsmenu.label.nfts",
  },
  {
    path: TabsRoutePath.SCAN,           // KEEP - Quick access
    component: Scan,
    icon: [scan, scanOutline],
    i18nKey: "tabsmenu.label.scan",
  },
  {
    path: TabsRoutePath.SETTINGS,      // RENAMED from Menu
    component: Settings,
    icon: [settings, settingsOutline],
    i18nKey: "tabsmenu.label.settings",
  },
];
```

**Move Advanced Features to Settings**:
```
Settings Page:
├── Account Management
│   ├── Wallets/Addresses
│   ├── Biometric DID
│   └── Security
├── Advanced Features
│   ├── Staking
│   ├── Governance
│   ├── dApp Browser
│   ├── Multi-sig
│   └── Connections
├── Preferences
│   ├── Currency
│   ├── Language
│   └── Notifications
└── About
    ├── Version
    ├── Support
    └── Legal
```

---

## 🎨 Visual Design Improvements

### 1. Typography Hierarchy

**Current Issues**: Flat hierarchy, everything same size

**Recommended Scale**:
```scss
// Typography system
$font-hero: 32px / 700;      // Total balance
$font-h1: 24px / 700;        // Page titles
$font-h2: 20px / 600;        // Section headers
$font-h3: 18px / 600;        // Card titles
$font-body-lg: 16px / 400;   // Primary text
$font-body: 14px / 400;      // Secondary text
$font-caption: 12px / 400;   // Tertiary text
```

**Apply to Home**:
```tsx
<div className="balance-hero">
  {/* font-hero: 32px/700 */}
  <div className="balance-amount">₳ 1,234.56</div>
  {/* font-body-lg: 16px/400 */}
  <div className="balance-usd">$2,469.12 USD</div>
</div>

<div className="section">
  {/* font-h2: 20px/600 */}
  <h2>Your Assets</h2>

  <div className="asset-card">
    {/* font-h3: 18px/600 */}
    <div className="asset-name">ADA</div>
    {/* font-body: 14px/400 */}
    <div className="asset-desc">Cardano</div>
  </div>
</div>
```

### 2. Spacing System

**Current Issues**: Inconsistent spacing, cramped layouts

**Recommended Scale** (8px base):
```scss
$space-xs: 4px;
$space-sm: 8px;
$space-md: 16px;
$space-lg: 24px;
$space-xl: 32px;
$space-xxl: 48px;
```

**Apply Consistently**:
```scss
// Sections
.section {
  margin-bottom: $space-xl; // 32px

  h2 {
    margin-bottom: $space-md; // 16px
  }
}

// Cards
.card {
  padding: $space-lg; // 24px
  margin-bottom: $space-md; // 16px
  border-radius: 12px;
}

// Lists
.list-item {
  padding: $space-md 0; // 16px vertical

  + .list-item {
    border-top: 1px solid $border-color;
  }
}
```

### 3. Color System Enhancement

**Current Issues**: Inconsistent brand colors, poor contrast

**Recommended Palette**:
```scss
// Brand Colors (Biovera = Bio + Vera = Truth)
$primary: #0066FF;        // Vivid blue (trust, tech)
$primary-light: #3385FF;
$primary-dark: #0052CC;

$secondary: #00D4AA;      // Teal (bio, health)
$secondary-light: #33DDB8;
$secondary-dark: #00AA88;

// Semantic Colors
$success: #00C853;
$warning: #FFB300;
$error: #F44336;
$info: #2196F3;

// Neutrals
$text-primary: #1A1A1A;
$text-secondary: #666666;
$text-tertiary: #999999;
$bg-primary: #FFFFFF;
$bg-secondary: #F5F5F5;
$bg-tertiary: #EEEEEE;
$border: #E0E0E0;
```

**Biometric Brand Integration**:
```scss
// Biometric DID branding
$biometric-gradient: linear-gradient(135deg, $primary, $secondary);

.biometric-badge {
  background: $biometric-gradient;
  padding: $space-sm $space-md;
  border-radius: 20px;
  color: white;

  &::before {
    content: "🔒";
    margin-right: $space-xs;
  }
}

.biometric-card {
  border: 2px solid transparent;
  background:
    linear-gradient(white, white) padding-box,
    $biometric-gradient border-box;
}
```

### 4. Component Library

**Create Reusable Components**:

```tsx
// src/ui/components/core/Button/Button.tsx
export type ButtonVariant = 'primary' | 'secondary' | 'tertiary' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  fullWidth?: boolean;
  icon?: string;
  loading?: boolean;
  disabled?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
}

// Usage:
<Button variant="primary" size="lg" fullWidth>
  Send
</Button>
```

```tsx
// src/ui/components/core/Card/Card.tsx
export type CardElevation = 'flat' | 'low' | 'medium' | 'high';

interface CardProps {
  elevation?: CardElevation;
  interactive?: boolean; // Hover effects
  padding?: boolean;
  children: React.ReactNode;
}

// Usage:
<Card elevation="low" interactive>
  <CardHeader>ADA Balance</CardHeader>
  <CardContent>₳ 1,234.56</CardContent>
</Card>
```

---

## 🚀 Implementation Plan

### Phase 1: Navigation Restructure (Week 1)
**Goal**: Reduce from 8 tabs to 4, create unified Home view

**Tasks**:
1. **Create Home Page** (`src/ui/pages/Home/`)
   - [ ] Merge Identifiers + Tokens content
   - [ ] Add balance card component
   - [ ] Add quick actions (Send/Receive/Buy)
   - [ ] Add assets list
   - [ ] Add activity feed
   - [ ] Add advanced features grid

2. **Simplify Tab Navigation**
   - [ ] Update `TabsMenu.tsx` to 4 tabs (Home, NFTs, Scan, Settings)
   - [ ] Update routing in `routes/paths.ts`
   - [ ] Update translations for new tab labels

3. **Move Advanced Features**
   - [ ] Create Settings/AdvancedFeatures section
   - [ ] Move Staking to Settings > Advanced
   - [ ] Move Governance to Settings > Advanced
   - [ ] Move dApp Browser to Settings > Advanced
   - [ ] Keep quick access cards on Home

**Success Criteria**:
- ✅ 4 tabs visible in bottom nav
- ✅ Home shows balance + assets + actions
- ✅ Advanced features accessible but not prominent
- ✅ No broken navigation links

### Phase 2: Visual Design System (Week 2)
**Goal**: Implement consistent typography, spacing, colors

**Tasks**:
1. **Create Design Tokens**
   - [ ] Define typography scale (`src/ui/styles/typography.scss`)
   - [ ] Define spacing scale (`src/ui/styles/spacing.scss`)
   - [ ] Define color palette (`src/ui/styles/colors.scss`)
   - [ ] Create CSS variables for theme

2. **Build Component Library**
   - [ ] Button component (variants, sizes, states)
   - [ ] Card component (elevations, interactive)
   - [ ] Input component (text, number, secure)
   - [ ] Badge component (status, counts)
   - [ ] List component (items, dividers)

3. **Apply to Home Page**
   - [ ] Implement typography hierarchy
   - [ ] Apply spacing system
   - [ ] Use color palette consistently
   - [ ] Add micro-interactions (hover, press)

**Success Criteria**:
- ✅ Design system documented
- ✅ Reusable components created
- ✅ Home page uses design system
- ✅ Visual hierarchy clear

### Phase 3: Core Actions Implementation (Week 3)
**Goal**: Make Send/Receive/Swap prominent and functional

**Tasks**:
1. **Send Flow**
   - [ ] Create Send modal/page (`src/ui/pages/Send/`)
   - [ ] Recipient input (address, contact, QR)
   - [ ] Amount input (ADA, tokens)
   - [ ] Fee estimation
   - [ ] Transaction review
   - [ ] Success confirmation

2. **Receive Flow**
   - [ ] Create Receive modal/page
   - [ ] Display wallet address
   - [ ] Generate QR code
   - [ ] Copy address button
   - [ ] Share options

3. **Transaction History**
   - [ ] Enhanced activity feed on Home
   - [ ] Transaction details page
   - [ ] Filter/search transactions
   - [ ] Export history (CSV)

**Success Criteria**:
- ✅ Users can send ADA in < 3 taps
- ✅ Users can receive (show address) in < 2 taps
- ✅ Transaction history visible on Home
- ✅ All flows tested end-to-end

### Phase 4: Biometric DID Branding (Week 4)
**Goal**: Make biometric identity the clear differentiator

**Tasks**:
1. **Visual Branding**
   - [ ] Biometric gradient theme
   - [ ] Fingerprint iconography (subtle, premium)
   - [ ] "Secured with Biometric ID" badges
   - [ ] Onboarding animations

2. **Feature Prominence**
   - [ ] Biometric enrollment in onboarding
   - [ ] Security status on Home
   - [ ] Biometric DID explanation (educational)
   - [ ] Benefits messaging (privacy, security)

3. **Marketing Integration**
   - [ ] Update app description
   - [ ] Screenshots showing biometric features
   - [ ] In-app tips/tooltips
   - [ ] Feature announcements

**Success Criteria**:
- ✅ Users understand biometric DID value
- ✅ Biometric features visually prominent
- ✅ Brand identity cohesive
- ✅ Competitive differentiation clear

### Phase 5: Polish & Optimization (Week 5)
**Goal**: Refinement, performance, accessibility

**Tasks**:
1. **Performance**
   - [ ] Lazy loading for advanced features
   - [ ] Image optimization
   - [ ] Bundle size reduction
   - [ ] Animation performance

2. **Accessibility**
   - [ ] Screen reader support
   - [ ] Keyboard navigation
   - [ ] High contrast mode
   - [ ] Font size scaling

3. **User Testing**
   - [ ] Usability testing (5-10 users)
   - [ ] Feedback collection
   - [ ] Iteration on issues
   - [ ] Final polish

**Success Criteria**:
- ✅ Page load < 2s
- ✅ WCAG 2.1 AA compliant
- ✅ User testing score > 4.5/5
- ✅ Zero critical bugs

---

## 📏 Success Metrics

### Before Redesign (Current Issues):
- ❌ **Navigation**: 8 tabs (cognitive overload)
- ❌ **User Comprehension**: "Identifiers" tab confusing
- ❌ **Core Actions**: Send/Receive hidden
- ❌ **Feature Hierarchy**: Advanced features too prominent
- ❌ **Visual Clarity**: Flat hierarchy, poor spacing

### After Redesign (Target Goals):
- ✅ **Navigation**: 4 tabs (industry standard)
- ✅ **User Comprehension**: "Home" = clear primary action
- ✅ **Core Actions**: Send/Receive visible in < 2 taps
- ✅ **Feature Hierarchy**: Progressive disclosure implemented
- ✅ **Visual Clarity**: Clear typography/spacing hierarchy

### KPIs to Track:
- **Time to Complete Send**: Target < 30 seconds (from Home)
- **Onboarding Completion**: Target > 80% (vs current unknown)
- **Feature Discovery**: Users find staking/governance organically
- **Support Tickets**: Reduce "how do I send" by 90%
- **User Satisfaction**: Net Promoter Score (NPS) > 50

---

## 🔧 Technical Implementation Notes

### 1. Backward Compatibility

**Migration Strategy**:
```tsx
// Old route redirects
// src/routes/index.tsx

// Redirect old Identifiers tab to new Home
<Route
  path="/tabs/identifiers"
  render={() => <Redirect to="/tabs/home" />}
/>

// Keep Tokens route for deep links, redirect to Home
<Route
  path="/tabs/tokens"
  render={() => <Redirect to="/tabs/home" />}
/>
```

### 2. Feature Flags

**Gradual Rollout**:
```tsx
// src/config/featureFlags.ts

export const FeatureFlags = {
  NEW_HOME_PAGE: true,           // Phase 1
  NEW_NAVIGATION: true,          // Phase 1
  ADVANCED_FEATURES_SETTINGS: true, // Phase 1
  BIOMETRIC_BRANDING: false,     // Phase 4 (coming soon)
  HARDWARE_WALLET_INTEGRATION: false, // Phase 3 of CIP-30 roadmap
};

// Usage:
{FeatureFlags.NEW_HOME_PAGE ? <Home /> : <Identifiers />}
```

### 3. Analytics Integration

**Track User Behavior**:
```tsx
// src/core/analytics/events.ts

export enum AnalyticsEvent {
  HOME_VIEW = 'home_view',
  SEND_INITIATED = 'send_initiated',
  RECEIVE_VIEWED = 'receive_viewed',
  ADVANCED_FEATURE_ACCESSED = 'advanced_feature_accessed',
}

// Track navigation changes
analytics.track(AnalyticsEvent.HOME_VIEW, {
  source: 'tab_navigation',
  timestamp: Date.now(),
});
```

---

## 📚 Resources & References

### Design Systems for Inspiration:
- **Material Design 3**: https://m3.material.io/
- **Ant Design**: https://ant.design/
- **Polaris (Shopify)**: https://polaris.shopify.com/
- **Lightning Design System**: https://www.lightningdesignsystem.com/

### Wallet UX Best Practices:
- **Consensys Design**: https://consensys.net/diligence/
- **WalletConnect UX**: https://docs.walletconnect.com/
- **CNCF Wallet UX**: https://www.cncf.io/blog/

### Cardano Community Standards:
- **CIP-30**: Cardano dApp Connector Standard
- **CIP-95**: Web-Wallet Bridge - Governance
- **Cardano Foundation**: Wallet certification requirements

---

## 🎯 Next Steps

1. **Review & Approve** this redesign plan with stakeholders
2. **Prioritize Phases** - Can compress timeline if needed
3. **Assign Resources** - Design + Frontend + UX testing
4. **Create Design Mockups** - High-fidelity prototypes in Figma
5. **User Testing** - Validate assumptions before build
6. **Begin Phase 1** - Navigation restructure (highest impact)

**Critical Path**:
```
Week 1: Navigation (4 tabs, Home page)
Week 2: Design system (typography, spacing, colors)
Week 3: Core actions (Send/Receive/Swap)
Week 4: Biometric branding
Week 5: Polish & testing
```

**Total Timeline**: 5 weeks for complete redesign
**Can Start**: Immediately (Phase 1 work can begin today)

---

**Last Updated**: November 3, 2025
**Next Review**: After Phase 1 completion (target: November 10, 2025)
**Questions/Feedback**: Document in GitHub Issues with `ux-redesign` label
