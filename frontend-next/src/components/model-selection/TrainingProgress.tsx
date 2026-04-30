'use client';

import React from 'react';
import { CheckCircle2, Circle, Loader2 } from 'lucide-react';
import { theme } from '@/styles/theme';

interface TrainingProgressProps {
    isTraining: boolean;
    status?: 'idle' | 'queued' | 'running' | 'stopping' | 'completed' | 'failed' | 'stopped';
    currentModel?: string;
    totalModels: number;
    completedModels: number;
}

type TrainingStatus = NonNullable<TrainingProgressProps['status']>;
type TrainingStageId = 'queued' | 'preparing' | 'training' | 'results';

const TRAINING_STAGES: Array<{ id: TrainingStageId; label: string; detail: string }> = [
    { id: 'queued', label: 'Kuyruk', detail: 'İş sıraya alındı' },
    { id: 'preparing', label: 'Hazırlık', detail: 'Veri hazırlanıyor' },
    { id: 'training', label: 'Eğitim', detail: 'Modeller çalışıyor' },
    { id: 'results', label: 'Sonuç', detail: 'Çıktılar kaydediliyor' },
];

function getActiveStage(
    status: TrainingStatus,
    currentModel: string | undefined,
    totalModels: number,
    completedModels: number
): TrainingStageId {
    if (status === 'queued') {
        return 'queued';
    }
    if (status === 'completed' || status === 'failed' || status === 'stopped') {
        return 'results';
    }
    if (status === 'stopping') {
        return currentModel ? 'training' : 'results';
    }
    if (status === 'running') {
        if (totalModels > 0 && completedModels >= totalModels) {
            return 'results';
        }
        return currentModel ? 'training' : 'preparing';
    }
    return 'queued';
}

export const TrainingProgress = React.memo(function TrainingProgress({
    isTraining,
    status = 'idle',
    currentModel,
    totalModels,
    completedModels,
}: TrainingProgressProps) {
    const progress = totalModels > 0 ? (completedModels / totalModels) * 100 : 0;
    const activeStage = getActiveStage(status, currentModel, totalModels, completedModels);
    const activeStageIndex = TRAINING_STAGES.findIndex((stage) => stage.id === activeStage);
    const resultStageDetail =
        status === 'completed'
            ? 'Eğitim tamamlandı'
            : status === 'stopped'
              ? 'Eğitim durduruldu'
              : status === 'failed'
                ? 'Eğitim başarısız oldu'
                : 'Çıktılar kaydediliyor';
    const title =
        status === 'queued'
            ? 'Eğitim kuyruğa alındı'
            : status === 'stopping'
              ? 'Eğitim durduruluyor...'
              : status === 'completed'
                ? 'Eğitim tamamlandı'
                : status === 'stopped'
                  ? 'Eğitim durduruldu'
                  : status === 'failed'
                    ? 'Eğitim başarısız oldu'
                    : isTraining
                      ? 'Modeller eğitiliyor...'
                      : 'Eğitim tamamlandı';

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
                        <p className="text-sm text-gray-400">Şu an: {currentModel}</p>
                    )}
                </div>
            </div>

            <ol className="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
                {TRAINING_STAGES.map((stage, index) => {
                    const isCompleted = index < activeStageIndex || status === 'completed';
                    const isActive = index === activeStageIndex && status !== 'completed';
                    const detail = stage.id === 'results' ? resultStageDetail : stage.detail;

                    return (
                        <li key={stage.id} className="relative min-w-0">
                            {index > 0 && (
                                <div
                                    className="absolute top-4 right-[calc(50%+1.25rem)] left-[calc(-50%+1.25rem)] hidden h-px sm:block"
                                    style={{
                                        background: isCompleted
                                            ? theme.gradients.primary
                                            : 'rgba(255, 255, 255, 0.12)',
                                    }}
                                />
                            )}
                            <div className="relative flex flex-col items-center gap-2 text-center">
                                <div
                                    className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border"
                                    style={{
                                        borderColor: isCompleted || isActive
                                            ? theme.colors.primary.cyan
                                            : 'rgba(255, 255, 255, 0.18)',
                                        background: isCompleted
                                            ? theme.colors.primary.cyan
                                            : isActive
                                              ? `${theme.colors.primary.cyan}20`
                                              : 'rgba(255, 255, 255, 0.04)',
                                        boxShadow: isActive ? `0 0 16px ${theme.colors.primary.cyan}35` : 'none',
                                    }}
                                >
                                    {isCompleted ? (
                                        <CheckCircle2 className="h-4 w-4 text-slate-950" />
                                    ) : isActive ? (
                                        <Loader2 className="h-4 w-4 animate-spin text-cyan-300" />
                                    ) : (
                                        <Circle className="h-3 w-3 text-gray-500" />
                                    )}
                                </div>
                                <div className="min-w-0">
                                    <p className={isActive || isCompleted ? 'text-xs font-semibold text-white' : 'text-xs font-semibold text-gray-500'}>
                                        {stage.label}
                                    </p>
                                    <p className={isActive ? 'text-[11px] leading-4 text-cyan-200' : 'text-[11px] leading-4 text-gray-500'}>
                                        {detail}
                                    </p>
                                </div>
                            </div>
                        </li>
                    );
                })}
            </ol>

            <div className="space-y-2">
                <div className="flex justify-between text-sm">
                    <span className="text-gray-400">İlerleme</span>
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
});
