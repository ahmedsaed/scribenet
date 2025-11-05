'use client';

import { useState } from 'react';

interface CreateProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (data: { title: string; genre: string; vision_document?: string }) => void;
  isLoading?: boolean;
}

export default function CreateProjectModal({
  isOpen,
  onClose,
  onCreate,
  isLoading = false,
}: CreateProjectModalProps) {
  const [title, setTitle] = useState('');
  const [genre, setGenre] = useState('');
  const [visionDocument, setVisionDocument] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  const popularGenres = [
    'Science Fiction',
    'Fantasy',
    'Mystery',
    'Romance',
    'Thriller',
    'Horror',
    'Historical Fiction',
    'Literary Fiction',
    'Non-Fiction',
    'Biography',
  ];

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    
    if (!title.trim()) {
      newErrors.title = 'Title is required';
    } else if (title.length > 200) {
      newErrors.title = 'Title must be less than 200 characters';
    }
    
    if (!genre.trim()) {
      newErrors.genre = 'Genre is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (validateForm()) {
      onCreate({
        title: title.trim(),
        genre: genre.trim(),
        vision_document: visionDocument.trim() || undefined,
      });
    }
  };

  const handleClose = () => {
    if (!isLoading) {
      setTitle('');
      setGenre('');
      setVisionDocument('');
      setErrors({});
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 animate-fade-in">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto animate-scale-in">
        <form onSubmit={handleSubmit}>
          {/* Header */}
          <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 rounded-t-2xl">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Create New Project</h2>
                <p className="text-sm text-gray-600 mt-1">Start your AI-powered book writing journey</p>
              </div>
              <button
                type="button"
                onClick={handleClose}
                disabled={isLoading}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* Title */}
            <div>
              <label htmlFor="title" className="block text-sm font-semibold text-gray-900 mb-2">
                Project Title <span className="text-red-500">*</span>
              </label>
              <input
                id="title"
                type="text"
                value={title}
                onChange={(e) => {
                  setTitle(e.target.value);
                  if (errors.title) setErrors({ ...errors, title: '' });
                }}
                placeholder="e.g., The Last Starship"
                disabled={isLoading}
                className={`w-full px-4 py-3 rounded-lg border-2 transition-colors text-gray-900 placeholder:text-gray-400 ${
                  errors.title
                    ? 'border-red-300 focus:border-red-500'
                    : 'border-gray-200 focus:border-sky-500'
                } focus:outline-none disabled:bg-gray-50 disabled:text-gray-500`}
                maxLength={200}
              />
              {errors.title && (
                <p className="mt-1 text-sm text-red-600">{errors.title}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">{title.length}/200 characters</p>
            </div>

            {/* Genre */}
            <div>
              <label htmlFor="genre" className="block text-sm font-semibold text-gray-900 mb-2">
                Genre <span className="text-red-500">*</span>
              </label>
              <input
                id="genre"
                type="text"
                value={genre}
                onChange={(e) => {
                  setGenre(e.target.value);
                  if (errors.genre) setErrors({ ...errors, genre: '' });
                }}
                placeholder="e.g., Science Fiction"
                disabled={isLoading}
                list="genres"
                className={`w-full px-4 py-3 rounded-lg border-2 transition-colors text-gray-900 placeholder:text-gray-400 ${
                  errors.genre
                    ? 'border-red-300 focus:border-red-500'
                    : 'border-gray-200 focus:border-sky-500'
                } focus:outline-none disabled:bg-gray-50 disabled:text-gray-500`}
              />
              <datalist id="genres">
                {popularGenres.map((g) => (
                  <option key={g} value={g} />
                ))}
              </datalist>
              {errors.genre && (
                <p className="mt-1 text-sm text-red-600">{errors.genre}</p>
              )}
              
              {/* Genre Pills */}
              <div className="mt-2 flex flex-wrap gap-2">
                {popularGenres.map((g) => (
                  <button
                    key={g}
                    type="button"
                    onClick={() => setGenre(g)}
                    disabled={isLoading}
                    className="px-3 py-1 text-xs rounded-full bg-gray-100 text-gray-700 hover:bg-sky-100 hover:text-sky-700 transition-colors disabled:opacity-50"
                  >
                    {g}
                  </button>
                ))}
              </div>
            </div>

            {/* Vision Document (Optional) */}
            <div>
              <label htmlFor="vision" className="block text-sm font-semibold text-gray-900 mb-2">
                Vision & Goals <span className="text-gray-400 text-xs">(Optional)</span>
              </label>
              <textarea
                id="vision"
                value={visionDocument}
                onChange={(e) => setVisionDocument(e.target.value)}
                placeholder="Describe your book's vision, themes, target audience, or any specific requirements..."
                disabled={isLoading}
                rows={6}
                className="w-full px-4 py-3 rounded-lg border-2 border-gray-200 focus:border-sky-500 focus:outline-none transition-colors text-gray-900 placeholder:text-gray-400 disabled:bg-gray-50 disabled:text-gray-500 resize-none"
              />
              <p className="mt-1 text-xs text-gray-500">
                Help the AI understand your creative vision and writing goals
              </p>
            </div>
          </div>

          {/* Footer */}
          <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 rounded-b-2xl flex gap-3">
            <button
              type="button"
              onClick={handleClose}
              disabled={isLoading}
              className={`flex-1 px-6 py-3 rounded-lg font-medium transition-all ${
                isLoading
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-white text-gray-700 border-2 border-gray-200 hover:bg-gray-50'
              }`}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className={`flex-1 px-6 py-3 rounded-lg font-medium transition-all ${
                isLoading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-gradient-to-r from-sky-500 to-sky-600 hover:from-sky-600 hover:to-sky-700'
              } text-white shadow-md hover:shadow-lg`}
            >
              {isLoading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Creating...
                </span>
              ) : (
                'Create Project'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
