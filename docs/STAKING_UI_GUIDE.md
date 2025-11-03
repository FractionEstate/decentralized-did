# Phase 2: Staking Module - UI Implementation Guide

## Overview
Phase 2 adds comprehensive Cardano staking functionality with a user-friendly interface for managing stake accounts, selecting pools, and tracking rewards.

---

## UI Components Implemented

### 1. Navigation Tab
**Location**: Bottom tab bar  
**Icon**: Trophy (🏆)  
**Label**: "Staking"  
**Route**: `/tabs/staking`

The Staking tab is positioned between Tokens and Scan tabs, providing easy access to staking features.

---

### 2. Staking Page Layout

The Staking page features a **3-tab interface** with pull-to-refresh:

```
┌─────────────────────────────────────┐
│          Staking                    │ ← Page Header
├─────────────────────────────────────┤
│ [Account] [Pools] [Rewards]         │ ← Tab Navigation
├─────────────────────────────────────┤
│                                     │
│      Content Area                   │
│      (varies by tab)                │
│                                     │
└─────────────────────────────────────┘
```

---

### 3. Account Tab

**Purpose**: Display stake account status, balance, and delegation info

**Layout**:
```
┌─────────────────────────────────────┐
│  Status              [Registered]   │ ← Status Badge
├─────────────────────────────────────┤
│  Total Balance      Available      │
│  10.5 ₳             0.25 ₳         │ ← Balance Display
├─────────────────────────────────────┤
│  Delegated To:                     │
│  pool1pu5jlj4q9w9...               │ ← Pool ID (truncated)
└─────────────────────────────────────┘
```

**Features**:
- **Status Badge**: Green for "registered", gray for "not registered"
- **Balance Grid**: Two-column layout showing total balance and rewards
- **Delegation Info**: Shows currently delegated pool (if any)
- **Delegate Button**: Appears when not delegated, links to pool selection

**Color Coding**:
- Total Balance: Primary color (blue)
- Rewards: Success color (green)
- Status: Green (registered) / Gray (not registered)

---

### 4. Pools Tab

**Purpose**: Browse and select stake pools with key metrics

**Pool Card Layout**:
```
┌─────────────────────────────────────┐
│ POOL1          [4.50% APY]         │ ← Ticker + APY Badge
│ Test Stake Pool                    │ ← Pool Name
├─────────────────────────────────────┤
│ Stake: 50.23M ₳  Margin: 2.00%    │
│ Saturation: 65.50%                 │ ← Metrics Grid
├─────────────────────────────────────┤
│ 1,234 blocks • 567 delegators      │ ← Stats
└─────────────────────────────────────┘
```

**Features**:
- **Pool List**: Displays top 10 active pools
- **APY Badge**: Green badge showing estimated annual percentage yield
- **Metrics Grid**: 3-column layout for key pool data
- **Saturation Indicator**: Color-coded based on saturation level:
  - Green: < 60% (healthy)
  - Orange: 60-80% (moderate)
  - Yellow: 80-95% (high)
  - Red: > 95% (oversaturated)

**Metrics Displayed**:
1. **Active Stake**: Total ADA delegated (in millions)
2. **Margin**: Pool operator fee percentage
3. **Saturation**: Current pool saturation vs. network cap
4. **Blocks Minted**: Lifetime blocks produced
5. **Delegators**: Current number of delegators

---

### 5. Rewards Tab

**Purpose**: Show historical staking rewards by epoch

**Reward Item Layout**:
```
┌─────────────────────────────────────┐
│ Epoch 400              2.50 ₳      │ ← Epoch + Amount
│ Earned in epoch 398 • Nov 3, 2025  │ ← Details
├─────────────────────────────────────┤
│ Epoch 399              2.40 ₳      │
│ Earned in epoch 397 • Oct 29, 2025 │
└─────────────────────────────────────┘
```

**Features**:
- **Epoch Display**: Clear epoch number for each reward
- **Reward Amount**: Bold green text showing ADA earned
- **Earned Epoch**: Shows when reward was actually earned (2 epochs prior)
- **Date Formatting**: Approximate date calculated from epoch (~5 days/epoch)
- **Scrollable List**: Most recent rewards first

**Color Coding**:
- Reward amounts: Success color (green)
- Dates and details: Medium gray

---

## Mobile Responsiveness

All components are designed **mobile-first**:

1. **Touch-Friendly**: Large tap targets (44x44pt minimum)
2. **Responsive Grid**: Pool cards adapt to screen width
3. **Pull-to-Refresh**: Native iOS/Android gesture support
4. **Loading States**: Skeleton screens during data fetch
5. **Error Handling**: Clear error messages with retry options

---

## Color System

Following Ionic color variables:

- **Primary**: `--ion-color-primary` (blue) - Main actions, balances
- **Success**: `--ion-color-success` (green) - Rewards, healthy pools, APY
- **Warning**: `--ion-color-warning` (orange) - Moderate saturation
- **Danger**: `--ion-color-danger` (red) - Oversaturated pools
- **Medium**: `--ion-color-medium` (gray) - Labels, secondary text
- **Light**: `--ion-color-light` (light gray) - Card backgrounds

---

## Typography

- **Headers**: 18-20px, bold
- **Body Text**: 14-16px, regular
- **Labels**: 11-12px, medium weight, gray
- **Monospace**: Pool IDs, transaction hashes

---

## Interactions

1. **Tab Switching**: Instant content swap, active tab highlighted
2. **Pull-to-Refresh**: Reloads all staking data
3. **Pool Cards**: Tap to view full details (future: delegation flow)
4. **Delegate Button**: Navigates to pool selection (future implementation)
5. **Loading States**: Spinner or "Loading..." text during API calls

---

## Error States

**Account Not Found**:
```
┌─────────────────────────────────────┐
│  ⚠️  No account data available      │
│                                     │
│  This stake address may not be      │
│  registered yet.                    │
└─────────────────────────────────────┘
```

**Network Error**:
```
┌─────────────────────────────────────┐
│  ❌  Failed to load staking data    │
│                                     │
│  Please check your connection       │
│  and try again.                     │
└─────────────────────────────────────┘
```

---

## Future Enhancements (Phases 3-6)

1. **Delegation Flow**: Complete stake delegation transaction builder
2. **Pool Details Page**: Full pool information with performance charts
3. **Rewards Charts**: Visual representation of reward history
4. **Pool Search/Filter**: Find pools by ticker, APY, saturation
5. **Multi-Account**: Support for multiple stake addresses
6. **CIP-30 Integration**: Sign delegation transactions in-app

---

## Technical Implementation

**Stack**:
- React + Ionic for UI components
- Redux Toolkit for state management
- TypeScript for type safety
- SCSS for styling

**API Integration**:
- Backend: Python FastAPI + Koios REST API
- Frontend: Fetch API with AbortSignal timeouts
- Caching: 5-minute TTL via Koios client

**Performance**:
- Lazy loading of components
- Async data fetching
- Optimized re-renders with React.memo (when needed)
- Efficient Redux selectors

---

## Testing

**Current Status**:
- ✅ Backend: 20 unit tests (100% passing)
- ⏳ Frontend: Component tests pending

**Test Coverage Needed**:
1. Redux async thunks
2. Component rendering
3. User interactions (tab switching, refresh)
4. Error state handling
5. Loading state transitions

---

*This UI implementation provides a solid foundation for Cardano staking features. The modular design allows for easy extension in future phases.*
