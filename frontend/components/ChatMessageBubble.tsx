'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ChatMessageBubbleProps {
  message: string;
  sender: 'user' | 'ai';
  timestamp: string;
}

export default function ChatMessageBubble({ message, sender, timestamp }: ChatMessageBubbleProps) {
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  if (sender === 'user') {
    return (
      <div className="flex items-start gap-2 flex-row-reverse">
        <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center flex-shrink-0">
          <span className="text-gray-600 text-sm">👤</span>
        </div>
        <div className="flex-1">
          <div className="bg-gradient-to-r from-sky-500 to-purple-600 text-white rounded-lg p-3">
            <p className="text-sm whitespace-pre-wrap">{message}</p>
          </div>
          <p className="text-xs text-gray-400 mt-1 text-right">
            {formatTime(timestamp)}
          </p>
        </div>
      </div>
    );
  }

  // AI message with markdown support
  return (
    <div className="flex items-start gap-2">
      <div className="w-8 h-8 rounded-full bg-gradient-to-r from-sky-500 to-purple-600 flex items-center justify-center flex-shrink-0">
        <span className="text-white text-sm">🎬</span>
      </div>
      <div className="flex-1">
        <div className="bg-gray-50 border border-gray-200 text-gray-900 rounded-lg p-3">
          <div className="prose prose-sm max-w-none
            prose-headings:text-gray-900 prose-headings:font-bold
            prose-h1:text-lg prose-h1:mt-0 prose-h1:mb-2
            prose-h2:text-base prose-h2:mt-0 prose-h2:mb-2
            prose-h3:text-sm prose-h3:mt-0 prose-h3:mb-1
            prose-p:text-sm prose-p:text-gray-800 prose-p:my-2 prose-p:leading-relaxed
            prose-a:text-sky-600 prose-a:no-underline hover:prose-a:underline
            prose-strong:text-gray-900 prose-strong:font-semibold
            prose-em:text-gray-800
            prose-code:text-sm prose-code:bg-gray-100 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-pink-600 prose-code:before:content-none prose-code:after:content-none
            prose-pre:bg-gray-900 prose-pre:text-gray-100 prose-pre:text-xs prose-pre:p-3 prose-pre:rounded-lg prose-pre:overflow-x-auto
            prose-ul:my-2 prose-ul:text-sm prose-ul:text-gray-800
            prose-ol:my-2 prose-ol:text-sm prose-ol:text-gray-800
            prose-li:my-1 prose-li:text-gray-800
            prose-blockquote:border-l-4 prose-blockquote:border-sky-500 prose-blockquote:pl-4 prose-blockquote:italic prose-blockquote:text-gray-700
            prose-table:text-sm prose-table:my-2
            prose-th:bg-gray-100 prose-th:p-2 prose-th:text-left prose-th:font-semibold
            prose-td:p-2 prose-td:border prose-td:border-gray-200
            prose-hr:my-4 prose-hr:border-gray-300
            first:prose-p:mt-0 last:prose-p:mb-0">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message}
            </ReactMarkdown>
          </div>
        </div>
        <p className="text-xs text-gray-400 mt-1">
          {formatTime(timestamp)}
        </p>
      </div>
    </div>
  );
}
