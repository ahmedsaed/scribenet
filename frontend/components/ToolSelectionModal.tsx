'use client';

import { useState, useEffect } from 'react';

interface Tool {
  name: string;
  description: string;
  server: string;
}

interface ToolsByServer {
  [serverName: string]: Tool[];
}

interface ToolSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
  selectedTools: string[];
  onSave: (tools: string[]) => void;
}

export default function ToolSelectionModal({
  isOpen,
  onClose,
  projectId,
  selectedTools,
  onSave,
}: ToolSelectionModalProps) {
  const [toolsByServer, setToolsByServer] = useState<ToolsByServer>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [localSelectedTools, setLocalSelectedTools] = useState<Set<string>>(
    new Set(selectedTools)
  );
  const [expandedServers, setExpandedServers] = useState<Set<string>>(new Set());

  // Update local selected tools when prop changes
  useEffect(() => {
    setLocalSelectedTools(new Set(selectedTools));
  }, [selectedTools]);

  // Fetch available tools when modal opens
  useEffect(() => {
    if (isOpen) {
      fetchTools();
    }
  }, [isOpen, projectId]);

  const fetchTools = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`http://localhost:8080/api/projects/${projectId}/chat/tools`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch tools');
      }
      
      const data = await response.json();
      
      if (!data.enabled) {
        setError('MCP tools are not enabled in the configuration');
        setToolsByServer({});
      } else {
        setToolsByServer(data.servers || {});
        // Expand all servers by default
        setExpandedServers(new Set(Object.keys(data.servers || {})));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tools');
      setToolsByServer({});
    } finally {
      setLoading(false);
    }
  };

  const handleToggleServer = (serverName: string) => {
    const tools = toolsByServer[serverName] || [];
    const toolNames = tools.map((t) => t.name);
    
    // Check if all tools in this server are selected
    const allSelected = toolNames.every((name) => localSelectedTools.has(name));
    
    const newSelected = new Set(localSelectedTools);
    
    if (allSelected) {
      // Deselect all tools from this server
      toolNames.forEach((name) => newSelected.delete(name));
    } else {
      // Select all tools from this server
      toolNames.forEach((name) => newSelected.add(name));
    }
    
    setLocalSelectedTools(newSelected);
  };

  const handleToggleTool = (toolName: string) => {
    const newSelected = new Set(localSelectedTools);
    
    if (newSelected.has(toolName)) {
      newSelected.delete(toolName);
    } else {
      newSelected.add(toolName);
    }
    
    setLocalSelectedTools(newSelected);
  };

  const handleToggleServerExpansion = (serverName: string) => {
    const newExpanded = new Set(expandedServers);
    
    if (newExpanded.has(serverName)) {
      newExpanded.delete(serverName);
    } else {
      newExpanded.add(serverName);
    }
    
    setExpandedServers(newExpanded);
  };

  const handleSelectAll = () => {
    const allTools = Object.values(toolsByServer)
      .flat()
      .map((tool) => tool.name);
    setLocalSelectedTools(new Set(allTools));
  };

  const handleDeselectAll = () => {
    setLocalSelectedTools(new Set());
  };

  const handleSave = () => {
    onSave(Array.from(localSelectedTools));
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-900/40 backdrop-blur-[2px] flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <span className="text-2xl">⚙️</span>
              Configure Tools
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Select which MCP tools are available for this chat session
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600"></div>
              <span className="ml-3 text-gray-600">Loading tools...</span>
            </div>
          ) : error ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
              <p className="text-red-800 font-medium">⚠️ {error}</p>
            </div>
          ) : Object.keys(toolsByServer).length === 0 ? (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center">
              <p className="text-yellow-800 font-medium">No tools available</p>
              <p className="text-yellow-700 text-sm mt-1">
                Check your MCP configuration in config.yaml
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Action Buttons */}
              <div className="flex gap-2 mb-4">
                <button
                  onClick={handleSelectAll}
                  className="px-3 py-1.5 text-xs font-medium text-sky-700 bg-sky-50 border border-sky-200 rounded-lg hover:bg-sky-100 transition-colors"
                >
                  Select All
                </button>
                <button
                  onClick={handleDeselectAll}
                  className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-gray-50 border border-gray-200 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  Deselect All
                </button>
                <div className="flex-1"></div>
                <div className="text-xs text-gray-600 flex items-center">
                  {localSelectedTools.size} tools selected
                </div>
              </div>

              {/* Servers and Tools */}
              {Object.entries(toolsByServer).map(([serverName, tools]) => {
                const allToolsSelected = tools.every((tool) =>
                  localSelectedTools.has(tool.name)
                );
                const someToolsSelected =
                  !allToolsSelected &&
                  tools.some((tool) => localSelectedTools.has(tool.name));
                const isExpanded = expandedServers.has(serverName);

                return (
                  <div
                    key={serverName}
                    className="border border-gray-200 rounded-lg overflow-hidden"
                  >
                    {/* Server Header */}
                    <div className="bg-gray-50 p-3 flex items-center gap-3">
                      <button
                        onClick={() => handleToggleServerExpansion(serverName)}
                        className="text-gray-500 hover:text-gray-700 transition-colors"
                      >
                        <span className="text-lg">
                          {isExpanded ? '▼' : '▶'}
                        </span>
                      </button>
                      <label className="flex items-center gap-3 cursor-pointer flex-1">
                        <input
                          type="checkbox"
                          checked={allToolsSelected}
                          ref={(el) => {
                            if (el) el.indeterminate = someToolsSelected;
                          }}
                          onChange={() => handleToggleServer(serverName)}
                          className="w-4 h-4 text-sky-600 border-gray-300 rounded focus:ring-sky-500"
                        />
                        <div className="flex-1">
                          <p className="font-semibold text-gray-900">
                            {serverName}
                          </p>
                          <p className="text-xs text-gray-600">
                            {tools.length} tool{tools.length !== 1 ? 's' : ''}
                          </p>
                        </div>
                      </label>
                    </div>

                    {/* Tools List */}
                    {isExpanded && (
                      <div className="divide-y divide-gray-100">
                        {tools.map((tool) => (
                          <label
                            key={tool.name}
                            className="flex items-start gap-3 p-3 hover:bg-gray-50 cursor-pointer transition-colors"
                          >
                            <input
                              type="checkbox"
                              checked={localSelectedTools.has(tool.name)}
                              onChange={() => handleToggleTool(tool.name)}
                              className="w-4 h-4 text-sky-600 border-gray-300 rounded focus:ring-sky-500 mt-0.5"
                            />
                            <div className="flex-1 min-w-0">
                              <p className="font-medium text-sm text-gray-900">
                                {tool.name}
                              </p>
                              <p className="text-xs text-gray-600 mt-0.5">
                                {tool.description || 'No description available'}
                              </p>
                            </div>
                          </label>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 flex items-center justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-sky-600 to-purple-600 rounded-lg hover:from-sky-700 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Save Selection
          </button>
        </div>
      </div>
    </div>
  );
}
