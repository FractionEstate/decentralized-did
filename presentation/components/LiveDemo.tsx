'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Fingerprint, CheckCircle, Loader2 } from 'lucide-react'

export default function LiveDemo() {
  const [enrollmentStep, setEnrollmentStep] = useState(0)
  const [fingersEnrolled, setFingersEnrolled] = useState<number[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [generatedDID, setGeneratedDID] = useState('')

  const fingers = [
    { id: 1, name: 'Left Thumb' },
    { id: 2, name: 'Left Index' },
    { id: 3, name: 'Left Middle' },
    { id: 4, name: 'Left Ring' },
    { id: 5, name: 'Left Pinky' },
    { id: 6, name: 'Right Thumb' },
    { id: 7, name: 'Right Index' },
    { id: 8, name: 'Right Middle' },
    { id: 9, name: 'Right Ring' },
    { id: 10, name: 'Right Pinky' },
  ]

  const enrollFinger = (fingerId: number) => {
    setIsProcessing(true)
    setTimeout(() => {
      setFingersEnrolled([...fingersEnrolled, fingerId])
      setIsProcessing(false)
      if (fingersEnrolled.length === 9) {
        // All 10 fingers enrolled
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
    <div className="max-w-7xl mx-auto">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center mb-12"
      >
        <h2 className="text-7xl font-bold mb-6">
          <span className="gradient-text">Live Demo</span>
        </h2>
        <p className="text-4xl font-light text-white/90">Interactive Enrollment</p>
      </motion.div>

      <div className="card-glass p-12">
        <AnimatePresence mode="wait">
          {enrollmentStep === 0 && (
            <motion.div
              key="enrollment"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <h3 className="text-4xl font-bold mb-8 text-center text-white">
                Enroll Your Fingerprints
                <span className="text-cardano-cyan ml-4">
                  ({fingersEnrolled.length}/10)
                </span>
              </h3>

              <div className="fingerprint-grid mb-8">
                {fingers.map((finger) => (
                  <button
                    key={finger.id}
                    onClick={() => !fingersEnrolled.includes(finger.id) && !isProcessing && enrollFinger(finger.id)}
                    disabled={fingersEnrolled.includes(finger.id) || isProcessing}
                    className={`p-6 rounded-lg border-2 transition-all ${fingersEnrolled.includes(finger.id)
                        ? 'bg-green-500/20 border-green-500'
                        : 'bg-white/5 border-white/20 hover:border-cardano-cyan hover:bg-cardano-cyan/10'
                      } ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                  >
                    <Fingerprint className={`w-12 h-12 mx-auto mb-2 ${fingersEnrolled.includes(finger.id) ? 'text-green-500' : 'text-white/60'
                      }`} />
                    <div className="text-sm text-white/80">{finger.name}</div>
                    {fingersEnrolled.includes(finger.id) && (
                      <CheckCircle className="w-6 h-6 mx-auto mt-2 text-green-500" />
                    )}
                  </button>
                ))}
              </div>

              <p className="text-xl text-center text-white/60">
                {isProcessing ? 'Processing...' : 'Click each finger to enroll'}
              </p>
            </motion.div>
          )}

          {enrollmentStep === 1 && (
            <motion.div
              key="processing"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-center py-20"
            >
              <Loader2 className="w-32 h-32 mx-auto mb-8 text-cardano-cyan animate-spin" />
              <h3 className="text-5xl font-bold mb-4 text-white">Generating DID...</h3>
              <p className="text-2xl text-white/70">
                Applying fuzzy extractor + BCH error correction
              </p>
              <p className="text-2xl text-white/70 mt-2">
                Computing BLAKE2b hash
              </p>
              <p className="text-2xl text-white/70 mt-2">
                Encoding to Base58
              </p>
            </motion.div>
          )}

          {enrollmentStep === 2 && (
            <motion.div
              key="success"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className="text-center py-12"
            >
              <CheckCircle className="w-32 h-32 mx-auto mb-8 text-green-500" />
              <h3 className="text-5xl font-bold mb-8 text-white">DID Generated! 🎉</h3>

              <div className="card-glass p-8 mb-8 bg-black/30">
                <p className="text-sm text-white/60 mb-2">Your Decentralized Identifier:</p>
                <p className="text-2xl font-mono text-cardano-cyan break-all">
                  {generatedDID}
                </p>
              </div>

              <div className="grid grid-cols-3 gap-6 mb-8">
                <div className="card-glass p-6">
                  <div className="text-4xl mb-2">🔒</div>
                  <div className="text-xl text-white/80">Private</div>
                  <div className="text-sm text-white/60">Data never left device</div>
                </div>
                <div className="card-glass p-6">
                  <div className="text-4xl mb-2">🎯</div>
                  <div className="text-xl text-white/80">Unique</div>
                  <div className="text-sm text-white/60">One person = one DID</div>
                </div>
                <div className="card-glass p-6">
                  <div className="text-4xl mb-2">⛓️</div>
                  <div className="text-xl text-white/80">Immutable</div>
                  <div className="text-sm text-white/60">Forever on Cardano</div>
                </div>
              </div>

              <button
                onClick={reset}
                className="px-8 py-4 bg-cardano-cyan text-black font-semibold rounded-lg hover:bg-cardano-cyan/80 transition-all text-xl"
              >
                Try Again
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="text-center mt-8 text-xl text-white/50"
      >
        * Demo uses simulated biometric data for presentation purposes
      </motion.p>
    </div>
  )
}
