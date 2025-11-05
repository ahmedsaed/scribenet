'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { brand } from '@/lib/branding';

interface NavbarProps {
  onCreateProject?: () => void;
}

export default function Navbar({ onCreateProject }: NavbarProps = {}) {
  const pathname = usePathname();

  const isActive = (path: string) => {
    return pathname === path;
  };

  return (
    <nav className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-3 group">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-sky-500 to-purple-600 text-white text-xl transition-transform group-hover:scale-110">
              {brand.logo.icon}
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-sky-600 to-purple-600 bg-clip-text text-transparent">
                {brand.logo.text}
              </h1>
              <p className="text-xs text-gray-500 -mt-1">{brand.logo.tagline}</p>
            </div>
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center space-x-6">
            <Link
              href="/"
              className={`text-sm font-medium transition-colors ${
                isActive('/')
                  ? 'text-sky-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Projects
            </Link>
            <Link
              href="/docs"
              className={`text-sm font-medium transition-colors ${
                isActive('/docs')
                  ? 'text-sky-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Documentation
            </Link>
            <Link
              href="/settings"
              className={`text-sm font-medium transition-colors ${
                isActive('/settings')
                  ? 'text-sky-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Settings
            </Link>
            
            {/* Action Button */}
            <button
              onClick={() => {
                if (onCreateProject) {
                  onCreateProject();
                } else {
                  alert('Create project functionality coming soon! Use CLI for now: python cli.py create-project');
                }
              }}
              className="px-4 py-2 bg-gradient-to-r from-sky-500 to-sky-600 text-white text-sm font-medium rounded-lg hover:from-sky-600 hover:to-sky-700 transition-all shadow-md hover:shadow-lg"
            >
              + New Project
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
