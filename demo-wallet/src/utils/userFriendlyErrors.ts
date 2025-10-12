/**
 * User-Friendly Error Messages
 *
 * Converts technical error messages into simple, actionable user feedback
 */

export interface UserError {
  title: string;
  message: string;
  action?: string;
  type: 'error' | 'warning' | 'info';
}

/**
 * Convert technical error to user-friendly message
 */
export function getUserFriendlyError(error: any): UserError {
  const errorStr = String(error?.message || error || 'Unknown error');
  const lowerError = errorStr.toLowerCase();

  // Network errors
  if (lowerError.includes('network') || lowerError.includes('fetch') || lowerError.includes('connection')) {
    return {
      title: '⚠️ Connection Issue',
      message: 'Please check your internet connection and try again.',
      action: 'Retry',
      type: 'error',
    };
  }

  // API errors
  if (lowerError.includes('500') || lowerError.includes('internal server')) {
    return {
      title: '⚠️ Server Error',
      message: 'Something went wrong on our end. Please try again in a moment.',
      action: 'Retry',
      type: 'error',
    };
  }

  if (lowerError.includes('404') || lowerError.includes('not found')) {
    return {
      title: '⚠️ Not Found',
      message: 'We couldn\'t find what you\'re looking for.',
      type: 'warning',
    };
  }

  if (lowerError.includes('401') || lowerError.includes('unauthorized') || lowerError.includes('authentication')) {
    return {
      title: '🔒 Authentication Required',
      message: 'Please verify your identity to continue.',
      action: 'Verify',
      type: 'warning',
    };
  }

  if (lowerError.includes('403') || lowerError.includes('forbidden')) {
    return {
      title: '🔒 Access Denied',
      message: 'You don\'t have permission to do this.',
      type: 'error',
    };
  }

  if (lowerError.includes('400') || lowerError.includes('bad request')) {
    return {
      title: '⚠️ Invalid Request',
      message: 'Please check your information and try again.',
      action: 'Check',
      type: 'warning',
    };
  }

  if (lowerError.includes('timeout')) {
    return {
      title: '⏱️ Request Timeout',
      message: 'This is taking longer than expected. Please try again.',
      action: 'Retry',
      type: 'warning',
    };
  }

  // Biometric errors
  if (lowerError.includes('biometric') || lowerError.includes('fingerprint')) {
    if (lowerError.includes('quality') || lowerError.includes('low')) {
      return {
        title: '👆 Try Again',
        message: 'Please place your finger firmly on the sensor.',
        action: 'Retry Scan',
        type: 'warning',
      };
    }
    if (lowerError.includes('match') || lowerError.includes('verify')) {
      return {
        title: '❌ Fingerprint Mismatch',
        message: 'Your fingerprint doesn\'t match. Please try again.',
        action: 'Retry',
        type: 'error',
      };
    }
    return {
      title: '👆 Fingerprint Error',
      message: 'Couldn\'t read your fingerprint. Please try again.',
      action: 'Retry',
      type: 'warning',
    };
  }

  // Wallet errors
  if (lowerError.includes('wallet')) {
    if (lowerError.includes('balance') || lowerError.includes('insufficient')) {
      return {
        title: '💰 Insufficient Funds',
        message: 'You don\'t have enough funds for this transaction.',
        type: 'warning',
      };
    }
    if (lowerError.includes('address')) {
      return {
        title: '⚠️ Invalid Address',
        message: 'Please check the wallet address and try again.',
        action: 'Check Address',
        type: 'warning',
      };
    }
  }

  // Seed phrase errors
  if (lowerError.includes('seed') || lowerError.includes('phrase')) {
    return {
      title: '⚠️ Seed Phrase Error',
      message: 'Please check your seed phrase words are correct.',
      action: 'Check Words',
      type: 'warning',
    };
  }

  // DID errors
  if (lowerError.includes('did')) {
    return {
      title: '🆔 Identity Error',
      message: 'Couldn\'t verify your digital identity. Please try again.',
      action: 'Retry',
      type: 'error',
    };
  }

  // Generic fallback
  return {
    title: '⚠️ Something Went Wrong',
    message: 'Please try again. If the problem persists, contact support.',
    action: 'Retry',
    type: 'error',
  };
}

