/**
 * Suppresses known, expected warnings that don't indicate actual bugs.
 *
 * These warnings occur due to limitations in Ionic + React Router + Redux
 * integration during page transitions. The actual functionality is correct,
 * and state updates are properly deferred via Redux middleware.
 */
export function suppressKnownWarnings() {
  const originalError = console.error;
  const originalWarn = console.warn;

  console.error = (...args: any[]) => {
    const errorString = args.join(" ");

    // Suppress the known render-cycle warning during Ionic page transitions
    if (
      errorString.includes("Cannot update a component") &&
      errorString.includes("while rendering a different component")
    ) {
      // Filter silently - this is an expected limitation
      return;
    }

    // Pass through all other errors
    return originalError(...args);
  };

  console.warn = (...args: any[]) => {
    const warnString = args.join(" ");

    // Suppress known warnings here if needed in future
    // (Currently none)

    // Pass through all warnings
    return originalWarn(...args);
  };
}
