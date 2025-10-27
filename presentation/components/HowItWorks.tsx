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
    <div className="max-w-7xl mx-auto">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center mb-16"
      >
        <h2 className="text-7xl font-bold mb-6">
          <span className="gradient-text">How It Works</span>
        </h2>
        <p className="text-4xl font-light text-white/90">The Technology Stack</p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {steps.map((step, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.2 }}
            className="card-glass p-8 relative overflow-hidden"
          >
            <div className="absolute top-0 right-0 text-9xl font-bold text-white/5">
              {i + 1}
            </div>
            <step.icon className="w-20 h-20 mb-6 text-cardano-cyan" />
            <h3 className="text-3xl font-bold mb-4 text-white">{step.title}</h3>
            <div className="text-2xl text-cardano-cyan mb-2 font-semibold">{step.desc}</div>
            <div className="text-xl text-white/80 mb-3">{step.detail}</div>
            <div className="text-lg text-green-400 flex items-center gap-2">
              ✓ {step.privacy}
            </div>
          </motion.div>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        className="card-glass p-8 mt-12 text-center"
      >
        <p className="text-3xl text-white/90">
          <span className="text-cardano-cyan font-bold">Collision Probability:</span> &lt; 2^-256
        </p>
        <p className="text-xl text-white/60 mt-2">
          (More unique combinations than atoms in the universe)
        </p>
      </motion.div>
    </div>
  )
}
