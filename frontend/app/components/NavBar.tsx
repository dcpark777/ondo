'use client'

import { useState } from 'react'
import { usePathname } from 'next/navigation'
import NotificationBell from './NotificationBell'
import ThemeToggle from './ThemeToggle'

const navLinks = [
  { href: '/', label: 'Dashboard', exact: true },
  { href: '/datasets', label: 'Datasets' },
  { href: '/browse', label: 'Browse' },
  { href: '/glossary', label: 'Glossary' },
]

export default function NavBar() {
  const pathname = usePathname()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const isActive = (href: string, exact?: boolean) => {
    if (exact) return pathname === href
    return pathname === href || pathname.startsWith(href + '/')
  }

  return (
    <nav className="bg-white border-b border-gray-200 dark:bg-gray-800 dark:border-gray-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <a href="/" className="text-xl font-semibold text-gray-900 dark:text-gray-100">Ondo</a>
          </div>

          {/* Desktop nav links */}
          <div className="hidden md:flex items-center space-x-1">
            {navLinks.map(({ href, label, exact }) => (
              <a
                key={href}
                href={href}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive(href, exact)
                    ? 'text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/30'
                    : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50 dark:text-gray-300 dark:hover:text-white dark:hover:bg-gray-700'
                }`}
              >
                {label}
              </a>
            ))}
            <ThemeToggle />
            <NotificationBell />
          </div>

          {/* Mobile hamburger button and notification bell */}
          <div className="flex items-center md:hidden gap-2">
            <ThemeToggle />
            <NotificationBell />
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-100 dark:hover:bg-gray-700 focus:outline-none"
              aria-expanded={mobileMenuOpen}
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-gray-200 dark:border-gray-700">
          <div className="px-2 pt-2 pb-3 space-y-1">
            {navLinks.map(({ href, label, exact }) => (
              <a
                key={href}
                href={href}
                className={`block px-3 py-2 rounded-md text-base font-medium ${
                  isActive(href, exact)
                    ? 'text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/30'
                    : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50 dark:text-gray-300 dark:hover:text-white dark:hover:bg-gray-700'
                }`}
                onClick={() => setMobileMenuOpen(false)}
              >
                {label}
              </a>
            ))}
          </div>
        </div>
      )}
    </nav>
  )
}
