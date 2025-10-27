'use client'

import { motion } from 'framer-motion'
import { Fingerprint, ArrowRight, Shield } from 'lucide-react'

export default function Solution() {
  return (
    <div className="w-full h-full flex flex-col justify-center items-center px-3 overflow-hidden">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center mb-6 sm:mb-8"
      >
        <h2 className="text-4xl sm:text-6xl lg:text-7xl font-bold mb-3 sm:mb-4">
          <span className="gradient-text">The Solution</span>
        </h2>
        <p className="text-2xl sm:text-4xl lg:text-5xl font-light text-white/90">
          Your Body <span className="text-cardano-cyan">IS</span> Your Identity
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.3 }}
        className="card-glass p-4 sm:p-8 mb-6 sm:mb-8 w-full max-w-5xl"
      >
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4 text-lg sm:text-2xl">
          <div className="text-center">
            <Fingerprint className="w-12 sm:w-20 h-12 sm:h-20 mx-auto mb-2 sm:mb-3 text-cardano-cyan" />
            <div className="font-semibold text-sm sm:text-base">Your Fingerprints</div>
            <div className="text-xs sm:text-lg text-white/60 mt-1">(Private)</div>
          </div>

          <ArrowRight className="w-8 sm:w-12 h-8 sm:h-12 text-white/40 rotate-90 sm:rotate-0" />

          <div className="text-center">
            <div className="w-12 sm:w-20 h-12 sm:h-20 mx-auto mb-2 sm:mb-3 bg-gradient-to-br from-cardano-cyan to-cardano-purple rounded-full flex items-center justify-center text-3xl sm:text-4xl font-mono">
              #
            </div>
            <div className="font-semibold text-sm sm:text-base">Cryptographic Hash</div>
            <div className="text-xs sm:text-lg text-white/60 mt-1">(Anonymous)</div>
          </div>

          <ArrowRight className="w-8 sm:w-12 h-8 sm:h-12 text-white/40 rotate-90 sm:rotate-0" />

          <div className="text-center">
            <Shield className="w-12 sm:w-20 h-12 sm:h-20 mx-auto mb-2 sm:mb-3 text-cardano-purple" />
            <div className="font-semibold text-sm sm:text-base">Blockchain DID</div>
            <div className="text-xs sm:text-lg text-white/60 mt-1">(Permanent)</div>
          </div>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
        className="grid grid-cols-2 gap-2 sm:gap-4 w-full max-w-4xl"
      >
        {[
          { title: 'One Person = One DID', desc: 'Sybil-resistant by design' },
          { title: 'Privacy-First', desc: 'Data never leaves your device' },
          { title: 'Tamper-Proof', desc: 'Immutable on Cardano blockchain' },
          { title: 'Standards-Compliant', desc: 'W3C DID, NIST, eIDAS, GDPR' },
        ].map((item, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: i % 2 === 0 ? -20 : 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.8 + i * 0.1 }}
            className="card-glass p-3 sm:p-5"
          >
            <h3 className="text-sm sm:text-xl lg:text-2xl font-bold mb-1 sm:mb-2 text-cardano-cyan">{item.title}</h3>
            <p className="text-xs sm:text-base lg:text-lg text-white/80">{item.desc}</p>
          </motion.div>
        ))}
      </motion.div>
    </div>
  )
}
