'use client';

import { Loader2 } from 'lucide-react';
import { theme } from '@/styles/theme';

interface TrainingProgressProps {
    isTraining: boolean;
    status?: 'idle' | 'queued' | 'running' | 'stopping' | 'completed' | 'failed' | 'stopped';
    currentModel?: string;
    totalModels: number;
    completedModels: number;
}

export function TrainingProgress({
    isTraining,
    status = 'idle',
    currentModel,
    totalModels,
    completedModels,
}: TrainingProgressProps) {
    const progress = totalModels > 0 ? (completedModels / totalModels) * 100 : 0;
    const title =
        status === 'queued'
            ? 'Egitim kuyruga alindi'
            : status === 'stopping'
              ? 'Egitim durduruluyor...'
              : status === 'completed'
                ? 'Egitim tamamlandi'
                : status === 'stopped'
                  ? 'Egitim durduruldu'
                  : status === 'failed'
                    ? 'Egitim basarisiz oldu'
                    : isTraining
                      ? 'Modeller egitiliyor...'
                      : 'Egitim tamamlandi';

    if (!isTraining && completedModels === 0) {
        return null;
    }

    return (
        <div
            className="p-6 rounded-xl border"
            style={{
                borderColor: `${theme.colors.primary.cyan}30`,
                background: `${theme.colors.primary.cyan}05`,
            }}
        >
            <div className="mb-4 flex items-center gap-4">
                {isTraining && (
                    <Loader2
                        className="h-8 w-8 animate-spin"
                        style={{ color: theme.colors.primary.cyan }}
                    />
                )}
                <div>
                    <h3 className="font-semibold text-white">{title}</h3>
                    {currentModel && isTraining && (
                        <p className="text-sm text-gray-400">Su an: {currentModel}</p>
                    )}
                </div>
            </div>

            <div className="space-y-2">
                <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Ilerleme</span>
                    <span className="text-cyan-400">
                        {completedModels} / {totalModels} model
                    </span>
                </div>
                <div className="h-3 overflow-hidden rounded-full bg-white/10">
                    <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{
                            width: `${progress}%`,
                            background: theme.gradients.primary,
                            boxShadow: `0 0 10px ${theme.colors.primary.cyan}50`,
                        }}
                    />
                </div>
            </div>
        </div>
    );
}
