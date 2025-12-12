'use client';

import { Loader2, CheckCircle, AlertCircle, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';
import { theme } from '@/styles/theme';
import { UploadStatus, UploadedFile } from '@/types/data-upload';

interface UploadProgressProps {
    status: UploadStatus;
    progress: number;
    file?: UploadedFile | null;
    error?: string | null;
}

export function UploadProgress({ status, progress, file, error }: UploadProgressProps) {
    if (status === 'idle') return null;

    const statusConfig = {
        uploading: {
            icon: Loader2,
            iconClass: 'animate-spin text-cyan-400',
            label: 'Yükleniyor...',
            color: theme.colors.primary.cyan,
        },
        validating: {
            icon: Loader2,
            iconClass: 'animate-spin text-purple-400',
            label: 'Doğrulanıyor...',
            color: theme.colors.accent.purple,
        },
        success: {
            icon: CheckCircle,
            iconClass: 'text-green-400',
            label: 'Başarılı!',
            color: theme.colors.secondary.green,
        },
        error: {
            icon: AlertCircle,
            iconClass: 'text-red-400',
            label: 'Hata!',
            color: theme.colors.status.error,
        },
    };

    const config = statusConfig[status];
    const Icon = config.icon;

    return (
        <div
            className={cn(
                'p-4 rounded-xl border transition-all duration-300',
                status === 'success' && 'border-green-500/30 bg-green-500/5',
                status === 'error' && 'border-red-500/30 bg-red-500/5',
                (status === 'uploading' || status === 'validating') && 'border-white/10 bg-white/5'
            )}
        >
            <div className="flex items-center gap-4">
                {/* Icon */}
                <div
                    className="p-3 rounded-lg"
                    style={{
                        background: `${config.color}20`,
                        boxShadow: `0 0 15px ${config.color}30`,
                    }}
                >
                    <Icon className={cn('w-6 h-6', config.iconClass)} />
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                        <p className="font-medium text-white truncate">
                            {file?.name || config.label}
                        </p>
                        <span className="text-sm" style={{ color: config.color }}>
                            {status === 'success' ? '✓ Tamamlandı' : `${progress}%`}
                        </span>
                    </div>

                    {/* Progress bar */}
                    {(status === 'uploading' || status === 'validating') && (
                        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                            <div
                                className="h-full rounded-full transition-all duration-300"
                                style={{
                                    width: `${progress}%`,
                                    background: `linear-gradient(90deg, ${theme.colors.primary.cyan} 0%, ${theme.colors.secondary.green} 100%)`,
                                    boxShadow: `0 0 10px ${theme.colors.primary.cyan}50`,
                                }}
                            />
                        </div>
                    )}

                    {/* File info */}
                    {file && status === 'success' && (
                        <div className="flex items-center gap-3 mt-2 text-sm text-gray-400">
                            <span className="flex items-center gap-1">
                                <FileText className="w-4 h-4" />
                                {(file.size / 1024).toFixed(1)} KB
                            </span>
                        </div>
                    )}

                    {/* Error message */}
                    {error && (
                        <p className="text-sm text-red-400 mt-1">{error}</p>
                    )}
                </div>
            </div>
        </div>
    );
}
