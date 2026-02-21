import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import NavBar from './components/NavBar'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Ondo - Dataset Readiness',
  description: 'Score and improve dataset readiness',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} dark:bg-gray-900`}>
        <div className="min-h-screen">
          <NavBar />
          <main>{children}</main>
        </div>
      </body>
    </html>
  )
}
