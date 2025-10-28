# BIOVERA - App Store Deployment Guide

**Project**: BIOVERA - Your Biometric Truth
**Contact**: biovera-wallet@gmail.com
**App ID**: org.biovera
**Date**: October 28, 2025

---

## 📱 App Store Deployment Checklist

### Phase 1: Android APK Signing

#### 1.1 Generate Keystore (One-Time Setup)
```bash
# Generate release keystore
keytool -genkey -v -keystore biovera-release.jks \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000 \
  -alias biovera-key \
  -keypass android \
  -storepass android

# Output: biovera-release.jks (keep this file safe!)
```

**Keystore Details**:
- **Filename**: biovera-release.jks
- **Alias**: biovera-key
- **Password**: android (change in production to a strong password)
- **Validity**: 10,000 days (~27 years)

#### 1.2 Sign APK
```bash
cd /workspaces/decentralized-did/demo-wallet/android/app/build/outputs/apk/release

# Sign the unsigned APK
jarsigner -verbose \
  -sigalg SHA1withRSA \
  -digestalg SHA1 \
  -keystore biovera-release.jks \
  -keypass android \
  -storepass android \
  app-release-unsigned.apk \
  biovera-key
```

#### 1.3 Zipalign APK (Required for Play Store)
```bash
# Install Android build tools if needed
# sudo apt install android-sdk-build-tools

# Align the APK (4-byte alignment required)
zipalign -v 4 \
  app-release-unsigned.apk \
  app-release.apk

# Verify alignment
zipalign -c -v 4 app-release.apk
```

**Expected Output**:
```
4-byte alignment of app-release.apk verified
```

#### 1.4 Verify Signed APK
```bash
# Check signature
jarsigner -verify -verbose -certs app-release.apk

# Check file properties
ls -lh app-release.apk
file app-release.apk
```

---

### Phase 2: iOS IPA Build (macOS Only)

#### 2.1 Prerequisites
- macOS 12.0+ (Monterey or newer)
- Xcode 14.0+ with Command Line Tools
- Apple Developer Account
- Valid provisioning profile for org.biovera

#### 2.2 Build IPA
```bash
cd /workspaces/decentralized-did/demo-wallet/ios

# Create archive
xcodebuild \
  -workspace App/App.xcworkspace \
  -scheme App \
  -configuration Release \
  -archivePath build/App.xcarchive \
  -allowProvisioningUpdates \
  archive

# Export IPA
xcodebuild \
  -exportArchive \
  -archivePath build/App.xcarchive \
  -exportOptionsPlist exportOptions.plist \
  -exportPath build/ \
  -allowProvisioningUpdates

# Output: build/App.ipa
```

#### 2.3 exportOptions.plist Template
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>destination</key>
    <string>generic/platform=iOS</string>
    <key>method</key>
    <string>app-store</string>
    <key>provisioningProfiles</key>
    <dict>
        <key>org.biovera</key>
        <string>BIOVERA Distribution</string>
    </dict>
    <key>signingCertificate</key>
    <string>Apple Distribution</string>
    <key>stripSwiftSymbols</key>
    <true/>
    <key>teamID</key>
    <string>YOUR_TEAM_ID</string>
</dict>
</plist>
```

---

### Phase 3: Google Play Store Submission

#### 3.1 Create Developer Account
- Visit: https://play.google.com/console
- Sign in with Google account
- Pay one-time registration fee ($25 USD)
- Complete store listing profile

#### 3.2 Create App Listing
1. **Navigate**: Google Play Console → Create New App
2. **App Name**: BIOVERA
3. **Default Language**: English
4. **App Category**: Finance or Utilities
5. **Content Rating**: Complete questionnaire
6. **Privacy Policy**: Link to https://biovera.io/privacy

#### 3.3 Upload APK
1. **Navigate**: Google Play Console → BIOVERA → Release
2. **Create New Release**:
   - Release Name: `1.0.0`
   - Release Notes: "Initial release of BIOVERA - Biometric DID Wallet"
3. **Upload APK**: Select signed `app-release.apk`
4. **Review**: Verify app details (name, screenshots, description)

#### 3.4 App Store Listing Details

**Title**: BIOVERA - Biometric Cardano Wallet

**Short Description** (80 chars max):
```
Sybil-resistant biometric identity for Cardano
```

**Full Description**:
```
BIOVERA is a production-ready biometric DID wallet for Cardano.

✓ Self-Sovereign Identity (SSI) with biometric authentication
✓ Deterministic DID generation from fingerprint data
✓ Privacy-preserving, Sybil-resistant verification
✓ Cardano blockchain integration with KERI support
✓ Bank-grade security with penetration testing

Features:
• Fingerprint & Face ID authentication
• Secure local storage with SQLite encryption
• Cardano multi-signature transaction support
• QR code scanning for dApp interaction
• Offline-capable with eventual consistency

