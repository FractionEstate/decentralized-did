'use client'

import { motion } from 'framer-motion'
import { Github, Mail, ExternalLink, Rocket } from 'lucide-react'

export default function CallToAction() {
  return (
    <div className="w-full h-full flex flex-col justify-center items-center px-3 overflow-hidden">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ type: 'spring', stiffness: 200 }}
        className="text-center mb-4 sm:mb-6"
      >
        <Rocket className="w-12 sm:w-20 h-12 sm:h-20 mx-auto mb-2 sm:mb-4 text-cardano-cyan" />
        <h2 className="text-4xl sm:text-6xl lg:text-7xl font-bold mb-2 sm:mb-4">
          <span className="gradient-text glow">Join the Revolution</span>
        </h2>
        <p className="text-xl sm:text-3xl lg:text-5xl font-light text-white/90 mb-4 sm:mb-6">
          One Person, One Identity — Forever
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="card-glass p-3 sm:p-6 mb-3 sm:mb-4 w-full max-w-5xl"
      >
        <h3 className="text-2xl sm:text-4xl lg:text-5xl font-bold mb-3 sm:mb-4 text-white">Get Involved</h3>

        <div className="grid grid-cols-3 gap-1 sm:gap-3">
          <a
            href="https://github.com/FractionEstate/decentralized-did"
            target="_blank"
            rel="noopener noreferrer"
            className="card-glass p-2 sm:p-4 hover:bg-white/10 transition-all cursor-pointer group"
          >
            <Github className="w-8 sm:w-14 h-8 sm:h-14 mx-auto mb-1 sm:mb-3 text-cardano-cyan group-hover:scale-110 transition-transform" />
            <h4 className="text-xs sm:text-lg lg:text-xl font-bold mb-1 text-white">Star on GitHub</h4>
            <p className="text-xs sm:text-sm text-white/70 mb-1">Contribute</p>
            <ExternalLink className="w-4 sm:w-5 h-4 sm:h-5 mx-auto text-white/50" />
          </a>

          <a
            href="https://cardano.org/summit"
            target="_blank"
            rel="noopener noreferrer"
            className="card-glass p-2 sm:p-4 hover:bg-white/10 transition-all cursor-pointer group"
          >
            <Rocket className="w-8 sm:w-14 h-8 sm:h-14 mx-auto mb-1 sm:mb-3 text-cardano-purple group-hover:scale-110 transition-transform" />
            <h4 className="text-xs sm:text-lg lg:text-xl font-bold mb-1 text-white">Try Demo</h4>
            <p className="text-xs sm:text-sm text-white/70 mb-1">Experience DID</p>
            <ExternalLink className="w-4 sm:w-5 h-4 sm:h-5 mx-auto text-white/50" />
          </a>

          <a
            href="mailto:contact@fractionestate.com"
            className="card-glass p-2 sm:p-4 hover:bg-white/10 transition-all cursor-pointer group"
          >
            <Mail className="w-8 sm:w-14 h-8 sm:h-14 mx-auto mb-1 sm:mb-3 text-cardano-cyan group-hover:scale-110 transition-transform" />
            <h4 className="text-xs sm:text-lg lg:text-xl font-bold mb-1 text-white">Contact</h4>
            <p className="text-xs sm:text-sm text-white/70 mb-1">Partner with us</p>
            <ExternalLink className="w-4 sm:w-5 h-4 sm:h-5 mx-auto text-white/50" />
          </a>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
        className="space-y-2 sm:space-y-3 text-center"
      >
        <p className="text-lg sm:text-2xl lg:text-3xl text-white/90">
          Built for <span className="text-cardano-cyan font-bold">Cardano Summit 2025</span>
        </p>
        <p className="text-xs sm:text-lg text-white/70">
          Hackathon: Identity & Governance
        </p>
        <p className="text-xs sm:text-base text-white/50">
          Team FractionEstate
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.9 }}
        className="mt-2 sm:mt-3 text-xs sm:text-sm text-white/40"
      >
        <p>🔒 Privacy-First • ⛓️ Decentralized • 🌍 Open Source</p>
      </motion.div>
    </div>
  )
}
