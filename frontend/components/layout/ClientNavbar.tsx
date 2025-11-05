'use client';

import { useState } from 'react';
import Navbar from './Navbar';
import CreateProjectModal from '../CreateProjectModal';
import { useRouter } from 'next/navigation';

export default function ClientNavbar() {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const router = useRouter();

  const handleCreateProject = async (data: { title: string; genre: string; visionDocument?: string }) => {
    setIsCreating(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';
      const response = await fetch(`${apiUrl}/api/projects`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to create project');
      }

      const project = await response.json();
      
      // Show success toast
      if (typeof window !== 'undefined' && (window as any).showToast) {
        (window as any).showToast(`Project "${data.title}" created successfully!`, 'success');
      }
      
      // Close modal and navigate to the new project
      setShowCreateModal(false);
      router.push(`/projects/${project.id}`);
    } catch (error) {
      console.error('Failed to create project:', error);
      if (typeof window !== 'undefined' && (window as any).showToast) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to create project';
        (window as any).showToast(errorMessage, 'error');
      }
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <>
      <Navbar onCreateProject={() => setShowCreateModal(true)} />
      <CreateProjectModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreate={handleCreateProject}
        isLoading={isCreating}
      />
    </>
  );
}
