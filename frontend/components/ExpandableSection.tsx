'use client';

import { useState, ReactNode } from 'react';

interface ExpandableSectionProps {
  title: string;
  icon: string;
  children: ReactNode;
  defaultExpanded?: boolean;
}

export default function ExpandableSection({ 
  title, 
  icon, 
  children, 
  defaultExpanded = true 
}: ExpandableSectionProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <div className="bg-white rounded-xl border border-gray-200 hover:border-sky-300 hover:shadow-lg transition-all duration-300 overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between bg-gradient-to-r from-sky-50 to-purple-50 hover:from-sky-100 hover:to-purple-100 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="text-lg">{icon}</span>
          <h3 className="text-sm font-bold text-gray-900">{title}</h3>
        </div>
        <svg
          className={`w-4 h-4 text-gray-600 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      
      {isExpanded && (
        <div className="px-4 py-3 animate-fade-in">
          {children}
        </div>
      )}
    </div>
  );
}
