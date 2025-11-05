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
  agent_started: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-900', icon: 'bg-blue-500' },
  agent_completed: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-900', icon: 'bg-green-500' },
  chapter_completed: { bg: 'bg-purple-50', border: 'border-purple-200', text: 'text-purple-900', icon: 'bg-purple-500' },
  quality_scored: { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-900', icon: 'bg-yellow-500' },
  error: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-900', icon: 'bg-red-500' },
  info: { bg: 'bg-gray-50', border: 'border-gray-200', text: 'text-gray-900', icon: 'bg-gray-500' },
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
              className={`${colors.bg} ${colors.border} border rounded-lg p-3 transition-all hover:shadow-md`}
            >
              <div className="flex items-start gap-2">
                <div className={`${colors.icon} w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0 text-white text-xs`}>
                  {icon}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <p className={`text-xs font-medium ${colors.text} flex-1 break-words`}>{event.message}</p>
                    <span className="text-xs text-gray-600 font-mono flex-shrink-0 whitespace-nowrap">
                      {formatTime(event.timestamp)}
                    </span>
                  </div>
                  {event.agentType && (
                    <span className={`inline-block mt-1.5 text-xs bg-white px-2 py-0.5 rounded-md capitalize font-semibold ${colors.text}`}>
                      {event.agentType}
                    </span>
                  )}
                  {event.metadata && Object.keys(event.metadata).length > 0 && (
                    <div className="mt-2 text-xs bg-white p-2 rounded-md font-mono overflow-x-auto text-gray-800">
                      {Object.entries(event.metadata).map(([key, value]) => (
                        <div key={key} className="flex gap-2 break-all">
                          <span className="font-semibold flex-shrink-0 text-gray-900">{key}:</span>
                          <span className="break-all text-gray-700">{JSON.stringify(value)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}
