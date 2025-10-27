'use client'

import { motion } from 'framer-motion'
import { Shield, Lock, Eye, Zap } from 'lucide-react'

export default function Security() {
  const layers = [
    {
      icon: Shield,
      title: 'Layer 1: Biometric Security',
      items: [
        '10-finger enrollment (FBI/NIST standard)',
        'Liveness detection (prevents spoofing)',
        'Quality thresholds (128+ minutiae points)',
        'Fuzzy matching (works with injuries/aging)',
      ],
    },
    {
      icon: Lock,
      title: 'Layer 2: Cryptographic Security',
      items: [
        'BLAKE2b hashing (quantum-resistant)',
        'BCH error correction (23-bit tolerance)',
        'Deterministic generation',
        'No key storage required',
      ],
    },
    {
      icon: Zap,
      title: 'Layer 3: Blockchain Security',
      items: [
        'Cardano Proof-of-Stake',
        'Immutable audit trail',
        'Timestamp verification',
        'No central authority',
      ],
    },
    {
      icon: Eye,
      title: 'Layer 4: Privacy Protection',
      items: [
        'Raw biometrics never leave device',
        'Zero-knowledge architecture',
        'GDPR + eIDAS compliant',
        'User-controlled data',
      ],
    },
  ]

  return (
    <div className="w-full h-full flex flex-col justify-center items-center px-3 overflow-hidden">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center mb-4 sm:mb-6"
      >
        <Shield className="w-16 sm:w-24 h-16 sm:h-24 mx-auto mb-3 sm:mb-4 text-cardano-cyan" />
        <h2 className="text-4xl sm:text-6xl lg:text-7xl font-bold mb-2 sm:mb-4 text-white">Military-Grade Security</h2>
        <p className="text-xl sm:text-3xl lg:text-4xl font-light text-white/90">Multi-Layer Defense</p>
      </motion.div>

      <div className="grid grid-cols-2 gap-2 sm:gap-4 w-full max-w-5xl mb-4">
        {layers.map((layer, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.15 }}
            className="card-glass p-3 sm:p-5"
          >
            <layer.icon className="w-8 sm:w-12 h-8 sm:h-12 mb-2 sm:mb-3 text-cardano-cyan" />
            <h3 className="text-sm sm:text-lg lg:text-xl font-bold mb-2 sm:mb-3 text-white">{layer.title}</h3>
            <ul className="space-y-1 sm:space-y-2">
              {layer.items.map((item, j) => (
                <li key={j} className="flex items-start gap-1 sm:gap-2 text-xs sm:text-sm text-white/80">
                  <span className="text-green-400 flex-shrink-0">✓</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </motion.div>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="card-glass p-4 sm:p-6 text-center w-full max-w-3xl"
      >
        <h3 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-3 sm:mb-4 text-white">Attack Resistance</h3>
        <div className="grid grid-cols-3 gap-2 sm:gap-4">
          <div>
            <div className="text-3xl sm:text-4xl mb-1">🛡️</div>
            <div className="text-xs sm:text-base font-semibold text-cardano-cyan mb-1">Spoofing</div>
            <div className="text-xs text-white/70">Liveness detection</div>
          </div>
          <div>
            <div className="text-3xl sm:text-4xl mb-1">🔐</div>
            <div className="text-xs sm:text-base font-semibold text-cardano-cyan mb-1">Replay</div>
            <div className="text-xs text-white/70">Nonce + timestamps</div>
          </div>
          <div>
            <div className="text-3xl sm:text-4xl mb-1">⚡</div>
            <div className="text-xs sm:text-base font-semibold text-cardano-cyan mb-1">Brute Force</div>
            <div className="text-xs text-white/70">2^256 keyspace</div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
