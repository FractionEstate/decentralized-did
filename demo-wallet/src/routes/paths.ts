enum RoutePath {
  ROOT = "/",
  ONBOARDING = "/onboarding",
  SET_PASSCODE = "/setpasscode",
  GENERATE_SEED_PHRASE = "/generateseedphrase",
  VERIFY_SEED_PHRASE = "/verifyseedphrase",
  DEFERRED_BACKUP = "/deferredbackup",
  TABS_MENU = "/tabs",
  CREATE_PASSWORD = "/createpassword",
  SSI_AGENT = "/ssiagent",
  CONNECTION_DETAILS = "/connectiondetails",
  VERIFY_RECOVERY_SEED_PHRASE = "/verifyrecoveryseedphrase",
  SETUP_BIOMETRICS = "/setup-biometrics",
  BIOMETRIC_ENROLLMENT = "/biometric-enrollment",
}

enum TabsRoutePath {
  ROOT = "/tabs",
  HOME = "/tabs/home",
  IDENTIFIERS = "/tabs/identifiers",
  CREDENTIALS = "/tabs/credentials",
  SCAN = "/tabs/scan",
  NOTIFICATIONS = "/tabs/notifications",
  MENU = "/tabs/menu",
  TOKENS = "/tabs/tokens",
  NFTS = "/tabs/nfts",
  STAKING = "/tabs/staking",
  GOVERNANCE = "/tabs/governance",
  DAPP_BROWSER = "/tabs/dapp-browser",
  IDENTIFIER_DETAILS = "/tabs/identifiers/:id",
  CREDENTIAL_DETAILS = "/tabs/credentials/:id",
  NOTIFICATION_DETAILS = "/tabs/notifications/:id",
}

const PublicRoutes = [
  RoutePath.ROOT,
  RoutePath.ONBOARDING,
  RoutePath.SET_PASSCODE,
];

export { RoutePath, TabsRoutePath, PublicRoutes };
