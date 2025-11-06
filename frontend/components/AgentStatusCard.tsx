'use client';

import { useState, useEffect } from 'react';

export type AgentType = 'director' | 'outline' | 'writer' | 'editor' | 'critic' | 'summarizer';
export type AgentStatus = 'idle' | 'working' | 'completed' | 'error';

export interface AgentState {
  type: AgentType;
  status: AgentStatus;
  currentTask?: string;
  lastUpdated?: string;
  progress?: number; // 0-100
}

interface AgentStatusCardProps {
  agent: AgentState;
}

const agentColors = {
  director: { bg: 'from-purple-500 to-purple-600', icon: 'bg-purple-100 text-purple-600' },
  outline: { bg: 'from-blue-500 to-blue-600', icon: 'bg-blue-100 text-blue-600' },
  writer: { bg: 'from-green-500 to-green-600', icon: 'bg-green-100 text-green-600' },
  editor: { bg: 'from-yellow-500 to-yellow-600', icon: 'bg-yellow-100 text-yellow-600' },
  critic: { bg: 'from-red-500 to-red-600', icon: 'bg-red-100 text-red-600' },
  summarizer: { bg: 'from-indigo-500 to-indigo-600', icon: 'bg-indigo-100 text-indigo-600' },
};

const statusColors = {
  idle: { dot: 'bg-gray-400', text: 'text-gray-600' },
  working: { dot: 'bg-blue-500 animate-pulse', text: 'text-blue-600 font-semibold' },
  completed: { dot: 'bg-green-500', text: 'text-green-600 font-semibold' },
  error: { dot: 'bg-red-500', text: 'text-red-600 font-semibold' },
};

const agentIcons = {
  director: '🎬',
  outline: '📋',
  writer: '✍️',
  editor: '📝',
  critic: '🔍',
  summarizer: '📊',
};

export default function AgentStatusCard({ agent }: AgentStatusCardProps) {
  const [elapsedTime, setElapsedTime] = useState<string>('');

  useEffect(() => {
    if (agent.status === 'working' && agent.lastUpdated) {
      const interval = setInterval(() => {
        const start = new Date(agent.lastUpdated!);
        const now = new Date();
        const diff = Math.floor((now.getTime() - start.getTime()) / 1000);
        const minutes = Math.floor(diff / 60);
        const seconds = diff % 60;
        setElapsedTime(`${minutes}m ${seconds}s`);
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [agent.status, agent.lastUpdated]);

  return (
    <div className="bg-gradient-to-br from-gray-50 to-white rounded-lg border border-gray-200 p-2.5 hover:shadow-md transition-all">
      <div className="flex items-center gap-2">
        <div className={`w-8 h-8 rounded-lg ${agentColors[agent.type].icon} flex items-center justify-center text-lg flex-shrink-0`}>
          {agentIcons[agent.type]}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="text-xs font-bold capitalize text-gray-900">{agent.type}</h3>
            {/* Status indicator with tooltip */}
            <div className="relative group">
              <span className={`inline-block w-1.5 h-1.5 rounded-full ${statusColors[agent.status].dot}`} />
              {/* Tooltip - shown on hover */}
              {agent.status === 'working' && elapsedTime && (
                <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover:block z-10 pointer-events-none">
                  <div className="bg-gray-900 text-white text-[10px] px-2 py-1 rounded whitespace-nowrap font-mono">
                    {elapsedTime}
                    <div className="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900" />
                  </div>
                </div>
              )}
            </div>
          </div>
          {agent.status === 'working' && agent.progress !== undefined && (
            <div className="w-full bg-gray-200 rounded-full h-1 mt-1.5 overflow-hidden">
              <div
                className={`h-full bg-gradient-to-r ${agentColors[agent.type].bg} transition-all duration-500 ease-out`}
                style={{ width: `${agent.progress}%` }}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
