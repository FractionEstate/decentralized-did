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
    <div className="max-w-7xl mx-auto">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center mb-16"
      >
        <Shield className="w-32 h-32 mx-auto mb-8 text-cardano-cyan" />
        <h2 className="text-7xl font-bold mb-6 text-white">Military-Grade Security</h2>
        <p className="text-4xl font-light text-white/90">Multi-Layer Defense</p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {layers.map((layer, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.15 }}
            className="card-glass p-8"
          >
            <layer.icon className="w-16 h-16 mb-6 text-cardano-cyan" />
            <h3 className="text-3xl font-bold mb-6 text-white">{layer.title}</h3>
            <ul className="space-y-3">
              {layer.items.map((item, j) => (
                <li key={j} className="flex items-start gap-3 text-xl text-white/80">
                  <span className="text-green-400 text-2xl">✓</span>
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
        className="card-glass p-12 mt-12 text-center"
      >
        <h3 className="text-4xl font-bold mb-6 text-white">Attack Resistance</h3>
        <div className="grid grid-cols-3 gap-8">
          <div>
            <div className="text-5xl mb-3">🛡️</div>
            <div className="text-2xl font-semibold text-cardano-cyan mb-2">Spoofing</div>
            <div className="text-lg text-white/70">Liveness detection</div>
          </div>
          <div>
            <div className="text-5xl mb-3">🔐</div>
            <div className="text-2xl font-semibold text-cardano-cyan mb-2">Replay</div>
            <div className="text-lg text-white/70">Nonce + timestamps</div>
          </div>
          <div>
            <div className="text-5xl mb-3">⚡</div>
            <div className="text-2xl font-semibold text-cardano-cyan mb-2">Brute Force</div>
            <div className="text-lg text-white/70">2^256 keyspace</div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
