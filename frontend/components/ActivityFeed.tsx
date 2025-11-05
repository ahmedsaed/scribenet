'use client';

import { useEffect, useRef } from 'react';

export interface ActivityEvent {
  id: string;
  timestamp: string;
  type: 'agent_started' | 'agent_completed' | 'chapter_completed' | 'quality_scored' | 'error' | 'info';
  message: string;
  agentType?: string;
  metadata?: Record<string, any>;
}

interface ActivityFeedProps {
  events: ActivityEvent[];
  maxHeight?: string;
}

const eventColors = {
  agent_started: { bg: 'bg-blue-50', border: 'border-blue-300', text: 'text-blue-900' },
  agent_completed: { bg: 'bg-green-50', border: 'border-green-300', text: 'text-green-900' },
  chapter_completed: { bg: 'bg-purple-50', border: 'border-purple-300', text: 'text-purple-900' },
  quality_scored: { bg: 'bg-yellow-50', border: 'border-yellow-300', text: 'text-yellow-900' },
  error: { bg: 'bg-red-50', border: 'border-red-300', text: 'text-red-900' },
  info: { bg: 'bg-gray-50', border: 'border-gray-300', text: 'text-gray-900' },
};

const eventIcons = {
  agent_started: '▶️',
  agent_completed: '✅',
  chapter_completed: '📖',
  quality_scored: '📊',
  error: '❌',
  info: 'ℹ️',
};

export default function ActivityFeed({ events, maxHeight = '600px' }: ActivityFeedProps) {
  const feedRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new events arrive
  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [events]);

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit' 
    });
  };

  return (
    <div className="space-y-2">
      {events.length === 0 ? (
        <div className="text-center text-gray-500 py-8">
          <p className="text-sm text-gray-900 font-medium">No activity yet</p>
          <p className="text-xs mt-1 text-gray-600">Activity will appear here as you work</p>
        </div>
      ) : (
        events.map((event) => {
          const colors = eventColors[event.type] || eventColors.info;
          const icon = eventIcons[event.type] || eventIcons.info;
          return (
            <div
              key={event.id}
              className={`${colors.bg} ${colors.border} ${colors.text} border-l-4 rounded-lg p-3 transition-all`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-2 flex-1">
                  <span className="text-lg">{icon}</span>
                  <div className="flex-1">
                    <p className="text-sm font-medium">{event.message}</p>
                    {event.agentType && (
                      <span className="inline-block mt-1 text-xs bg-white/70 px-2 py-0.5 rounded capitalize font-semibold">
                        {event.agentType}
                      </span>
                    )}
                    {event.metadata && Object.keys(event.metadata).length > 0 && (
                      <div className="mt-2 text-xs bg-white/70 p-2 rounded font-mono">
                        {Object.entries(event.metadata).map(([key, value]) => (
                          <div key={key} className="flex justify-between">
                            <span className="font-semibold">{key}:</span>
                            <span>{JSON.stringify(value)}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
                <span className="text-xs text-gray-600 font-mono ml-2 flex-shrink-0">
                  {formatTime(event.timestamp)}
                </span>
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}
