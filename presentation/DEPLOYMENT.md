# Deployment Guide - Cardano Summit Presentation

## 🚀 Quick Deploy to Vercel (5 minutes)

### Option 1: GitHub Integration (Recommended)

1. **Push to GitHub**
   ```bash
   cd /workspaces/decentralized-did/presentation
   git add .
   git commit -m "Add interactive presentation website"
   git push origin 10-finger-biometry-did-and-wallet
   ```

2. **Connect to Vercel**
   - Visit [vercel.com](https://vercel.com)
   - Click "Add New Project"
   - Import from GitHub: `FractionEstate/decentralized-did`
   - Root Directory: `presentation`
   - Framework Preset: Next.js (auto-detected)
   - Click "Deploy"

3. **Done!**
   - Vercel builds and deploys automatically
   - Get URL: `https://decentralized-did-presentation.vercel.app`
   - Every push to GitHub auto-deploys

### Option 2: Vercel CLI (Manual)

```bash
# Install Vercel CLI
npm install -g vercel

# Navigate to presentation folder
cd /workspaces/decentralized-did/presentation

# Install dependencies
npm install

# Build locally first (optional - test before deploy)
npm run build

# Deploy to production
vercel --prod

# Follow prompts:
# - Link to existing project? No
# - Project name: biometric-did-presentation
# - Directory: ./
# - Override settings? No
```

## 📋 Pre-Deployment Checklist

Before deploying, verify:

- [ ] `npm install` completes without errors
- [ ] `npm run build` succeeds
- [ ] All components load in dev mode
- [ ] Interactive demo works (finger enrollment)
- [ ] Navigation (arrows/spacebar) works
- [ ] No console errors in browser
- [ ] Animations smooth (no performance issues)
- [ ] Responsive on mobile/tablet
- [ ] Text readable on projected screen

## 🎨 Customization Before Deploy

### 1. Update GitHub Links
Edit `components/CallToAction.tsx`:
```typescript
href="https://github.com/FractionEstate/decentralized-did"
```

### 2. Update Contact Email
Edit `components/CallToAction.tsx`:
```typescript
href="mailto:your-email@domain.com"
```

### 3. Update Demo Link
Edit `components/CallToAction.tsx`:
```typescript
href="https://your-wallet-demo-url.vercel.app"
```

### 4. Add Analytics (Optional)
Add to `app/layout.tsx`:
```typescript
export const metadata = {
  // ... existing metadata
  verification: {
    google: 'your-google-verification-code'
  }
}
```

## 🌐 Custom Domain (Optional)

### Add Domain in Vercel:
1. Go to project settings in Vercel
2. Domains → Add Domain
3. Enter: `biometric-did.fractionestate.com`
4. Add DNS records in your domain provider:
   - Type: CNAME
   - Name: biometric-did
   - Value: cname.vercel-dns.com

## 🔧 Environment Variables

No environment variables needed for this presentation. All data is static/mocked.

If you want to connect to live API later:

1. Vercel Dashboard → Project → Settings → Environment Variables
2. Add:
   - `NEXT_PUBLIC_API_URL` = `https://your-api.com`
   - `NEXT_PUBLIC_WALLET_URL` = `https://your-wallet.vercel.app`

3. Redeploy to apply changes

## 📊 Monitoring & Analytics

### Vercel Analytics (Free)
Already enabled! View in Vercel dashboard:
- Page views
- Load times
- Geographic distribution
- Device types

### Google Analytics (Optional)
1. Create GA4 property
2. Add tracking code to `app/layout.tsx`:
   ```typescript
   <Script src="https://www.googletagmanager.com/gtag/js?id=GA_TRACKING_ID" />
   <Script id="google-analytics">
     {`
       window.dataLayer = window.dataLayer || [];
       function gtag(){dataLayer.push(arguments);}
       gtag('js', new Date());
       gtag('config', 'GA_TRACKING_ID');
     `}
   </Script>
   ```

## 🐛 Troubleshooting

### Build Fails
```bash
# Clear cache
rm -rf .next node_modules package-lock.json
npm install
npm run build
```

### TypeScript Errors
```bash
# Reinstall types
npm install --save-dev @types/react @types/node
```

### Framer Motion Issues
```bash
# Specific version
npm install framer-motion@^11.0.0
```

### Module Not Found
```bash
# Verify tsconfig.json paths
{
  "paths": {
    "@/*": ["./*"]
  }
}
```

## 🚀 Post-Deployment

### 1. Test Live Site
- [ ] Visit deployed URL
- [ ] Test on mobile device
- [ ] Test keyboard navigation
- [ ] Verify all links work
- [ ] Check loading speed (should be <2s)

### 2. Share Preview
- Get URL from Vercel dashboard
- Share with team for feedback
- Test on conference WiFi (if possible)

### 3. Backup Plan
- Download static export: `npm run build` → ZIP the `out/` folder
- Upload to backup hosting (GitHub Pages, Netlify)
- Have USB drive with offline version

## 📱 Stage Day Preparation

### Hardware
- [ ] Laptop fully charged
- [ ] Backup laptop ready
- [ ] HDMI/USB-C adapters
- [ ] Wireless presenter remote
- [ ] Mouse (in case trackpad fails)

### Software
- [ ] Bookmark presentation URL
- [ ] Download offline version (just in case)
- [ ] Clear browser cache
- [ ] Close all other tabs
- [ ] Disable notifications
- [ ] Full screen mode ready (F11)

### Network
- [ ] Test on conference WiFi before stage
- [ ] Have mobile hotspot backup
- [ ] Offline version works (Next.js static export)

## 🎭 Performance Optimization

Already optimized:
- ✅ Static export (no server required)
- ✅ Images optimized (using Lucide icons - SVG)
- ✅ Code splitting (Next.js automatic)
- ✅ CSS purged (Tailwind production build)
- ✅ Animations hardware-accelerated (Framer Motion)

## 📝 Deployment Log

Track your deployments:

| Date | URL | Notes |
|------|-----|-------|
| 2025-10-27 | `https://...vercel.app` | Initial deploy |
|  |  | Fixed mobile responsiveness |
|  |  | Production ready |

## 🆘 Emergency Contacts

- Vercel Support: support@vercel.com
- Team Lead: [your-number]
- Backup Presenter: [backup-number]

---

## ✅ Final Checklist Before Stage

30 minutes before presentation:
- [ ] Visit live URL - works perfectly
- [ ] Test keyboard navigation
- [ ] Full screen mode (F11)
- [ ] Volume muted
- [ ] Notifications off
- [ ] Wireless presenter paired
- [ ] Backup laptop ready
- [ ] Offline version on USB
- [ ] Water bottle nearby
- [ ] Deep breath - you got this! 💪

**Good luck at Cardano Summit 2025!** 🚀
