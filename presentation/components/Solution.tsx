'use client'

import { motion } from 'framer-motion'
import { Fingerprint, ArrowRight, Shield } from 'lucide-react'

export default function Solution() {
  return (
    <div className="max-w-7xl mx-auto">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center mb-16"
      >
        <h2 className="text-7xl font-bold mb-6">
          <span className="gradient-text">The Solution</span>
        </h2>
        <p className="text-5xl font-light text-white/90">
          Your Body <span className="text-cardano-cyan">IS</span> Your Identity
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.3 }}
        className="card-glass p-12 mb-12"
      >
        <div className="flex items-center justify-center gap-8 text-3xl">
          <div className="text-center">
            <Fingerprint className="w-24 h-24 mx-auto mb-4 text-cardano-cyan" />
            <div className="font-semibold">Your Fingerprints</div>
            <div className="text-xl text-white/60 mt-2">(Private)</div>
          </div>

          <ArrowRight className="w-16 h-16 text-white/40" />

          <div className="text-center">
            <div className="w-24 h-24 mx-auto mb-4 bg-gradient-to-br from-cardano-cyan to-cardano-purple rounded-full flex items-center justify-center text-5xl font-mono">
              #
            </div>
            <div className="font-semibold">Cryptographic Hash</div>
            <div className="text-xl text-white/60 mt-2">(Anonymous)</div>
          </div>

          <ArrowRight className="w-16 h-16 text-white/40" />

          <div className="text-center">
            <Shield className="w-24 h-24 mx-auto mb-4 text-cardano-purple" />
            <div className="font-semibold">Blockchain DID</div>
            <div className="text-xl text-white/60 mt-2">(Permanent)</div>
          </div>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
        className="grid grid-cols-1 md:grid-cols-2 gap-8"
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
            className="card-glass p-8"
          >
            <h3 className="text-3xl font-bold mb-3 text-cardano-cyan">{item.title}</h3>
            <p className="text-2xl text-white/80">{item.desc}</p>
          </motion.div>
        ))}
      </motion.div>
    </div>
  )
}
