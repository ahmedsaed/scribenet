'use client';

import Link from 'next/link';
import { brand } from '@/lib/branding';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-gray-50 border-t border-gray-200 mt-auto">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center space-x-3 mb-4">
              <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-sky-500 to-purple-600 text-white text-xl">
                {brand.logo.icon}
              </div>
              <div>
                <h2 className="text-lg font-bold bg-gradient-to-r from-sky-600 to-purple-600 bg-clip-text text-transparent">
                  {brand.logo.text}
                </h2>
                <p className="text-xs text-gray-500 -mt-1">{brand.logo.tagline}</p>
              </div>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              A multi-agent system that collaborates to write high-quality books using AI technology.
              Orchestrating Director, Outline, Writer, Editor, Critic, and Summarizer agents.
            </p>
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <span>Backend: <code className="text-xs bg-gray-200 px-2 py-1 rounded">localhost:8080</code></span>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Quick Links</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/" className="text-gray-600 hover:text-sky-600 transition-colors">
                  Projects
                </Link>
              </li>
              <li>
                <Link href="/docs" className="text-gray-600 hover:text-sky-600 transition-colors">
                  Documentation
                </Link>
              </li>
              <li>
                <a href="https://github.com" className="text-gray-600 hover:text-sky-600 transition-colors" target="_blank" rel="noopener noreferrer">
                  GitHub
                </a>
              </li>
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Resources</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/settings" className="text-gray-600 hover:text-sky-600 transition-colors">
                  Settings
                </Link>
              </li>
              <li>
                <a href="https://ollama.ai" className="text-gray-600 hover:text-sky-600 transition-colors" target="_blank" rel="noopener noreferrer">
                  Ollama
                </a>
              </li>
              <li>
                <a href="https://langchain.com" className="text-gray-600 hover:text-sky-600 transition-colors" target="_blank" rel="noopener noreferrer">
                  LangChain
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-gray-200">
          <div className="flex flex-col md:flex-row justify-between items-center text-sm text-gray-600">
            <p>&copy; {currentYear} ScribeNet. All rights reserved.</p>
            <div className="flex items-center space-x-4 mt-4 md:mt-0">
              <span className="text-xs">Powered by Ollama, LangGraph & FastAPI</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
