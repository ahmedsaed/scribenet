'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ApiClient } from '@/lib/api';

const api = new ApiClient('http://localhost:8080');

export default function ChapterDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;
  const chapterNumber = parseInt(params.num as string);

  const [chapter, setChapter] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadChapter();
  }, [projectId, chapterNumber]);

  const loadChapter = async () => {
    try {
      setLoading(true);
      const data = await api.getChapter(projectId, chapterNumber);
      setChapter(data);
    } catch (err) {
      console.error('Failed to load chapter:', err);
      setError('Failed to load chapter');
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerate = async () => {
    if (!confirm('Are you sure you want to regenerate this chapter?')) return;

    try {
      setRegenerating(true);
      await api.regenerateChapter(projectId, chapterNumber);
      alert('Chapter regeneration started. Check the dashboard for progress.');
      router.push(`/projects/${projectId}`);
    } catch (err) {
      console.error('Failed to regenerate chapter:', err);
      alert('Failed to regenerate chapter');
    } finally {
      setRegenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">Loading chapter...</p>
        </div>
      </div>
    );
  }

  if (error || !chapter) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error || 'Chapter not found'}
          </div>
          <button
            onClick={() => router.push(`/projects/${projectId}`)}
            className="mt-4 text-blue-600 hover:text-blue-800"
          >
            ← Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => router.push(`/projects/${projectId}`)}
            className="text-sm text-gray-600 hover:text-gray-900 mb-2"
          >
            ← Back to Dashboard
          </button>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Chapter {chapter.chapter_number}: {chapter.title}
              </h1>
              <div className="flex items-center space-x-4 mt-2 text-sm text-gray-600">
                <span>Status: <span className="capitalize font-semibold">{chapter.status}</span></span>
                <span>Word Count: <span className="font-semibold">{chapter.word_count?.toLocaleString() || 'N/A'}</span></span>
              </div>
            </div>
            <button
              onClick={handleRegenerate}
              disabled={regenerating}
              className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                regenerating
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-red-600 hover:bg-red-700 text-white'
              }`}
            >
              {regenerating ? '🔄 Regenerating...' : '🔄 Regenerate'}
            </button>
          </div>
        </div>

        {/* Quality Scores */}
        {chapter.scores && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-bold mb-4">Quality Scores</h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {Object.entries(chapter.scores).map(([key, value]) => (
                <div key={key} className="text-center">
                  <div className="text-3xl font-bold text-blue-600">{value as number}</div>
                  <div className="text-sm text-gray-600 capitalize">{key}</div>
                </div>
              ))}
            </div>
            {chapter.latest_score && (
              <div className="mt-4 pt-4 border-t text-center">
                <div className="text-4xl font-bold text-green-600">{chapter.latest_score}</div>
                <div className="text-sm text-gray-600">Overall Score</div>
              </div>
            )}
          </div>
        )}

        {/* Chapter Content */}
        <div className="bg-white rounded-lg shadow-md p-8">
          <h2 className="text-xl font-bold mb-4">Content</h2>
          {chapter.content ? (
            <div className="prose max-w-none">
              <pre className="whitespace-pre-wrap text-gray-800 leading-relaxed">
                {chapter.content}
              </pre>
            </div>
          ) : (
            <div className="text-center text-gray-500 py-12">
              <p>Chapter content not available yet.</p>
              <p className="text-sm mt-2">Start the workflow to generate this chapter.</p>
            </div>
          )}
        </div>

        {/* Feedback (if available) */}
        {chapter.feedback && (
          <div className="bg-yellow-50 rounded-lg shadow-md p-6 mt-6">
            <h2 className="text-xl font-bold mb-4">Critic Feedback</h2>
            <div className="text-gray-700 whitespace-pre-wrap">
              {chapter.feedback}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
