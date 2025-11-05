'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ApiClient } from '@/lib/api';
import { brand, getStatusColor } from '@/lib/branding';
import { showToast } from '@/components/ToastContainer';
import ConfirmModal from '@/components/ConfirmModal';
import CreateProjectModal from '@/components/CreateProjectModal';

const api = new ApiClient('http://localhost:8080');

interface Project {
  id: string;
  title: string;
  genre: string;
  status: string;
  created_at: string;
  updated_at?: string;
}

interface ConfirmAction {
  type: 'delete' | 'archive';
  projectId: string;
  projectTitle: string;
}

export default function HomePage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [confirmAction, setConfirmAction] = useState<ConfirmAction | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const data = await api.getProjects();
      setProjects(data);
      setError(null);
    } catch (err) {
      console.error('Failed to load projects:', err);
      setError('Failed to load projects. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProject = async (projectId: string, projectTitle: string) => {
    console.log('Delete button clicked for:', projectId, projectTitle);
    setConfirmAction({ type: 'delete', projectId, projectTitle });
  };

  const handleArchiveProject = async (projectId: string, projectTitle: string) => {
    console.log('Archive button clicked for:', projectId, projectTitle);
    setConfirmAction({ type: 'archive', projectId, projectTitle });
  };

  const executeConfirmedAction = async () => {
    if (!confirmAction) return;

    const { type, projectId, projectTitle } = confirmAction;
    setIsProcessing(true);

    try {
      if (type === 'delete') {
        console.log('Attempting to delete project:', projectId);
        await api.deleteProject(projectId);
        console.log('Project deleted successfully:', projectId);
        
        // Remove from local state
        setProjects(projects.filter(p => p.id !== projectId));
        showToast(`Project "${projectTitle}" deleted successfully`, 'success');
      } else if (type === 'archive') {
        console.log('Attempting to archive project:', projectId);
        await api.updateProject(projectId, { status: 'archived' });
        console.log('Project archived successfully:', projectId);
        
        // Update local state
        setProjects(projects.map(p => 
          p.id === projectId ? { ...p, status: 'archived' } : p
        ));
        showToast(`Project "${projectTitle}" archived successfully`, 'warning');
      }
      
      // Close modal
      setConfirmAction(null);
    } catch (err) {
      console.error(`Failed to ${type} project:`, err);
      showToast(
        `Failed to ${type} project: ${err instanceof Error ? err.message : 'Unknown error'}`,
        'error'
      );
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCreateProject = async (data: { title: string; genre: string; vision_document?: string }) => {
    setIsCreating(true);
    try {
      const newProject = await api.createProject(data);
      showToast(`Project "${data.title}" created successfully!`, 'success');
      setShowCreateModal(false);
      // Navigate to the new project page
      router.push(`/projects/${newProject.id}`);
    } catch (err) {
      console.error('Failed to create project:', err);
      showToast(
        `Failed to create project: ${err instanceof Error ? err.message : 'Unknown error'}`,
        'error'
      );
    } finally {
      setIsCreating(false);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getTimeAgo = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diffInSeconds < 60) return 'just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`;
    return formatDate(dateStr);
  };

  // Filter projects based on search and status
  const filteredProjects = projects.filter(project => {
    const matchesSearch = searchQuery === '' || 
      project.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      project.genre?.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesStatus = selectedStatus === null || project.status === selectedStatus;
    
    return matchesSearch && matchesStatus;
  });

  // Get unique statuses with counts
  const statusCounts = projects.reduce((acc, project) => {
    acc[project.status] = (acc[project.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const availableStatuses = Object.keys(statusCounts).sort();

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-gray-200 border-t-sky-600 mb-4"></div>
          <p className="text-gray-600 font-medium">Loading your projects...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-200px)] bg-gradient-to-b from-gray-50 to-white py-12">
      <div className="max-w-7xl mx-auto px-6 min-h-[600px]">
        {/* Hero Section */}
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold mb-4">
            <span className="bg-gradient-to-r from-sky-600 via-blue-600 to-purple-600 bg-clip-text text-transparent">
              Your Writing Projects
            </span>
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-8">
            Manage and monitor your AI-powered book writing projects
          </p>

          {/* Search Bar */}
          <div className="max-w-2xl mx-auto mb-6">
            <div className="relative">
              <svg
                className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
              <input
                type="text"
                placeholder="Search projects by title or genre..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-12 pr-4 py-4 rounded-xl border-2 border-gray-200 focus:border-sky-500 focus:outline-none transition-colors text-gray-900 placeholder-gray-400"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          </div>

          {/* Status Filter Pills */}
          {projects.length > 0 && (
            <div className="flex flex-wrap items-center justify-center gap-2">
              <button
                onClick={() => setSelectedStatus(null)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                  selectedStatus === null
                    ? 'bg-gradient-to-r from-sky-500 to-sky-600 text-white shadow-md'
                    : 'bg-white text-gray-600 border border-gray-200 hover:border-sky-300 hover:text-sky-600'
                }`}
              >
                All Projects ({projects.length})
              </button>
              {availableStatuses.map((status) => {
                const statusColor = getStatusColor(status);
                const isActive = selectedStatus === status;
                return (
                  <button
                    key={status}
                    onClick={() => setSelectedStatus(status === selectedStatus ? null : status)}
                    className={`px-4 py-2 rounded-full text-sm font-medium transition-all capitalize ${
                      isActive
                        ? `${statusColor.bg} ${statusColor.text} border ${statusColor.border} shadow-md`
                        : 'bg-white text-gray-600 border border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    {status.replace('_', ' ')} ({statusCounts[status]})
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-8 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start space-x-3">
            <span className="text-red-600 text-xl">⚠️</span>
            <div className="flex-1">
              <h3 className="text-red-800 font-semibold mb-1">Connection Error</h3>
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          </div>
        )}

        {/* Projects Grid */}
        {projects.length === 0 ? (
          <div className="text-center py-20">
            <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-gradient-to-br from-sky-100 to-purple-100 mb-6">
              <span className="text-5xl">{brand.logo.icon}</span>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-3">No projects yet</h3>
            <p className="text-gray-600 mb-8 max-w-md mx-auto">
              Start your journey by creating your first AI-powered book writing project
            </p>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 max-w-lg mx-auto">
              <p className="text-sm text-gray-700 mb-3 font-medium">Get started with the CLI:</p>
              <code className="block bg-gray-900 text-green-400 px-4 py-3 rounded text-sm font-mono">
                python cli.py create-project
              </code>
            </div>
          </div>
        ) : filteredProjects.length === 0 ? (
          <div className="text-center py-20">
            <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-gray-100 mb-6">
              <span className="text-5xl">🔍</span>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-3">No projects found</h3>
            <p className="text-gray-600 mb-6">
              {searchQuery 
                ? `No projects match "${searchQuery}"`
                : `No projects with status "${selectedStatus?.replace('_', ' ')}"`
              }
            </p>
            <button
              onClick={() => {
                setSearchQuery('');
                setSelectedStatus(null);
              }}
              className="px-6 py-3 bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-all font-medium"
            >
              Clear Filters
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProjects.map((project) => {
              const statusColor = getStatusColor(project.status);
              const isProcessingThis = isProcessing && 
                confirmAction?.projectId === project.id;
              
              return (
                <div
                  key={project.id}
                  className="group bg-white rounded-xl border border-gray-200 hover:border-sky-300 hover:shadow-xl transition-all duration-300 overflow-hidden"
                >
                  {/* Card Header with Status */}
                  <div className="p-6 pb-4">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <Link href={`/projects/${project.id}`}>
                          <h3 className="text-xl font-bold text-gray-900 mb-2 group-hover:text-sky-600 transition-colors line-clamp-2">
                            {project.title}
                          </h3>
                        </Link>
                        <div className="flex items-center space-x-2 text-sm text-gray-600">
                          <span className="flex items-center">
                            <span className="mr-1.5">📖</span>
                            {project.genre}
                          </span>
                        </div>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${statusColor.bg} ${statusColor.text} border ${statusColor.border} whitespace-nowrap`}>
                        {project.status.replace('_', ' ')}
                      </span>
                    </div>

                    {/* Metadata */}
                    <div className="flex items-center space-x-4 text-xs text-gray-500 mb-4">
                      <span className="flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Created {formatDate(project.created_at)}
                      </span>
                      {project.updated_at && (
                        <span className="flex items-center">
                          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                          {getTimeAgo(project.updated_at)}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Card Footer with Actions */}
                  <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex items-center justify-between">
                    <Link
                      href={`/projects/${project.id}`}
                      className="flex items-center text-sm font-medium text-sky-600 hover:text-sky-700 transition-colors"
                    >
                      <span>Open Dashboard</span>
                      <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </Link>

                    <div className="flex items-center space-x-2">
                      {/* Archive Button */}
                      <button
                        onClick={() => handleArchiveProject(project.id, project.title)}
                        className="p-2 text-gray-400 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition-colors"
                        title="Archive project"
                        disabled={isProcessingThis}
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                        </svg>
                      </button>

                      {/* Delete Button */}
                      <button
                        onClick={() => handleDeleteProject(project.id, project.title)}
                        disabled={isProcessingThis}
                        className={`p-2 rounded-lg transition-colors ${
                          isProcessingThis
                            ? 'text-gray-300 cursor-not-allowed'
                            : 'text-gray-400 hover:text-red-600 hover:bg-red-50'
                        }`}
                        title="Delete project"
                      >
                        {isProcessingThis ? (
                          <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                        ) : (
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Results Summary */}
        {projects.length > 0 && filteredProjects.length > 0 && (searchQuery || selectedStatus) && (
          <div className="mt-8 text-center">
            <p className="text-sm text-gray-600">
              Showing <span className="font-semibold text-gray-900">{filteredProjects.length}</span> of{' '}
              <span className="font-semibold text-gray-900">{projects.length}</span> projects
            </p>
          </div>
        )}

        {/* Stats Summary */}
        {projects.length > 0 && (
          <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg border border-gray-200 p-4 text-center hover:border-sky-300 transition-colors cursor-pointer" onClick={() => setSelectedStatus(null)}>
              <div className="text-3xl font-bold text-gray-900">{projects.length}</div>
              <div className="text-sm text-gray-600 mt-1">Total Projects</div>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-4 text-center hover:border-blue-300 transition-colors cursor-pointer" onClick={() => setSelectedStatus('in_progress')}>
              <div className="text-3xl font-bold text-blue-600">
                {projects.filter(p => p.status === 'in_progress').length}
              </div>
              <div className="text-sm text-gray-600 mt-1">In Progress</div>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-4 text-center hover:border-green-300 transition-colors cursor-pointer" onClick={() => setSelectedStatus('completed')}>
              <div className="text-3xl font-bold text-green-600">
                {projects.filter(p => p.status === 'completed').length}
              </div>
              <div className="text-sm text-gray-600 mt-1">Completed</div>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-4 text-center hover:border-amber-300 transition-colors cursor-pointer" onClick={() => setSelectedStatus('planning')}>
              <div className="text-3xl font-bold text-amber-600">
                {projects.filter(p => p.status === 'planning').length}
              </div>
              <div className="text-sm text-gray-600 mt-1">Planning</div>
            </div>
          </div>
        )}
      </div>

      {/* Confirmation Modal */}
      <ConfirmModal
        isOpen={confirmAction !== null}
        onClose={() => !isProcessing && setConfirmAction(null)}
        onConfirm={executeConfirmedAction}
        title={
          confirmAction?.type === 'delete' 
            ? 'Delete Project?' 
            : 'Archive Project?'
        }
        message={
          confirmAction?.type === 'delete'
            ? `Are you sure you want to delete "${confirmAction.projectTitle}"? This action cannot be undone and all project data will be permanently removed.`
            : `Archive "${confirmAction?.projectTitle}"? You can restore it later if needed.`
        }
        confirmText={confirmAction?.type === 'delete' ? 'Delete' : 'Archive'}
        cancelText="Cancel"
        type={confirmAction?.type === 'delete' ? 'danger' : 'warning'}
        isLoading={isProcessing}
      />

      {/* Create Project Modal */}
      <CreateProjectModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreate={handleCreateProject}
        isLoading={isCreating}
      />
    </div>
  );
}
