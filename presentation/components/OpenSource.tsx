'use client'

import { motion } from 'framer-motion'
import { Github, Code, Users, BookOpen } from 'lucide-react'

export default function OpenSource() {
  return (
    <div className="w-full h-full flex flex-col justify-center items-center px-3 overflow-hidden">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center mb-4 sm:mb-6"
      >
        <Github className="w-16 sm:w-24 h-16 sm:h-24 mx-auto mb-3 sm:mb-4 text-cardano-cyan" />
        <h2 className="text-4xl sm:text-6xl lg:text-7xl font-bold mb-2 sm:mb-3">
          <span className="gradient-text">100% Open Source</span>
        </h2>
        <p className="text-xl sm:text-3xl lg:text-4xl font-light text-white/90">Transparent & Auditable</p>
      </motion.div>

      <div className="grid grid-cols-2 gap-2 sm:gap-4 mb-4 w-full max-w-4xl">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="card-glass p-3 sm:p-6"
        >
          <Code className="w-10 sm:w-16 h-10 sm:h-16 mb-2 sm:mb-4 text-cardano-cyan" />
          <h3 className="text-lg sm:text-2xl lg:text-3xl font-bold mb-2 sm:mb-4 text-white">No Paid Services</h3>
          <ul className="space-y-1 sm:space-y-2 text-xs sm:text-lg text-white/80">
            <li>✓ Apache 2.0 License</li>
            <li>✓ Self-hostable infrastructure</li>
            <li>✓ Commodity hardware</li>
            <li>✓ Open drivers & protocols</li>
          </ul>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
          className="card-glass p-3 sm:p-6"
        >
          <Users className="w-10 sm:w-16 h-10 sm:h-16 mb-2 sm:mb-4 text-cardano-purple" />
          <h3 className="text-lg sm:text-2xl lg:text-3xl font-bold mb-2 sm:mb-4 text-white">Community-Driven</h3>
          <ul className="space-y-1 sm:space-y-2 text-xs sm:text-lg text-white/80">
            <li>✓ Public GitHub repository</li>
            <li>✓ Full audit trail</li>
            <li>✓ Community contributions</li>
            <li>✓ Transparent governance</li>
          </ul>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="card-glass p-3 sm:p-6 w-full max-w-4xl"
      >
        <div className="flex items-center gap-3 sm:gap-6 mb-4 sm:mb-6 flex-col sm:flex-row text-center sm:text-left">
          <BookOpen className="w-12 sm:w-16 h-12 sm:h-16 text-cardano-cyan flex-shrink-0" />
          <div>
            <h3 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-1 sm:mb-2 text-white">Tech Stack</h3>
            <p className="text-xs sm:text-base lg:text-lg text-white/70">All components are free & open-source</p>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3">
          {[
            { name: 'Python SDK', license: 'Apache 2.0' },
            { name: 'Cardano', license: 'Apache 2.0' },
            { name: 'React', license: 'MIT' },
            { name: 'FastAPI', license: 'MIT' },
            { name: 'PostgreSQL', license: 'PostgreSQL' },
            { name: 'BLAKE2b', license: 'CC0' },
            { name: 'Capacitor', license: 'MIT' },
            { name: 'WebAuthn', license: 'W3C' },
          ].map((tech, i) => (
            <div key={i} className="bg-white/5 p-2 sm:p-3 rounded-lg">
              <div className="font-semibold text-xs sm:text-sm text-white">{tech.name}</div>
              <div className="text-xs text-green-400">{tech.license}</div>
            </div>
          ))}
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="text-center mt-3 sm:mt-4"
      >
        <p className="text-base sm:text-2xl lg:text-3xl text-white/90 italic">
          "Decentralized identity requires <span className="text-cardano-cyan font-bold">decentralized development</span>"
        </p>
      </motion.div>
    </div>
  )
}
