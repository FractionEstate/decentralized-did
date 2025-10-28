'use client'

interface NavigationProps {
  sections: Array<{ id: string; title: string }>
  currentSection: number
  onNavigate: (index: number) => void
}

export default function Navigation({ sections, currentSection, onNavigate }: NavigationProps) {
  return (
    <nav className="fixed top-8 left-8 right-8 z-40 flex justify-between items-center">
      <div className="text-2xl font-bold text-white">
        <span className="gradient-text">Biometric DID</span>
      </div>

      <div className="flex gap-3">
        {sections.map((section, i) => (
          <button
            key={section.id}
            onClick={() => onNavigate(i)}
            className={`w-3 h-3 rounded-full transition-all ${i === currentSection
                ? 'bg-cardano-cyan w-12'
                : 'bg-white/30 hover:bg-white/50'
              }`}
            title={section.title}
          />
        ))}
      </div>

      <div className="text-lg text-white/60">
        Cardano Summit 2025
      </div>
    </nav>
  )
}
