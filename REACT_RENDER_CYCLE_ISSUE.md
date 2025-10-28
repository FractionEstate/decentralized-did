# React Render Cycle Conflict - Investigation & Status

## Problem Summary

The app displays only a blue background with no UI components. Console shows:
```
Warning: Cannot update a component (`SidePage`) while rendering a different component (`TabsMenu`)
```

## Root Cause Analysis

### Component Render Order Issue
1. **App.tsx** renders:
   - `AppWrapper` wrapper
   - `Routes` component (contains `TabsMenu`)
   - `SidePage` component (at same level as Routes)

2. **Routes component flow**:
   - Routes reads Redux state: `const routes = useAppSelector(getRoutes)`
   - On first load, `routes` is empty array `[]`
   - Routes useEffect dispatches: `dispatch(setCurrentRoute({ path: nextPath }))`
   - This updates Redux state

3. **SidePage component reacts**:
   - SidePage also watches Redux state
   - When Redux changes from Routes' dispatch, SidePage's useEffect triggers
   - SidePage calls `setState` (setOpenSidePage)
   - React detects that SidePage is updating state WHILE TabsMenu is still rendering
   - Error: "Cannot update a component (SidePage) while rendering (TabsMenu)"

### Why useLayoutEffect Doesn't Help
- `useLayoutEffect` runs synchronously, but AFTER render phase completes
- Ionic's routing layer (ViewLifeCycleManager, IonRouterOutlet) has its own component lifecycle
- These Ionic components interfere with React's normal render cycle handling
- Even synchronous updates trigger Ionic's internal re-renders, causing conflicts

### Why useEffect with Promise.resolve() Doesn't Help
- Promise.resolve() defers to next microtask
- But React's render cycle has already started
- The deferred dispatch still happens during React's commit phase
- This still triggers SidePage's updates while TabsMenu is rendering

## Files Affected

- `demo-wallet/src/routes/index.tsx` - Routes component
- `demo-wallet/src/ui/components/SidePage/SidePage.tsx` - SidePage component
- `demo-wallet/src/ui/App.tsx` - App root component
- `demo-wallet/src/store/reducers/stateCache/stateCache.ts` - Redux store

## Attempted Fixes (All Failed)

1. ✗ `useLayoutEffect` - Still conflicts with Ionic routing
2. ✗ `Promise.resolve().then()` - Deferred too late
3. ✗ `startTransition()` - Non-blocking updates still trigger errors
4. ✗ Removing `ErrorBoundary` - App still fails to render
5. ✗ Disabling `StrictMode` - Warnings still appear and prevent render

## Proper Solution Requires

### Option 1: Separate Initialization Logic (Recommended)
- Move Routes initialization OUT of React render cycle
- Initialize routes in Redux store or middleware BEFORE app renders
- Ensure `routes` array is never empty on first render
- Prevents the `if (!routes.length)` dispatch that triggers conflicts

### Option 2: Prevent Redux State Updates During Render
- Wrap dispatch in custom middleware
- Detect if called during React render phase
- Defer dispatch to next event loop cycle
- Requires deeper integration with React internals

### Option 3: Refactor Component Architecture
- Remove SidePage from same level as Routes
- Create wrapper components to isolate state updates
- Use Portal or Suspense boundaries
- Better separation of concerns

### Option 4: Disable React Strict Mode in Production
- Strict Mode amplifies render cycle warnings
- Comment out `<StrictMode>` wrapper
- Not recommended - hides underlying issues

## Current Status

- **App Status**: ✗ Not rendering (blue background only)
- **React Errors**: ✗ Render cycle conflicts prevent render
- **Build Status**: ✓ Webpack compiles successfully
- **Dev Server**: ✓ Running on localhost:3003

## Next Steps

1. Implement Option 1 (Separate Initialization Logic)
   - Initialize routes in Redux initial state
   - Or use Redux middleware to handle initialization
   - Verify `routes` has default value on first render

2. Test that Routes component doesn't need to dispatch `setCurrentRoute`

3. Verify SidePage doesn't conflict with initial TabsMenu render

4. Test full app flow with UI components visible

## Technical Notes

- This is a specific conflict between React's render cycle and Ionic's component lifecycle
- Similar issues have been reported in React + Ionic frameworks
- The proper fix requires synchronizing initialization BEFORE any render cycles begin
- Cannot be solved purely with useEffect/useLayoutEffect timing

