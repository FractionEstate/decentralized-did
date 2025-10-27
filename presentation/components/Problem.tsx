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
    <div className="w-full h-full flex flex-col justify-center items-center px-4 overflow-hidden">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center mb-8 sm:mb-12"
      >
        <AlertTriangle className="w-16 sm:w-24 h-16 sm:h-24 mx-auto mb-4 sm:mb-6 text-red-500" />
        <h2 className="text-4xl sm:text-6xl lg:text-7xl font-bold mb-3 sm:mb-4 text-white">The Problem</h2>
        <p className="text-2xl sm:text-4xl lg:text-5xl font-light text-white/90">Digital Identity is Broken</p>
      </motion.div>

      <div className="grid grid-cols-2 gap-3 sm:gap-4 mb-8 w-full max-w-6xl">
        {stats.map((stat, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="card-glass p-3 sm:p-6 text-center"
          >
            <stat.icon className="w-8 sm:w-12 h-8 sm:h-12 mx-auto mb-2 sm:mb-3 text-cardano-cyan" />
            <div className="text-xl sm:text-3xl font-bold text-white mb-1">{stat.value}</div>
            <div className="text-xs sm:text-base text-white/70">{stat.label}</div>
          </motion.div>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="card-glass p-6 sm:p-8 text-center w-full max-w-4xl"
      >
        <p className="text-lg sm:text-2xl lg:text-3xl italic text-white/90">
          "Your identity is controlled by corporations who profit from selling your data"
        </p>
        <div className="mt-4 sm:mt-6 text-sm sm:text-lg text-red-400 font-semibold">
          🚨 Centralized Systems = Single Points of Failure
        </div>
      </motion.div>
    </div>
  )
}
