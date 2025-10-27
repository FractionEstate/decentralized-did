'use client'

import { motion } from 'framer-motion'
import { Smartphone, Hash, Database, Link } from 'lucide-react'

export default function HowItWorks() {
  const steps = [
    {
      icon: Smartphone,
      title: '1. Biometric Capture',
      desc: '10 fingerprints captured',
      detail: 'Minutiae extraction (128+ points)',
      privacy: 'Raw images NEVER stored'
    },
    {
      icon: Hash,
      title: '2. Cryptographic Transform',
      desc: 'Fuzzy Extractor + BCH',
      detail: 'BLAKE2b Hash (256-bit)',
      privacy: 'Fault-tolerant & deterministic'
    },
    {
      icon: Database,
      title: '3. DID Generation',
      desc: 'Base58 encoding',
      detail: 'did:cardano:mainnet:zQm...',
      privacy: 'W3C DID standard'
    },
    {
      icon: Link,
      title: '4. Blockchain Anchoring',
      desc: 'Cardano transaction',
      detail: 'Permanent & immutable',
      privacy: 'Timestamped record'
    },
  ]

  return (
    <div className="w-full h-full flex flex-col justify-center items-center px-3 overflow-hidden">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center mb-6"
      >
        <h2 className="text-4xl sm:text-6xl lg:text-7xl font-bold mb-2 sm:mb-4">
          <span className="gradient-text">How It Works</span>
        </h2>
        <p className="text-xl sm:text-3xl lg:text-4xl font-light text-white/90">The Technology Stack</p>
      </motion.div>

      <div className="grid grid-cols-2 gap-2 sm:gap-4 w-full max-w-5xl mb-4 sm:mb-6">
        {steps.map((step, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.2 }}
            className="card-glass p-3 sm:p-5 relative overflow-hidden"
          >
            <div className="absolute top-0 right-0 text-5xl sm:text-7xl font-bold text-white/5">
              {i + 1}
            </div>
            <step.icon className="w-10 sm:w-16 h-10 sm:h-16 mb-2 sm:mb-3 text-cardano-cyan" />
            <h3 className="text-base sm:text-2xl lg:text-2xl font-bold mb-1 sm:mb-2 text-white">{step.title}</h3>
            <div className="text-xs sm:text-base lg:text-lg text-cardano-cyan mb-1 sm:mb-1 font-semibold">{step.desc}</div>
            <div className="text-xs sm:text-sm text-white/80 mb-1">{step.detail}</div>
            <div className="text-xs sm:text-sm text-green-400">✓ {step.privacy}</div>
          </motion.div>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        className="card-glass p-4 sm:p-6 text-center w-full max-w-3xl"
      >
        <p className="text-lg sm:text-2xl lg:text-3xl text-white/90">
          <span className="text-cardano-cyan font-bold">Collision Probability:</span> &lt; 2^-256
        </p>
        <p className="text-xs sm:text-base text-white/60 mt-2">
          (More unique combinations than atoms in the universe)
        </p>
      </motion.div>
    </div>
  )
}
