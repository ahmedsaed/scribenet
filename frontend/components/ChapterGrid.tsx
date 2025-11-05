'use client';

import Link from 'next/link';

export interface Chapter {
  number: number;
  title: string;
  status: 'not_started' | 'in_progress' | 'completed' | 'needs_revision';
  qualityScore?: number;
  wordCount?: number;
}

interface ChapterGridProps {
  projectId: string;
  chapters: Chapter[];
}

const statusColors = {
  not_started: { bg: 'bg-gray-100', border: 'border-gray-300', text: 'text-gray-700' },
  in_progress: { bg: 'bg-blue-50', border: 'border-blue-300', text: 'text-blue-800' },
  completed: { bg: 'bg-green-50', border: 'border-green-300', text: 'text-green-800' },
  needs_revision: { bg: 'bg-yellow-50', border: 'border-yellow-300', text: 'text-yellow-800' },
};

const statusIcons = {
  not_started: '⭕',
  in_progress: '🔄',
  completed: '✅',
  needs_revision: '⚠️',
};

const statusLabels = {
  not_started: 'Not Started',
  in_progress: 'In Progress',
  completed: 'Completed',
  needs_revision: 'Needs Revision',
};

export default function ChapterGrid({ projectId, chapters }: ChapterGridProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {chapters.map((chapter) => (
        <Link
          key={chapter.number}
          href={`/projects/${projectId}/chapters/${chapter.number}`}
          className="block group"
        >
          <div className={`${statusColors[chapter.status].bg} ${statusColors[chapter.status].border} ${statusColors[chapter.status].text} rounded-2xl p-5 border-2 transition-all hover:shadow-lg hover:-translate-y-1 bg-white relative overflow-hidden`}>
            {/* Animated gradient overlay for in-progress */}
            {chapter.status === 'in_progress' && (
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-blue-100/50 to-transparent animate-shimmer" 
                   style={{ backgroundSize: '200% 100%' }} />
            )}
            
            <div className="relative">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-xl ${statusColors[chapter.status].bg} flex items-center justify-center text-2xl border ${statusColors[chapter.status].border}`}>
                    {statusIcons[chapter.status]}
                  </div>
                  <div>
                    <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Chapter</span>
                    <div className="text-xl font-bold">{chapter.number}</div>
                  </div>
                </div>
                {chapter.qualityScore !== undefined && (
                  <div className={`px-3 py-1 rounded-full text-xs font-bold ${
                    chapter.qualityScore >= 80 ? 'bg-green-100 text-green-700' : 
                    chapter.qualityScore >= 60 ? 'bg-yellow-100 text-yellow-700' : 
                    'bg-red-100 text-red-700'
                  }`}>
                    {chapter.qualityScore}/100
                  </div>
                )}
              </div>

              <h3 className="font-bold text-base mb-3 line-clamp-2 min-h-[3rem] text-gray-900 group-hover:text-sky-600 transition-colors">
                {chapter.title || 'Untitled Chapter'}
              </h3>

              <div className="flex items-center justify-between text-xs">
                <span className={`px-2 py-1 rounded-full ${statusColors[chapter.status].bg} font-medium`}>
                  {statusLabels[chapter.status]}
                </span>
                {chapter.wordCount !== undefined && (
                  <span className="font-mono text-gray-600 flex items-center gap-1">
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    {chapter.wordCount.toLocaleString()}
                  </span>
                )}
              </div>
            </div>
          </div>
        </Link>
      ))}
    </div>
  );
}
