import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Biometric DID on Cardano | One Person, One Identity',
  description: 'Decentralized biometric identity on Cardano blockchain. Privacy-preserving, tamper-proof, Sybil-resistant.',
  keywords: 'Cardano, DID, Biometric, Blockchain, Identity, Privacy, Security',
  openGraph: {
    title: 'Biometric DID on Cardano',
    description: 'One Person, One Identity - Forever',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