/**
 * Get simple error message for toast/alert
 */
export function getSimpleErrorMessage(error: any): string {
  const userError = getUserFriendlyError(error);
  return userError.message;
}

/**
 * Common user-friendly terms
 */
export const USER_FRIENDLY_TERMS = {
  // Technical → Simple
  did: 'Digital ID',
  identifier: 'Wallet ID',
  credential: 'Card',
  verification: 'Confirmation',
  template: 'Fingerprint',
  helper_data: 'Security Key',
  biometric_data: 'Your Fingerprint',
  seed_phrase: 'Recovery Words',
  mnemonic: 'Recovery Phrase',
  private_key: 'Secret Key',
  public_key: 'Wallet Address',
  transaction: 'Payment',
  blockchain: 'Network',
  consensus: 'Agreement',
  node: 'Server',

  // Actions
  verify: 'Confirm',
  authenticate: 'Verify',
  authorize: 'Approve',
  sign: 'Confirm',
  broadcast: 'Send',

  // Status
  pending: 'In Progress',
  confirmed: 'Complete',
  failed: 'Unsuccessful',
  success: 'Successful',
};

/**
 * Replace technical terms in text
 */
export function simplifyText(text: string): string {
  let simplified = text;

  Object.entries(USER_FRIENDLY_TERMS).forEach(([technical, simple]) => {
    const regex = new RegExp(`\\b${technical}\\b`, 'gi');
    simplified = simplified.replace(regex, simple);
  });

  return simplified;
}

/**
 * Log error for debugging (while showing user-friendly message to user)
 */
export function logError(error: any, context?: string): void {
  if (process.env.NODE_ENV === 'development') {
    console.error(`[Error${context ? ` in ${context}` : ''}]:`, error);
    if (error?.stack) {
      console.error('Stack trace:', error.stack);
    }
  }

  // TODO: Send to error tracking service (Sentry, etc.)
  // trackError(error, context);
}

/**
 * Helper to show toast with user-friendly error (works with Ionic useIonToast)
 */
export function showErrorToast(
  error: any,
  showToast: (options: any) => Promise<void>,
  context?: string
): void {
  const userError = getUserFriendlyError(error);

  showToast({
    message: `${userError.title}\n${userError.message}`,
    duration: 4000,
    position: 'top',
    color: userError.type === 'error' ? 'danger' : 'warning',
    buttons: [
      {
        text: 'Dismiss',
        role: 'cancel',
      },
    ],
  });

  logError(error, context);
}

/**
 * Success messages
 */
export const SUCCESS_MESSAGES = {
  // Biometric
  biometric_enrolled: '✓ Fingerprint saved successfully!',
  biometric_verified: '✓ Identity confirmed!',

  // Wallet
  wallet_created: '✓ Wallet created successfully!',
  transaction_sent: '✓ Payment sent!',
  transaction_confirmed: '✓ Payment confirmed!',

  // General
  saved: '✓ Saved successfully!',
  copied: '✓ Copied to clipboard!',
  updated: '✓ Updated successfully!',
  deleted: '✓ Deleted successfully!',

  // Onboarding
  onboarding_complete: '🎉 You\'re all set! Welcome!',
  seed_phrase_saved: '✓ Recovery words saved!',
  security_setup: '✓ Security setup complete!',
};

/**
 * Loading messages
 */
export const LOADING_MESSAGES = {
  // Biometric
  scanning: 'Scanning fingerprint...',
  verifying: 'Verifying identity...',

  // Wallet
  creating_wallet: 'Creating your wallet...',
  sending: 'Sending payment...',
  loading_wallet: 'Loading wallet...',

  // General
  loading: 'Loading...',
  saving: 'Saving...',
  processing: 'Processing...',
};
