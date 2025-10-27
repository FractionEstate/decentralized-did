'use client'

import { motion } from 'framer-motion'
import { Fingerprint, Shield, Lock } from 'lucide-react'

export default function Hero() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8 }}
      className="text-center max-w-6xl mx-auto"
    >
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
        className="mb-8 flex justify-center gap-8"
      >
        <Fingerprint className="w-24 h-24 text-cardano-cyan animate-pulse-slow" />
        <Shield className="w-24 h-24 text-cardano-purple animate-pulse-slow" style={{ animationDelay: '0.5s' }} />
        <Lock className="w-24 h-24 text-cardano-cyan animate-pulse-slow" style={{ animationDelay: '1s' }} />
      </motion.div>

      <h1 className="text-7xl md:text-9xl font-bold mb-6">
        <span className="gradient-text">Biometric DID</span>
        <br />
        <span className="text-white">on Cardano</span>
      </h1>

      <p className="text-4xl md:text-5xl font-light mb-12 text-white/90">
        One Person, One Identity — <span className="gradient-text glow">Forever</span>
      </p>

      <div className="flex gap-6 justify-center text-xl md:text-2xl">
        <div className="card-glass px-8 py-4">
          <span className="text-cardano-cyan font-semibold">Decentralized</span>
        </div>
        <div className="card-glass px-8 py-4">
          <span className="text-cardano-purple font-semibold">Private</span>
        </div>
        <div className="card-glass px-8 py-4">
          <span className="text-cardano-cyan font-semibold">Tamper-Proof</span>
        </div>
      </div>

      <p className="mt-16 text-2xl text-white/60">
        Cardano Summit 2025 Hackathon
      </p>
    </motion.div>
  )
}
