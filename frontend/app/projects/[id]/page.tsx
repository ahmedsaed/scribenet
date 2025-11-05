'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import AgentStatusCard, { AgentState, AgentType } from '@/components/AgentStatusCard';
import ChapterGrid, { Chapter } from '@/components/ChapterGrid';
import ActivityFeed, { ActivityEvent } from '@/components/ActivityFeed';
import ScoreDisplay, { QualityScore } from '@/components/ScoreDisplay';
import ExpandableSection from '@/components/ExpandableSection';
import { ApiClient } from '@/lib/api';
import { useProjectWebSocket } from '@/lib/websocket';

const api = new ApiClient('http://localhost:8080');

const AGENT_TYPES: AgentType[] = ['director', 'outline', 'writer', 'editor', 'critic', 'summarizer'];

export default function ProjectDashboard() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const [projectTitle, setProjectTitle] = useState<string>('Loading...');
  const [agents, setAgents] = useState<Record<AgentType, AgentState>>({
    director: { type: 'director', status: 'idle' },
    outline: { type: 'outline', status: 'idle' },
    writer: { type: 'writer', status: 'idle' },
    editor: { type: 'editor', status: 'idle' },
    critic: { type: 'critic', status: 'idle' },
    summarizer: { type: 'summarizer', status: 'idle' },
  });
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [activities, setActivities] = useState<ActivityEvent[]>([]);
  const [qualityScores, setQualityScores] = useState<QualityScore[]>([]);
  const [overallScore, setOverallScore] = useState<number | undefined>();
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // WebSocket connection for real-time updates
  const { lastEvent, isConnected } = useProjectWebSocket(projectId);

  // Load initial project data
  useEffect(() => {
    const loadProject = async () => {
      setIsLoading(true);
      try {
        const project = await api.getProject(projectId);
        setProjectTitle(project.title);

        // Try to load chapters, but don't fail if there are none
        try {
          const chaptersData = await api.getChapters(projectId);
          // Map API chapter format to component format
          const mappedChapters = (chaptersData || []).map(ch => ({
            number: ch.chapter_number,
            title: ch.title || `Chapter ${ch.chapter_number}`,
            status: ch.status as 'not_started' | 'in_progress' | 'completed' | 'needs_revision',
            qualityScore: ch.latest_score,
            wordCount: ch.word_count,
          }));
          setChapters(mappedChapters);

          // Calculate initial scores from chapters
          if (mappedChapters.length > 0) {
            updateScoresFromChapters(mappedChapters);
          }
        } catch (chapterErr) {
          console.warn('No chapters yet for this project:', chapterErr);
          setChapters([]);
        }
      } catch (err) {
        console.error('Failed to load project:', err);
        setError('Failed to load project data');
      } finally {
        setIsLoading(false);
      }
    };

    loadProject();
  }, [projectId]);

  // Handle WebSocket events
  useEffect(() => {
    if (!lastEvent) return;

    // Add to activity feed
    const eventType = lastEvent.type || lastEvent.event;
    const activity: ActivityEvent = {
      id: `${Date.now()}-${Math.random()}`,
      timestamp: lastEvent.timestamp || new Date().toISOString(),
      type: eventType as any,
      message: lastEvent.message || eventType,
      agentType: lastEvent.agent_type,
      metadata: lastEvent.data,
    };
    setActivities((prev) => [...prev, activity]);

    // Update agent status
    if (lastEvent.agent_type) {
      const agentType = lastEvent.agent_type as AgentType;
      setAgents((prev) => ({
        ...prev,
        [agentType]: {
          type: agentType,
          status: eventType === 'agent_started' ? 'working' : 
                  eventType === 'agent_completed' ? 'completed' : 
                  eventType === 'error' ? 'error' : prev[agentType].status,
          currentTask: lastEvent.message,
          lastUpdated: new Date().toISOString(),
          progress: lastEvent.data?.progress,
        },
      }));
    }

    // Update chapters on completion
    if (eventType === 'chapter_completed' && lastEvent.data?.chapter_number) {
      const chapterNum = lastEvent.data.chapter_number;
      setChapters((prev) =>
        prev.map((ch) =>
          ch.number === chapterNum
            ? {
                ...ch,
                status: 'completed',
                qualityScore: lastEvent.data.quality_score,
                wordCount: lastEvent.data.word_count,
              }
            : ch
        )
      );
    }

    // Update quality scores
    if (eventType === 'quality_scored' && lastEvent.data) {
      updateScoresFromEvent(lastEvent.data);
    }
  }, [lastEvent]);

  const updateScoresFromChapters = (chaps: Chapter[]) => {
    const completedChapters = chaps.filter((ch) => ch.status === 'completed' && ch.qualityScore);
    if (completedChapters.length === 0) return;

    const avgScore = Math.round(
      completedChapters.reduce((sum, ch) => sum + (ch.qualityScore || 0), 0) / completedChapters.length
    );
    setOverallScore(avgScore);

    // Sample breakdown - in real implementation, get from API
    setQualityScores([
      { category: 'Content Quality', score: avgScore, maxScore: 100 },
      { category: 'Chapters Completed', score: completedChapters.length, maxScore: chaps.length },
    ]);
  };

  const updateScoresFromEvent = (data: any) => {
    if (data.overall_score !== undefined) {
      setOverallScore(data.overall_score);
    }
    if (data.scores && Array.isArray(data.scores)) {
      setQualityScores(data.scores);
    }
  };

  const handleStartWorkflow = async () => {
    try {
      setIsRunning(true);
      setError(null);
      await api.startProject(projectId);
      
      setActivities((prev) => [
        ...prev,
        {
          id: `${Date.now()}`,
          timestamp: new Date().toISOString(),
          type: 'info',
          message: 'Workflow started successfully',
        },
      ]);
    } catch (err) {
      console.error('Failed to start workflow:', err);
      setError('Failed to start workflow. Check console for details.');
      setIsRunning(false);
    }
  };

  const handleRegenerateChapter = async (chapterNumber: number) => {
    try {
      await api.regenerateChapter(projectId, chapterNumber);
      setActivities((prev) => [
        ...prev,
        {
          id: `${Date.now()}`,
          timestamp: new Date().toISOString(),
          type: 'info',
          message: `Regenerating chapter ${chapterNumber}`,
        },
      ]);
    } catch (err) {
      console.error('Failed to regenerate chapter:', err);
    }
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Background gradient - centered with white edges */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-br from-transparent via-sky-50/40 to-purple-50/30" 
             style={{ 
               maskImage: 'radial-gradient(ellipse at center, black 20%, transparent 70%)',
               WebkitMaskImage: 'radial-gradient(ellipse at center, black 20%, transparent 70%)'
             }} 
        />
      </div>

      {/* Header Bar */}
      <div className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-10 relative">
        <div className="max-w-[1800px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => router.push('/')}
                className="text-gray-600 hover:text-sky-600 transition-colors flex items-center gap-2 text-sm font-medium"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Back to Projects
              </button>
              <div className="h-6 w-px bg-gray-300" />
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold bg-gradient-to-r from-sky-600 to-purple-600 bg-clip-text text-transparent">
                  {isLoading ? 'Loading...' : projectTitle}
                </h1>
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-block w-2 h-2 rounded-full ${
                      isConnected ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
                    }`}
                  />
                  <span className="text-xs text-gray-600">
                    {isConnected ? 'Live' : 'Ready'}
                  </span>
                </div>
              </div>
            </div>
          </div>
          {error && (
            <div className="mt-3 bg-red-50 border-l-4 border-red-500 text-red-700 px-4 py-3 rounded">
              <div className="flex items-center gap-2">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                {error}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-[1800px] mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column - Chapters (Wider) */}
          <div className="lg:col-span-8">
            <div className="mb-4">
              <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <span className="text-3xl">📚</span>
                Chapters
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                {chapters.length > 0 ? `${chapters.length} chapters in progress` : 'No chapters yet'}
              </p>
            </div>
            
            {chapters.length > 0 ? (
              <ChapterGrid projectId={projectId} chapters={chapters} />
            ) : (
              <div className="bg-white rounded-2xl shadow-md border border-gray-200 p-12 text-center">
                <div className="text-7xl mb-6">�</div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">
                  Ready to Begin Your Story
                </h3>
                <p className="text-gray-600 mb-8 max-w-md mx-auto">
                  Your book project is set up and ready. Click "Start Workflow" above to begin the AI-powered writing process.
                </p>
                <div className="bg-gradient-to-br from-sky-50 to-purple-50 border-2 border-sky-200 rounded-xl p-6 text-left max-w-xl mx-auto">
                  <div className="flex items-center gap-2 mb-4">
                    <div className="w-8 h-8 bg-gradient-to-r from-sky-500 to-purple-600 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                    <p className="text-sm font-bold text-gray-900">The AI Writing Pipeline</p>
                  </div>
                  <div className="space-y-3">
                    {[
                      { icon: '🎬', name: 'Director', desc: 'Establishes creative vision & themes' },
                      { icon: '📋', name: 'Outline', desc: 'Structures your book & chapters' },
                      { icon: '✍️', name: 'Writer', desc: 'Drafts engaging chapter content' },
                      { icon: '✨', name: 'Editor', desc: 'Refines and polishes the text' },
                      { icon: '⚖️', name: 'Critic', desc: 'Provides quality feedback' },
                      { icon: '📝', name: 'Summarizer', desc: 'Creates chapter summaries' },
                    ].map((agent, idx) => (
                      <div key={idx} className="flex items-start gap-3">
                        <span className="text-2xl">{agent.icon}</span>
                        <div>
                          <p className="text-sm font-semibold text-gray-900">{agent.name}</p>
                          <p className="text-xs text-gray-600">{agent.desc}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Sidebar (Narrower) */}
          <div className="lg:col-span-4 space-y-4">
            {/* Agent Status */}
            <ExpandableSection title="Agent Status" icon="🤖" defaultExpanded={true}>
              <div className="grid grid-cols-2 gap-2">
                {AGENT_TYPES.map((type) => (
                  <AgentStatusCard key={type} agent={agents[type]} />
                ))}
              </div>
            </ExpandableSection>

            {/* Quality Metrics */}
            <ExpandableSection title="Quality Metrics" icon="⭐" defaultExpanded={true}>
              <ScoreDisplay scores={qualityScores} overallScore={overallScore} />
            </ExpandableSection>

            {/* Activity Feed */}
            <ExpandableSection title="Activity Feed" icon="📊" defaultExpanded={true}>
              <div className="h-[400px] overflow-y-auto pr-2 -mr-2 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100">
                {activities.length > 0 ? (
                  <ActivityFeed events={activities} maxHeight="none" />
                ) : (
                  <div className="text-center py-12 text-gray-500">
                    <svg className="w-12 h-12 mx-auto mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-sm text-gray-900 font-medium">No activity yet</p>
                    <p className="text-xs mt-1 text-gray-600">Activity will appear here as you work</p>
                  </div>
                )}
              </div>
            </ExpandableSection>
          </div>
        </div>
      </div>
    </div>
  );
}
