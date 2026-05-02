'use client';

import { useMemo, useState } from 'react';
import { BrainCircuit, Play, Target } from 'lucide-react';
import type { ProblemType, SavedModelSummary } from '@/types/model-selection';
import { cn } from '@/lib/utils';

interface SavedModelsPanelProps {
    models: SavedModelSummary[];
    selectedColumn: string | null;
    loading?: boolean;
    disabled?: boolean;
    onSelect: (savedModelId: string) => Promise<void> | void;
}

function formatMetric(problemType: ProblemType, metrics: SavedModelSummary['metrics']): string {
    if (problemType === 'classification') {
        return `Accuracy ${(metrics.accuracy ?? 0).toFixed(3)}`;
    }

    return `R2 ${(metrics.r2 ?? 0).toFixed(3)}`;
}

function formatDate(value: string | null): string {
    if (!value) {
        return 'Tarih yok';
    }

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return 'Tarih yok';
    }

    return new Intl.DateTimeFormat('tr-TR', {
        dateStyle: 'medium',
        timeStyle: 'short',
    }).format(date);
}

function truncateText(text: string, maxLength: number): string {
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength) + '...';
}

export function SavedModelsPanel({
    models,
    selectedColumn,
    loading = false,
    disabled = false,
    onSelect,
}: SavedModelsPanelProps) {
    const [pendingModelId, setPendingModelId] = useState<string | null>(null);

    const visibleModels = useMemo(() => {
        if (!selectedColumn) {
            return models;
        }

        return models.filter((model) => model.targetColumn === selectedColumn);
    }, [models, selectedColumn]);

    const handleSelect = async (savedModelId: string) => {
        try {
            setPendingModelId(savedModelId);
            await onSelect(savedModelId);
        } finally {
            setPendingModelId(null);
        }
    };

    return (
        <div className="space-y-4">
            <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                <div>
                    <div className="flex items-center gap-2">
                        <BrainCircuit className="h-5 w-5 text-cyan-400" />
                        <h3 className="text-lg font-semibold text-white">Kayıtlı Modeller</h3>
                    </div>
                    <p className="mt-1 text-sm text-gray-400">
                        Mevcut veri seti için kaydedilmiş modeller. Target seçince liste o kolona göre
                        filtrelenir.
                    </p>
                </div>

                <div className="flex items-center gap-2 text-xs text-gray-400">
                    <Target className="h-4 w-4" />
                    <span className="rounded-full border border-white/10 px-2.5 py-1">
                        {selectedColumn ? `Filtre: ${selectedColumn}` : 'Tüm targetlar'}
                    </span>
                </div>
            </div>

            {loading ? (
                <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-5 text-sm text-gray-400">
                    Kayıtlı modeller yükleniyor...
                </div>
            ) : null}

            {!loading && visibleModels.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-white/10 bg-white/[0.03] px-4 py-5 text-sm text-gray-400">
                    {selectedColumn
                        ? 'Seçili target için kayıtlı model bulunmuyor.'
                        : 'Bu veri seti için kayıtlı model bulunmuyor.'}
                </div>
            ) : null}

            {visibleModels.length > 0 ? (
                <div className="flex gap-3 overflow-x-auto">
                    {visibleModels.map((model) => {
                        const isPending = pendingModelId === model.id;

                        return (
                            <article
                                key={model.id}
                                className="min-w-[340px] flex-shrink-0 rounded-2xl border border-white/10 bg-white/[0.04] p-4 transition-colors"
                            >
                                <div className="flex flex-col gap-4">
                                    <div className="flex items-start justify-between gap-3">
                                        <div className="min-w-0 flex-1">
                                            <div className="flex flex-wrap items-center gap-2">
                                                <h4
                                                    className="truncate text-base font-semibold text-white"
                                                    title={model.modelName}
                                                >
                                                    {truncateText(model.modelName, 30)}
                                                </h4>
                                                <span className="rounded-full border border-cyan-400/30 bg-cyan-400/15 px-2.5 py-1 text-[11px] font-medium text-cyan-100">
                                                    {model.targetColumn}
                                                </span>
                                                <span className="rounded-full border border-white/10 px-2.5 py-1 text-[11px] text-gray-300">
                                                    {model.problemType === 'classification'
                                                        ? 'Sınıflandırma'
                                                        : 'Regresyon'}
                                                </span>
                                            </div>

                                            <div className="mt-2 flex flex-wrap gap-2 text-xs text-gray-400">
                                                <span className="rounded-full border border-white/10 px-2.5 py-1">
                                                    {formatMetric(model.problemType, model.metrics)}
                                                </span>
                                                <span className="rounded-full border border-white/10 px-2.5 py-1">
                                                    Süre {model.trainingTime?.toFixed(1) ?? '0.0'} sn
                                                </span>
                                                <span className="rounded-full border border-white/10 px-2.5 py-1">
                                                    Son kayıt: {formatDate(model.createdAt)}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex flex-wrap items-center gap-2">
                                        <button
                                            type="button"
                                            onClick={() => void handleSelect(model.id)}
                                            disabled={disabled || isPending}
                                            className={cn(
                                                'inline-flex cursor-pointer items-center gap-2 rounded-xl bg-cyan-400 px-3.5 py-2 text-sm font-medium text-slate-950 transition hover:bg-cyan-300',
                                                (disabled || isPending) &&
                                                    'cursor-not-allowed opacity-50'
                                            )}
                                        >
                                            <Play className="h-4 w-4" />
                                            {isPending ? 'Açılıyor...' : 'Sonuçları Aç'}
                                        </button>
                                    </div>
                                </div>
                            </article>
                        );
                    })}
                </div>
            ) : null}
        </div>
    );
}
