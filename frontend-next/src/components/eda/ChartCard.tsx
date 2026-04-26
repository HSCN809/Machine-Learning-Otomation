'use client';

import { ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { Download, Maximize2 } from 'lucide-react';

interface ChartCardProps {
    title: string;
    description?: string;
    children: ReactNode;
    className?: string;
    headerActions?: ReactNode;
    onExport?: () => void;
    onFullscreen?: () => void;
}

export function ChartCard({
    title,
    description,
    children,
    className,
    headerActions,
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
            <div className="flex flex-col gap-3 border-b border-white/10 px-4 py-3 md:flex-row md:items-start md:justify-between">
                <div>
                    <h3 className="font-semibold text-white">{title}</h3>
                    {description && (
                        <p className="mt-0.5 text-sm text-gray-400">{description}</p>
                    )}
                </div>
                <div className="flex flex-wrap items-center gap-2 md:justify-end">
                    {headerActions}
                    {onExport && (
                        <button
                            onClick={onExport}
                            className="rounded-lg p-2 transition-colors hover:bg-white/10"
                            title="Dışa Aktar"
                        >
                            <Download className="h-4 w-4 text-gray-400" />
                        </button>
                    )}
                    {onFullscreen && (
                        <button
                            onClick={onFullscreen}
                            className="rounded-lg p-2 transition-colors hover:bg-white/10"
                            title="Tam Ekran"
                        >
                            <Maximize2 className="h-4 w-4 text-gray-400" />
                        </button>
                    )}
                </div>
            </div>

            <div className="flex-1 p-4">{children}</div>
        </div>
    );
}
