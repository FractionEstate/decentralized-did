'use client'

import { motion } from 'framer-motion'
import { AlertTriangle, DollarSign, Users, Key, Database } from 'lucide-react'

export default function Problem() {
  const stats = [
    { icon: Database, value: '4.1 billion', label: 'Records Breached in 2024' },
    { icon: DollarSign, value: '$6 trillion', label: 'Lost to Identity Fraud' },
    { icon: Users, value: '15 million', label: 'Fake Accounts Created Daily' },
    { icon: Key, value: '100+', label: 'Passwords per Person' },
  ]

  return (
    <div className="max-w-7xl mx-auto">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center mb-16"
      >
        <AlertTriangle className="w-32 h-32 mx-auto mb-8 text-red-500" />
        <h2 className="text-7xl font-bold mb-6 text-white">The Problem</h2>
        <p className="text-5xl font-light text-white/90">Digital Identity is Broken</p>
      </motion.div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-16">
        {stats.map((stat, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="card-glass p-8 text-center"
          >
            <stat.icon className="w-16 h-16 mx-auto mb-4 text-cardano-cyan" />
            <div className="text-4xl font-bold text-white mb-2">{stat.value}</div>
            <div className="text-xl text-white/70">{stat.label}</div>
          </motion.div>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="card-glass p-12 text-center"
      >
        <p className="text-4xl italic text-white/90">
          "Your identity is controlled by corporations<br />who profit from selling your data"
        </p>
        <div className="mt-8 text-2xl text-red-400 font-semibold">
          🚨 Centralized Systems = Single Points of Failure
        </div>
      </motion.div>
    </div>
  )
}
