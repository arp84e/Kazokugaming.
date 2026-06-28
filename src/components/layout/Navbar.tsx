'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);

  const navLinks = [
    { name: 'Gaming', href: '/gaming' },
    { name: 'Tecnología', href: '/tecnologia' },
    { name: 'IA', href: '/ia' },
    { name: 'Reviews', href: '/reviews' },
    { name: 'Guías', href: '/guias' },
    { name: 'Herramientas', href: '/herramientas' },
    { name: 'Comunidad', href: '/comunidad' },
  ];

  return (
    <nav className="bg-[#171D2D] border-b border-[#20293D] sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex-shrink-0">
            <Link href="/" className="text-xl font-extrabold tracking-wider text-white hover:text-[#66C0F4] transition-colors">
              KAZOKU<span className="text-[#66C0F4]">GAMING</span>
            </Link>
          </div>

          {/* Enlaces Desktop */}
          <div className="hidden md:flex space-x-1">
            {navLinks.map((link) => (
              <Link
                key={link.name}
                href={link.href}
                className="px-3 py-2 rounded-md text-sm font-medium text-gray-300 hover:text-white hover:bg-[#20293D] transition-all"
              >
                {link.name}
              </Link>
            ))}
          </div>

          {/* Botón de Acción / Login temporal */}
          <div className="hidden md:block">
            <button className="px-4 py-1.5 rounded bg-[#1B2838] border border-[#66C0F4]/30 text-[#66C0F4] hover:bg-[#66C0F4] hover:text-[#1B2838] text-sm font-medium transition-all">
              Iniciar Sesión
            </button>
          </div>

          {/* Botón Menú Móvil */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-white hover:bg-[#20293D] focus:outline-none"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {isOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Menú Desplegable Móvil */}
      {isOpen && (
        <div className="md:hidden bg-[#171D2D] border-b border-[#20293D] px-2 pt-2 pb-3 space-y-1 sm:px-3">
          {navLinks.map((link) => (
            <Link
              key={link.name}
              href={link.href}
              className="block px-3 py-2 rounded-md text-base font-medium text-gray-300 hover:text-white hover:bg-[#20293D]"
              onClick={() => setIsOpen(false)}
            >
              {link.name}
            </Link>
          ))}
          <div className="pt-4 pb-2 border-t border-[#20293D]">
            <button className="w-full text-center px-4 py-2 rounded bg-[#00A8FF] text-white text-sm font-medium">
              Iniciar Sesión
            </button>
          </div>
        </div>
      )}
    </nav>
  );
}
