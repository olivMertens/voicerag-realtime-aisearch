import * as React from 'react';
import { cn } from '@/lib/utils';

interface DialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
}

const Dialog: React.FC<DialogProps> = ({ open, onOpenChange, children }) => {
  if (!open) return null;
  
  // Handle escape key
  React.useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onOpenChange(false);
      }
    };
    
    if (open) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }
    
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = previousOverflow;
    };
  }, [open, onOpenChange]);
  
  return (
    <div className="fixed inset-0 z-[9999]" role="dialog" aria-modal="true">
      <div 
        className="fixed inset-0 bg-black/80 backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
      />
      {children}
    </div>
  );
};

interface DialogContentProps {
  className?: string;
  children: React.ReactNode;
}

const DialogContent: React.FC<DialogContentProps> = ({ className, children }) => (
  <div className={cn(
    'fixed left-[50%] top-[50%] z-[10000] grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 rounded-lg border border-slate-200 bg-white p-6 shadow-lg max-h-[90vh] overflow-hidden',
    className
  )}>
    {children}
  </div>
);

const DialogHeader: React.FC<{ className?: string; children: React.ReactNode }> = ({ className, children }) => (
  <div className={cn('flex flex-col space-y-1.5 text-center sm:text-left', className)}>
    {children}
  </div>
);

const DialogTitle: React.FC<{ className?: string; children: React.ReactNode }> = ({ className, children }) => (
  <h2 className={cn('text-lg font-semibold leading-none tracking-tight', className)}>
    {children}
  </h2>
);

export {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
};