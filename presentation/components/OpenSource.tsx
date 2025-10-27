'use client'

import { motion } from 'framer-motion'
import { Github, Code, Users, BookOpen } from 'lucide-react'

export default function OpenSource() {
  return (
    <div className="max-w-7xl mx-auto">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center mb-16"
      >
        <Github className="w-32 h-32 mx-auto mb-8 text-cardano-cyan" />
        <h2 className="text-7xl font-bold mb-6">
          <span className="gradient-text">100% Open Source</span>
        </h2>
        <p className="text-4xl font-light text-white/90">Transparent & Auditable</p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="card-glass p-12"
        >
          <Code className="w-20 h-20 mb-6 text-cardano-cyan" />
          <h3 className="text-4xl font-bold mb-6 text-white">No Paid Services</h3>
          <ul className="space-y-4 text-2xl text-white/80">
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
          className="card-glass p-12"
        >
          <Users className="w-20 h-20 mb-6 text-cardano-purple" />
          <h3 className="text-4xl font-bold mb-6 text-white">Community-Driven</h3>
          <ul className="space-y-4 text-2xl text-white/80">
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
        className="card-glass p-12"
      >
        <div className="flex items-center gap-8 mb-8">
          <BookOpen className="w-24 h-24 text-cardano-cyan flex-shrink-0" />
          <div>
            <h3 className="text-4xl font-bold mb-4 text-white">Tech Stack</h3>
            <p className="text-2xl text-white/70">All components are free & open-source</p>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {[
            { name: 'Python SDK', license: 'Apache 2.0' },
            { name: 'Cardano Blockchain', license: 'Apache 2.0' },
            { name: 'React/TypeScript', license: 'MIT' },
            { name: 'FastAPI', license: 'MIT' },
            { name: 'PostgreSQL', license: 'PostgreSQL' },
            { name: 'BLAKE2b', license: 'CC0' },
            { name: 'Capacitor', license: 'MIT' },
            { name: 'WebAuthn', license: 'W3C' },
          ].map((tech, i) => (
            <div key={i} className="bg-white/5 p-4 rounded-lg">
              <div className="font-semibold text-xl text-white mb-2">{tech.name}</div>
              <div className="text-sm text-green-400">{tech.license}</div>
            </div>
          ))}
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="text-center mt-12"
      >
        <p className="text-3xl text-white/90 italic">
          "Decentralized identity requires<br />
          <span className="text-cardano-cyan font-bold">decentralized development</span>"
        </p>
      </motion.div>
    </div>
  )
}
