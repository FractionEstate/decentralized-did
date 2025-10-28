'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Hero from '@/components/Hero'
import Problem from '@/components/Problem'
import Solution from '@/components/Solution'
import HowItWorks from '@/components/HowItWorks'
import LiveDemo from '@/components/LiveDemo'
import Security from '@/components/Security'
import OpenSource from '@/components/OpenSource'
import CallToAction from '@/components/CallToAction'
import Navigation from '@/components/Navigation'

export default function Home() {
  const [currentSection, setCurrentSection] = useState(0)
  const [direction, setDirection] = useState(0)

  const sections = [
    { id: 'hero', component: Hero, title: 'Introduction' },
    { id: 'problem', component: Problem, title: 'The Problem' },
    { id: 'solution', component: Solution, title: 'The Solution' },
    { id: 'how-it-works', component: HowItWorks, title: 'How It Works' },
    { id: 'demo', component: LiveDemo, title: 'Live Demo' },
    { id: 'security', component: Security, title: 'Security' },
    { id: 'open-source', component: OpenSource, title: 'Open Source' },
    { id: 'cta', component: CallToAction, title: 'Join Us' },
  ]

  const handleNext = () => {
    if (currentSection < sections.length - 1) {
      setDirection(1)
      setCurrentSection(currentSection + 1)
    }
  }

  const handlePrev = () => {
    if (currentSection > 0) {
      setDirection(-1)
      setCurrentSection(currentSection - 1)
    }
  }

  const onNavigate = (index: number) => {
    setDirection(index > currentSection ? 1 : -1)
    setCurrentSection(index)
  }

  const slideVariants = {
    hidden: (direction: number) => ({
      x: direction > 0 ? '100%' : '-100%',
      opacity: 0,
      scale: 0.95,
    }),
    visible: {
      x: 0,
      opacity: 1,
      scale: 1,
      transition: { duration: 0.4, ease: 'easeOut' },
    },
    exit: (direction: number) => ({
      x: direction < 0 ? '100%' : '-100%',
      opacity: 0,
      scale: 0.95,
      transition: { duration: 0.3, ease: 'easeIn' },
    }),
  }

  const CurrentComponent = sections[currentSection].component

  return (
    <main className="relative h-screen overflow-hidden">
      <Navigation
        sections={sections}
        currentSection={currentSection}
        onNavigate={onNavigate}
      />

      <AnimatePresence initial={false} custom={direction}>
        <motion.div
          key={currentSection}
          custom={direction}
          variants={slideVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
          className="slide-section absolute inset-0"
        >
          <CurrentComponent />
        </motion.div>
      </AnimatePresence>

      {/* Navigation Controls */}
      <div className="fixed bottom-8 left-8 right-8 flex justify-between items-center z-50">
        <button
          onClick={handlePrev}
          disabled={currentSection === 0}
          className="px-6 py-3 bg-white/10 hover:bg-white/20 disabled:opacity-30 disabled:cursor-not-allowed rounded-lg backdrop-blur-sm transition-all"
        >
          ← Previous
        </button>
        <div className="text-sm text-white/60">
          {currentSection + 1} / {sections.length}
        </div>
        <button
          onClick={handleNext}
          disabled={currentSection === sections.length - 1}
          className="px-6 py-3 bg-cardano-cyan hover:bg-cardano-cyan/80 disabled:opacity-30 disabled:cursor-not-allowed rounded-lg transition-all text-black font-semibold"
        >
          Next →
        </button>
      </div>

      {/* Keyboard Navigation */}
      <div
        className="fixed inset-0 focus:outline-none"
        onKeyDown={(e) => {
          if (e.key === 'ArrowRight' || e.key === ' ') handleNext()
          if (e.key === 'ArrowLeft') handlePrev()
        }}
        tabIndex={-1}
      />
    </main>
  )
}
