'use client'

import { motion } from 'framer-motion'
import { Fingerprint, Shield, Lock } from 'lucide-react'

export default function Hero() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8 }}
      className="text-center w-full h-full flex flex-col justify-center items-center px-3"
    >
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
        className="mb-4 sm:mb-6 flex justify-center gap-3 sm:gap-6"
      >
        <Fingerprint className="w-12 sm:w-20 h-12 sm:h-20 text-cardano-cyan animate-pulse-slow" />
        <Shield className="w-12 sm:w-20 h-12 sm:h-20 text-cardano-purple animate-pulse-slow" style={{ animationDelay: '0.5s' }} />
        <Lock className="w-12 sm:w-20 h-12 sm:h-20 text-cardano-cyan animate-pulse-slow" style={{ animationDelay: '1s' }} />
      </motion.div>

      <h1 className="text-4xl sm:text-6xl lg:text-8xl font-bold mb-3 sm:mb-4">
        <span className="gradient-text">Biometric DID</span>
        <br />
        <span className="text-white">on Cardano</span>
      </h1>

      <p className="text-xl sm:text-3xl lg:text-5xl font-light mb-6 sm:mb-8 text-white/90">
        One Person, One Identity — <span className="gradient-text glow">Forever</span>
      </p>

      <div className="flex flex-wrap gap-2 sm:gap-4 justify-center text-xs sm:text-base lg:text-lg">
        <div className="card-glass px-3 sm:px-6 py-2 sm:py-3">
          <span className="text-cardano-cyan font-semibold">Decentralized</span>
        </div>
        <div className="card-glass px-3 sm:px-6 py-2 sm:py-3">
          <span className="text-cardano-purple font-semibold">Private</span>
        </div>
        <div className="card-glass px-3 sm:px-6 py-2 sm:py-3">
          <span className="text-cardano-cyan font-semibold">Tamper-Proof</span>
        </div>
      </div>

      <p className="mt-6 sm:mt-8 text-sm sm:text-lg text-white/60">
        Cardano Summit 2025 Hackathon
      </p>
    </motion.div>
  )
}