Contact: biovera-wallet@gmail.com
```

**Screenshots** (Required: 2-8, 16:9 aspect ratio):
- Home screen showing wallet balance
- Fingerprint authentication screen
- Transaction confirmation UI
- Settings with biometric options
- Transaction history view

**Privacy Policy URL**:
```
https://biovera.io/privacy
```

**Support Email**:
```
biovera-wallet@gmail.com
```

#### 3.5 Content Rating
- Select "Financial Services" category
- Answer content rating questionnaire
- Receive rating certificate

#### 3.6 Submit for Review
1. Complete all required fields
2. Review app compliance (target: 90+ quality score)
3. Click "Submit App for Review"
4. **Wait**: Typically 2-3 hours for initial review

---

### Phase 4: Apple App Store Submission (iOS)

#### 4.1 Create Developer Account
- Visit: https://appstoreconnect.apple.com
- Pay annual fee ($99 USD)
- Complete developer program agreements

#### 4.2 Create App Record
1. **Navigate**: App Store Connect → My Apps
2. **Create New App**:
   - Platform: iOS
   - App Name: BIOVERA
   - Bundle ID: org.biovera
   - SKU: BIOVERA-001

#### 4.3 Upload IPA
1. **Navigate**: App Store Connect → BIOVERA → TestFlight
2. **Upload Build**:
   - Select `App.ipa` file
   - Xcode automatically processes and signs
   - Wait for processing (typically 5-15 minutes)

#### 4.4 App Store Information
- **App Name**: BIOVERA
- **Subtitle**: Your Biometric Truth
- **Description**: (see Google Play Store section above)
- **Keywords**: wallet, biometric, cardano, did, identity, crypto
- **Support URL**: https://biovera.io/support
- **Privacy Policy URL**: https://biovera.io/privacy
- **Support Email**: biovera-wallet@gmail.com

#### 4.5 Screenshots (3 orientations x 2-5 screenshots)
- iPhone 6.7" (max Pro size)
- iPhone 6.1" (standard size)
- iPad 12.9" (optional, recommended)

#### 4.6 App Review Information
- **Sign in Credentials**: (if demo account needed)
  - Email: biovera-wallet@gmail.com
  - Password: (provide secure demo access)
- **Notes**:
  ```
  This app uses biometric authentication (fingerprint/Face ID) for local
  device access. No sensitive data is shared with external servers.
  All identity data is stored locally and encrypted.
  ```

#### 4.7 App Review Metadata
- **Version**: 1.0.0
- **Build**: 1
- **Export Compliance**: Not encryption-restricted (or comply as needed)
- **Advertising**: None

#### 4.8 Submit for Review
1. Complete all required information
2. Select "Submit for Review"
3. **Wait**: Typically 24-48 hours for review

---

## 🔐 Security Checklist

- [ ] Keystore file backed up securely (not in version control)
- [ ] Keystore password stored in secure password manager
- [ ] APK signed and zipaligned
- [ ] IPA signed with valid distribution certificate
- [ ] No debug symbols in release builds
- [ ] ProGuard/R8 obfuscation enabled (Android)
- [ ] bitcode enabled (iOS)
- [ ] Privacy policy published and linked
- [ ] No hardcoded credentials in app
- [ ] Biometric data never transmitted to servers
- [ ] SSL/TLS pinning for API calls (if applicable)

---

## 📊 Build Verification

### Android APK Verification
```bash
# Check file size
ls -lh app-release.apk

# Expected: ~76-80 MB

# Verify signature
jarsigner -verify -verbose -certs app-release.apk

# Check contents
unzip -l app-release.apk | head -20

# Verify alignment
zipalign -c -v 4 app-release.apk
```

### iOS IPA Verification
```bash
# Check file size
ls -lh App.ipa

# Expected: ~70-85 MB

# Verify contents
unzip -l App.ipa | head -20

# Check Info.plist
unzip -p App.ipa Payload/App.app/Info.plist | plutil -p -
```

---

## 🚀 Deployment Timeline

| Phase | Platform | Estimated Time | Status |
|-------|----------|-----------------|--------|
| 1 | Android APK Signing | 15 min | Ready |
| 2 | iOS IPA Build | 30 min | macOS required |
| 3 | Google Play Listing | 1-2 hours | Pending |
| 3.6 | Play Store Review | 2-3 hours | Pending |
| 4 | App Store Listing | 1-2 hours | Pending |
| 4.8 | App Store Review | 24-48 hours | Pending |

**Total Time to Production**: ~48-72 hours (assuming immediate review approval)

---

## 📞 Support & Contact

**Email**: biovera-wallet@gmail.com
**Website**: https://biovera.io
**Documentation**: https://docs.biovera.io
**GitHub**: https://github.com/FractionEstate/decentralized-did

---

## Version History

| Version | Date | Notes |
|---------|------|-------|
| 1.0.0 | Oct 28, 2025 | Initial release with BIOVERA branding |

---

**Last Updated**: October 28, 2025
**Status**: Ready for APK signing and app store submission
