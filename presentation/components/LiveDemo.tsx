'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Fingerprint, CheckCircle, Loader2, Smartphone, X } from 'lucide-react'

export default function LiveDemo() {
  const [enrollmentStep, setEnrollmentStep] = useState(0)
  const [fingersEnrolled, setFingersEnrolled] = useState<number[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [generatedDID, setGeneratedDID] = useState('')

  const fingers = [
    { id: 1, name: 'Left Thumb', label: 'L Thumb' },
    { id: 2, name: 'Left Index', label: 'L Index' },
    { id: 3, name: 'Left Middle', label: 'L Middle' },
    { id: 4, name: 'Left Ring', label: 'L Ring' },
    { id: 5, name: 'Left Pinky', label: 'L Pinky' },
    { id: 6, name: 'Right Thumb', label: 'R Thumb' },
    { id: 7, name: 'Right Index', label: 'R Index' },
    { id: 8, name: 'Right Middle', label: 'R Middle' },
    { id: 9, name: 'Right Ring', label: 'R Ring' },
    { id: 10, name: 'Right Pinky', label: 'R Pinky' },
  ]

  const enrollFinger = (fingerId: number) => {
    setIsProcessing(true)
    setTimeout(() => {
      setFingersEnrolled([...fingersEnrolled, fingerId])
      setIsProcessing(false)
      if (fingersEnrolled.length === 9) {
        setTimeout(() => {
          setEnrollmentStep(1)
          setIsProcessing(true)
          setTimeout(() => {
            const mockDID = `did:cardano:mainnet:zQm${Math.random().toString(36).substring(2, 15)}${Math.random().toString(36).substring(2, 15)}`
            setGeneratedDID(mockDID)
            setEnrollmentStep(2)
            setIsProcessing(false)
          }, 2000)
        }, 500)
      }
    }, 800)
  }

  const reset = () => {
    setEnrollmentStep(0)
    setFingersEnrolled([])
    setGeneratedDID('')
    setIsProcessing(false)
  }

  return (
    <div className="w-full h-full flex flex-col justify-center items-center px-3 overflow-hidden gap-2 sm:gap-4 lg:gap-6">
      {/* Title */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center mb-2 sm:mb-4"
      >
        <h2 className="text-4xl sm:text-6xl lg:text-7xl font-bold mb-1 sm:mb-2">
          <span className="gradient-text">Live Demo</span>
        </h2>
        <p className="text-xl sm:text-3xl lg:text-4xl font-light text-white/90">Interactive Enrollment</p>
      </motion.div>

      {/* Mobile Phone Frame */}
      <motion.div
        initial={{ opacity: 0, scale: 0.85 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        className="relative w-full max-w-sm"
      >
        {/* Phone Bezel */}
        <div className="bg-gradient-to-b from-slate-900 to-black rounded-3xl shadow-2xl overflow-hidden border-8 border-black"
          style={{ aspectRatio: '9/20' }}>
          {/* Notch */}
          <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-32 h-6 bg-black rounded-b-3xl z-20"></div>

          {/* Screen */}
          <div className="w-full h-full bg-gradient-to-b from-slate-900 via-blue-950 to-slate-900 overflow-y-auto flex flex-col">
            {/* Status Bar */}
            <div className="h-8 bg-black/60 flex items-center justify-between px-4 text-white/70 text-xs font-semibold sticky top-0 z-10">
              <span>9:41</span>
              <div className="flex gap-1">📶 🔋</div>
            </div>

            {/* App Content Container */}
            <div className="flex-1 px-3 py-4 flex flex-col items-center justify-center gap-2">
              <AnimatePresence mode="wait">
                {enrollmentStep === 0 && (
                  <motion.div
                    key="enrollment"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="w-full flex flex-col items-center gap-3"
                  >
                    {/* App Header */}
                    <div className="w-full flex items-center justify-between mb-1">
                      <X className="w-5 h-5 text-white/30" />
                      <span className="text-sm font-bold text-white">Biometric ID</span>
                      <Smartphone className="w-5 h-5 text-cardano-cyan" />
                    </div>

                    {/* Enrollment Status */}
                    <div className="w-full bg-gradient-to-r from-cardano-cyan/10 to-purple-500/10 rounded-lg p-2 border border-cardano-cyan/20">
                      <p className="text-xs text-center text-white/70">Fingerprint Enrollment</p>
                      <p className="text-sm font-bold text-center text-cardano-cyan">
                        {fingersEnrolled.length}/10
                      </p>
                      {/* Progress Bar */}
                      <div className="w-full h-1 bg-white/10 rounded-full mt-1 overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-cardano-cyan to-purple-500 transition-all"
                          style={{ width: `${(fingersEnrolled.length / 10) * 100}%` }}
                        ></div>
                      </div>
                    </div>

                    {/* Fingerprint Grid */}
                    <div className="w-full grid grid-cols-2 gap-1.5">
                      {fingers.map((finger) => (
                        <motion.button
                          key={finger.id}
                          onClick={() => !fingersEnrolled.includes(finger.id) && !isProcessing && enrollFinger(finger.id)}
                          disabled={fingersEnrolled.includes(finger.id) || isProcessing}
                          whileHover={!fingersEnrolled.includes(finger.id) && !isProcessing ? { scale: 1.05 } : {}}
                          whileTap={!fingersEnrolled.includes(finger.id) && !isProcessing ? { scale: 0.95 } : {}}
                          className={`p-2 rounded-lg border-2 transition-all text-xs font-semibold flex flex-col items-center gap-1 ${fingersEnrolled.includes(finger.id)
                              ? 'bg-emerald-500/20 border-emerald-500'
                              : 'bg-white/5 border-cardano-cyan/40 hover:border-cardano-cyan hover:bg-cardano-cyan/15'
                            } ${isProcessing && !fingersEnrolled.includes(finger.id) ? 'opacity-40 cursor-not-allowed' : ''}`}
                        >
                          <Fingerprint
                            className={`w-5 h-5 ${fingersEnrolled.includes(finger.id) ? 'text-emerald-500' : 'text-cardano-cyan'
                              }`}
                          />
                          <span className="text-white/80 text-xs">{finger.label}</span>
                          {fingersEnrolled.includes(finger.id) && (
                            <CheckCircle className="w-3 h-3 text-emerald-500" />
                          )}
                        </motion.button>
                      ))}
                    </div>

                    {/* Instructions */}
                    <p className="text-xs text-center text-white/50 mt-1">
                      {isProcessing ? '⏳ Processing...' : '👆 Tap each finger'}
                    </p>
                  </motion.div>
                )}

                {enrollmentStep === 1 && (
                  <motion.div
                    key="processing"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="w-full text-center py-4 flex flex-col items-center gap-2"
                  >
                    <Loader2 className="w-12 h-12 text-cardano-cyan animate-spin" />
                    <h3 className="text-base font-bold text-white">Generating DID...</h3>
                    <p className="text-xs text-white/60">
                      Extracting minutiae
                    </p>
                    <p className="text-xs text-white/60">
                      Computing hash
                    </p>
                    <p className="text-xs text-white/60">
                      Anchoring to blockchain
                    </p>
                  </motion.div>
                )}

                {enrollmentStep === 2 && (
                  <motion.div
                    key="success"
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0 }}
                    className="w-full text-center py-2 flex flex-col items-center gap-2"
                  >
                    <CheckCircle className="w-12 h-12 text-emerald-500 animate-bounce" />
                    <h3 className="text-base font-bold text-white">DID Created! ✨</h3>

                    {/* DID Display */}
                    <div className="w-full bg-black/40 rounded-lg p-2 border border-cardano-cyan/20">
                      <p className="text-xs text-white/60 mb-0.5">Your Identifier:</p>
                      <p className="text-xs font-mono text-cardano-cyan break-all line-clamp-2">
                        {generatedDID}
                      </p>
                    </div>

                    {/* Features Grid */}
                    <div className="w-full grid grid-cols-3 gap-1 text-center">
                      <div className="bg-white/5 rounded p-1.5 border border-white/10">
                        <div className="text-lg">🔒</div>
                        <div className="text-xs font-semibold text-white/80">Private</div>
                      </div>
                      <div className="bg-white/5 rounded p-1.5 border border-white/10">
                        <div className="text-lg">🎯</div>
                        <div className="text-xs font-semibold text-white/80">Unique</div>
                      </div>
                      <div className="bg-white/5 rounded p-1.5 border border-white/10">
                        <div className="text-lg">⛓️</div>
                        <div className="text-xs font-semibold text-white/80">Immutable</div>
                      </div>
                    </div>

                    {/* Try Again Button */}
                    <button
                      onClick={reset}
                      className="w-full mt-2 px-3 py-1.5 bg-gradient-to-r from-cardano-cyan to-purple-500 text-black font-semibold rounded-lg hover:from-cardano-cyan/80 hover:to-purple-500/80 transition-all text-xs"
                    >
                      Enroll Again
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Home Indicator */}
            <div className="h-5 bg-black/60 flex items-center justify-center">
              <div className="w-32 h-1 bg-white/30 rounded-full"></div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Demo Disclaimer */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="text-center text-xs text-white/40"
      >
        * Simulated biometric data for demonstration
      </motion.p>
    </div>
  )
}
