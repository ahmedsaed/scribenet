'use client';

import { useEffect, useState } from 'react';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

let toastId = 0;
const toastListeners: Set<(toast: Toast) => void> = new Set();

export function showToast(message: string, type: ToastType = 'success') {
  const toast: Toast = {
    id: `toast-${++toastId}`,
    message,
    type,
  };
  toastListeners.forEach(listener => listener(toast));
}

export default function ToastContainer() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    const listener = (toast: Toast) => {
      setToasts(prev => [...prev, toast]);
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== toast.id));
      }, 4000);
    };

    toastListeners.add(listener);
    return () => {
      toastListeners.delete(listener);
    };
  }, []);

  const typeStyles = {
    success: 'bg-green-50 border-green-200 text-green-800',
    error: 'bg-red-50 border-red-200 text-red-800',
    warning: 'bg-amber-50 border-amber-200 text-amber-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800',
  };

  const icons = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ',
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2">
      {toasts.map(toast => (
        <div
          key={toast.id}
          className={`${typeStyles[toast.type]} border rounded-lg px-6 py-3 shadow-lg animate-toast-in min-w-[300px] max-w-[400px]`}
        >
          <div className="flex items-center space-x-2">
            <span className="text-lg font-bold">{icons[toast.type]}</span>
            <span className="font-medium">{toast.message}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
