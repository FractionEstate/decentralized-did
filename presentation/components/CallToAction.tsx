'use client'

import { motion } from 'framer-motion'
import { Github, Mail, ExternalLink, Rocket } from 'lucide-react'

export default function CallToAction() {
  return (
    <div className="max-w-7xl mx-auto text-center">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ type: 'spring', stiffness: 200 }}
      >
        <Rocket className="w-32 h-32 mx-auto mb-8 text-cardano-cyan" />
        <h2 className="text-8xl font-bold mb-8">
          <span className="gradient-text glow">Join the Revolution</span>
        </h2>
        <p className="text-5xl font-light text-white/90 mb-16">
          One Person, One Identity — Forever
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="card-glass p-16 mb-12"
      >
        <h3 className="text-5xl font-bold mb-12 text-white">Get Involved</h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <a
            href="https://github.com/FractionEstate/decentralized-did"
            target="_blank"
            rel="noopener noreferrer"
            className="card-glass p-8 hover:bg-white/10 transition-all cursor-pointer group"
          >
            <Github className="w-20 h-20 mx-auto mb-6 text-cardano-cyan group-hover:scale-110 transition-transform" />
            <h4 className="text-3xl font-bold mb-4 text-white">Star on GitHub</h4>
            <p className="text-xl text-white/70 mb-4">Contribute to the codebase</p>
            <ExternalLink className="w-6 h-6 mx-auto text-white/50" />
          </a>

          <a
            href="https://cardano.org/summit"
            target="_blank"
            rel="noopener noreferrer"
            className="card-glass p-8 hover:bg-white/10 transition-all cursor-pointer group"
          >
            <Rocket className="w-20 h-20 mx-auto mb-6 text-cardano-purple group-hover:scale-110 transition-transform" />
            <h4 className="text-3xl font-bold mb-4 text-white">Try the Demo</h4>
            <p className="text-xl text-white/70 mb-4">Experience biometric DID</p>
            <ExternalLink className="w-6 h-6 mx-auto text-white/50" />
          </a>

          <a
            href="mailto:contact@fractionestate.com"
            className="card-glass p-8 hover:bg-white/10 transition-all cursor-pointer group"
          >
            <Mail className="w-20 h-20 mx-auto mb-6 text-cardano-cyan group-hover:scale-110 transition-transform" />
            <h4 className="text-3xl font-bold mb-4 text-white">Contact Us</h4>
            <p className="text-xl text-white/70 mb-4">Partner with us</p>
            <ExternalLink className="w-6 h-6 mx-auto text-white/50" />
          </a>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
        className="space-y-6"
      >
        <p className="text-4xl text-white/90">
          Built for <span className="text-cardano-cyan font-bold">Cardano Summit 2025</span>
        </p>
        <p className="text-3xl text-white/70">
          Hackathon Track: Identity & Governance
        </p>
        <p className="text-2xl text-white/50">
          Team FractionEstate
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.9 }}
        className="mt-16 text-xl text-white/40"
      >
        <p>🔒 Privacy-First • ⛓️ Decentralized • 🌍 Open Source</p>
      </motion.div>
    </div>
  )
}
