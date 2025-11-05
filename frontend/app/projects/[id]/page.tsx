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
  const [chatMessage, setChatMessage] = useState('');
  const [chatMessages, setChatMessages] = useState<Array<{ id: string; sender: 'user' | 'ai'; text: string; timestamp: string }>>([]);
  const [isSendingMessage, setIsSendingMessage] = useState(false);

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

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!chatMessage.trim() || isSendingMessage) return;

    const userMessageText = chatMessage.trim();
    setChatMessage('');
    setIsSendingMessage(true);

    // Add user message
    const userMsg = {
      id: `user-${Date.now()}`,
      sender: 'user' as const,
      text: userMessageText,
      timestamp: new Date().toISOString(),
    };
    setChatMessages((prev) => [...prev, userMsg]);

    try {
      // Convert chat messages to API format
      const conversationHistory = chatMessages.map(msg => ({
        role: (msg.sender === 'user' ? 'user' : 'assistant') as 'user' | 'assistant',
        content: msg.text,
        timestamp: msg.timestamp,
      }));

      // Call the API
      const response = await api.sendChatMessage(
        projectId,
        userMessageText,
        conversationHistory
      );

      // Add AI response
      const aiMsg = {
        id: `ai-${Date.now()}`,
        sender: 'ai' as const,
        text: response.message,
        timestamp: response.timestamp,
      };
      setChatMessages((prev) => [...prev, aiMsg]);
    } catch (error) {
      console.error('Failed to send message:', error);
      
      // Add error message
      const errorMsg = {
        id: `ai-error-${Date.now()}`,
        sender: 'ai' as const,
        text: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString(),
      };
      setChatMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsSendingMessage(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Header Bar */}
      <div className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-10">
        <div className="max-w-[1920px] mx-auto px-6 py-4">
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
            <div className="mt-3 bg-red-50 border-l-4 border-red-500 text-red-700 px-4 py-3 rounded-lg">
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

      {/* Main Content - Three Column Layout */}
      <div className="max-w-[1920px] mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Left Column - Sidebar (20%) */}
          <div className="lg:col-span-1 space-y-4">
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
              <div className="max-h-[400px] overflow-y-auto">
                {activities.length > 0 ? (
                  <ActivityFeed events={activities} maxHeight="none" />
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <svg className="w-10 h-10 mx-auto mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-xs text-gray-900 font-medium">No activity yet</p>
                    <p className="text-xs mt-1 text-gray-600">Start working to see updates</p>
                  </div>
                )}
              </div>
            </ExpandableSection>
          </div>

          {/* Middle Column - Chapters (60%) */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-xl border border-gray-200 hover:border-sky-300 hover:shadow-lg transition-all duration-300">
              <div className="p-4 border-b border-gray-100 bg-gradient-to-r from-sky-50 to-purple-50 rounded-t-xl">
                <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                  <span className="text-2xl">📚</span>
                  Chapters
                </h2>
                <p className="text-xs text-gray-600 mt-1">
                  {chapters.length > 0 ? `${chapters.length} chapters in progress` : 'No chapters yet'}
                </p>
              </div>
              
              <div className="p-6">
                {chapters.length > 0 ? (
                  <ChapterGrid projectId={projectId} chapters={chapters} />
                ) : (
                  <div className="text-center py-8">
                    <div className="text-6xl mb-4">📖</div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">
                      Ready to Begin Your Story
                    </h3>
                    <p className="text-gray-600 mb-6 max-w-md mx-auto text-sm">
                      Your book project is set up and ready. Use the AI assistant to start the writing process.
                    </p>
                    <div className="bg-gradient-to-br from-sky-50 to-purple-50 border-2 border-sky-200 rounded-xl p-4 text-left max-w-xl mx-auto">
                      <div className="flex items-center gap-2 mb-3">
                        <div className="w-7 h-7 bg-gradient-to-r from-sky-500 to-purple-600 rounded-lg flex items-center justify-center">
                          <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                          </svg>
                        </div>
                        <p className="text-xs font-bold text-gray-900">The AI Writing Pipeline</p>
                      </div>
                      <div className="space-y-2">
                        {[
                          { icon: '🎬', name: 'Director', desc: 'Establishes creative vision & themes' },
                          { icon: '📋', name: 'Outline', desc: 'Structures your book & chapters' },
                          { icon: '✍️', name: 'Writer', desc: 'Drafts engaging chapter content' },
                          { icon: '✨', name: 'Editor', desc: 'Refines and polishes the text' },
                          { icon: '⚖️', name: 'Critic', desc: 'Provides quality feedback' },
                          { icon: '📝', name: 'Summarizer', desc: 'Creates chapter summaries' },
                        ].map((agent, idx) => (
                          <div key={idx} className="flex items-start gap-2">
                            <span className="text-lg">{agent.icon}</span>
                            <div>
                              <p className="text-xs font-semibold text-gray-900">{agent.name}</p>
                              <p className="text-xs text-gray-600">{agent.desc}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column - Director Chat (20%) */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl border border-gray-200 hover:border-sky-300 hover:shadow-lg transition-all duration-300 h-[calc(100vh-180px)] sticky top-24 flex flex-col">
              {/* Chat Header */}
              <div className="p-4 border-b border-gray-100 bg-gradient-to-r from-sky-50 to-purple-50 rounded-t-xl flex-shrink-0">
                <h3 className="text-sm font-bold text-gray-900 flex items-center gap-2">
                  <span className="text-xl">🎬</span>
                  Director
                </h3>
                <p className="text-xs text-gray-600 mt-1">
                  Your creative project director
                </p>
              </div>

              {/* Chat Messages Area */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {/* Welcome Message */}
                <div className="flex items-start gap-2">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-r from-sky-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                    <span className="text-white text-sm">🎬</span>
                  </div>
                  <div className="flex-1">
                    <div className="bg-gradient-to-br from-sky-50 to-purple-50 border border-sky-200 rounded-lg p-3">
                      <p className="text-sm text-gray-900 mb-2">
                        Hello! I'm the Director, overseeing your book project.
                      </p>
                      <ul className="text-xs text-gray-700 space-y-1">
                        <li>• Guide the creative vision</li>
                        <li>• Coordinate the writing team</li>
                        <li>• Manage workflows and agents</li>
                        <li>• Monitor project progress</li>
                      </ul>
                      <p className="text-xs text-gray-700 mt-2 font-medium">
                        What would you like to work on?
                      </p>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">Just now</p>
                  </div>
                </div>

                {/* Chat Messages */}
                {chatMessages.map((msg) => (
                  <div key={msg.id} className={`flex items-start gap-2 ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}>
                    {msg.sender === 'ai' ? (
                      <div className="w-8 h-8 rounded-full bg-gradient-to-r from-sky-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                        <span className="text-white text-sm">🎬</span>
                      </div>
                    ) : (
                      <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center flex-shrink-0">
                        <span className="text-gray-600 text-sm">👤</span>
                      </div>
                    )}
                    <div className="flex-1">
                      <div className={`rounded-lg p-3 ${
                        msg.sender === 'user' 
                          ? 'bg-gradient-to-r from-sky-500 to-purple-600 text-white' 
                          : 'bg-gray-50 border border-gray-200 text-gray-900'
                      }`}>
                        <p className="text-sm">{msg.text}</p>
                      </div>
                      <p className={`text-xs text-gray-400 mt-1 ${msg.sender === 'user' ? 'text-right' : ''}`}>
                        {formatTime(msg.timestamp)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Chat Input Area */}
              <div className="p-4 border-t border-gray-100 bg-gray-50 rounded-b-xl flex-shrink-0">
                <form onSubmit={handleSendMessage}>
                  <div className="flex items-center gap-2">
                    <textarea
                      value={chatMessage}
                      onChange={(e) => setChatMessage(e.target.value)}
                      onKeyDown={handleKeyDown}
                      placeholder="Type your message..."
                      rows={2}
                      disabled={isSendingMessage}
                      className="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 resize-none disabled:opacity-50 disabled:cursor-not-allowed"
                    />
                    <button
                      type="submit"
                      disabled={isSendingMessage || !chatMessage.trim()}
                      className="px-3 py-2 bg-gradient-to-r from-sky-500 to-purple-600 text-white rounded-lg hover:from-sky-600 hover:to-purple-700 transition-all flex items-center justify-center flex-shrink-0 w-[52px] h-[52px] disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Send message"
                    >
                      {isSendingMessage ? (
                        <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                      ) : (
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                        </svg>
                      )}
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    Press Enter to send, Shift+Enter for new line
                  </p>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
