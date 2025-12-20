'use client';

import { ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { theme } from '@/styles/theme';
import { Download, Maximize2 } from 'lucide-react';

interface ChartCardProps {
    title: string;
    description?: string;
    children: ReactNode;
    className?: string;
    onExport?: () => void;
    onFullscreen?: () => void;
}

export function ChartCard({
    title,
    description,
    children,
    className,
    onExport,
    onFullscreen,
}: ChartCardProps) {
    return (
        <div
            className={cn(
                'rounded-xl border border-white/10 overflow-hidden flex flex-col',
                className
            )}
            style={{
                background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.6) 0%, rgba(31, 41, 55, 0.4) 100%)',
            }}
        >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
                <div>
                    <h3 className="font-semibold text-white">{title}</h3>
                    {description && (
                        <p className="text-sm text-gray-400 mt-0.5">{description}</p>
                    )}
                </div>
                <div className="flex items-center gap-2">
                    {onExport && (
                        <button
                            onClick={onExport}
                            className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                            title="Dışa Aktar"
                        >
                            <Download className="w-4 h-4 text-gray-400" />
                        </button>
                    )}
                    {onFullscreen && (
                        <button
                            onClick={onFullscreen}
                            className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                            title="Tam Ekran"
                        >
                            <Maximize2 className="w-4 h-4 text-gray-400" />
                        </button>
                    )}
                </div>
            </div>

            {/* Content */}
            <div className="p-4 flex-1">
                {children}
            </div>
        </div>
    );
}
