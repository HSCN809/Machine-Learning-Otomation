'use client';

import { useMemo, useState } from 'react';
import { Check, Database, Pencil, Play, Trash2, X } from 'lucide-react';
import type { PersistedDatasetSummary } from '@/types/data-upload';
import { cn } from '@/lib/utils';

interface SavedDatasetsProps {
    datasets: PersistedDatasetSummary[];
    activeDatasetId: string | null;
    loading?: boolean;
    disabled?: boolean;
    onLoad: (datasetId: string) => Promise<void> | void;
    onRename: (datasetId: string, name: string) => Promise<void> | void;
    onDelete: (datasetId: string) => Promise<void> | void;
}

type PendingAction =
    | { type: 'load' | 'rename' | 'delete'; datasetId: string }
    | null;

function formatUpdatedAt(value: string): string {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return 'Tarih bilinmiyor';
    }

    return new Intl.DateTimeFormat('tr-TR', {
        dateStyle: 'medium',
        timeStyle: 'short',
    }).format(date);
}

export function SavedDatasets({
    datasets,
    activeDatasetId,
    loading = false,
    disabled = false,
    onLoad,
    onRename,
    onDelete,
}: SavedDatasetsProps) {
    const [renamingDatasetId, setRenamingDatasetId] = useState<string | null>(null);
    const [renameValue, setRenameValue] = useState('');
    const [pendingAction, setPendingAction] = useState<PendingAction>(null);

    const pendingDatasetId = pendingAction?.datasetId ?? null;
    const isActionLocked = disabled || pendingAction !== null;
    const sortedDatasets = useMemo(
        () =>
            [...datasets].sort(
                (left, right) => new Date(right.updatedAt).getTime() - new Date(left.updatedAt).getTime()
            ),
        [datasets]
    );

    const startRename = (dataset: PersistedDatasetSummary) => {
        if (isActionLocked) {
            return;
        }

        setRenamingDatasetId(dataset.id);
        setRenameValue(dataset.name);
    };

    const cancelRename = () => {
        if (pendingAction?.type === 'rename') {
            return;
        }

        setRenamingDatasetId(null);
        setRenameValue('');
    };

    const submitRename = async (datasetId: string) => {
        const nextName = renameValue.trim();
        if (!nextName) {
            return;
        }

        try {
            setPendingAction({ type: 'rename', datasetId });
            await onRename(datasetId, nextName);
            setRenamingDatasetId(null);
            setRenameValue('');
        } finally {
            setPendingAction(null);
        }
    };

    const handleLoad = async (datasetId: string) => {
        try {
            setPendingAction({ type: 'load', datasetId });
            await onLoad(datasetId);
        } finally {
            setPendingAction(null);
        }
    };

    const handleDelete = async (datasetId: string) => {
        try {
            setPendingAction({ type: 'delete', datasetId });
            await onDelete(datasetId);
            if (renamingDatasetId === datasetId) {
                setRenamingDatasetId(null);
                setRenameValue('');
            }
        } finally {
            setPendingAction(null);
        }
    };

    return (
        <div className="space-y-4">
            <div className="flex items-center gap-2">
                <Database className="h-5 w-5 text-cyan-400" />
                <h2 className="text-lg font-semibold text-white">Kayıtlı Veri Setleri</h2>
            </div>

            <p className="text-sm text-gray-400">
                Veritabanındaki kayıtlı veri setlerinden birini seçip doğrudan veri editörüne yükleyebilirsiniz.
            </p>

            {loading && sortedDatasets.length === 0 ? (
                <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-5 text-sm text-gray-400">
                    Kayıtlı veri setleri yükleniyor...
                </div>
            ) : null}

            {!loading && sortedDatasets.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-white/10 bg-white/[0.03] px-4 py-5 text-sm text-gray-400">
                    Henüz kayıtlı veri seti bulunmuyor.
                </div>
            ) : null}

            {sortedDatasets.length > 0 ? (
                <div className="grid gap-3 xl:grid-cols-2">
                    {sortedDatasets.map((dataset) => {
                        const isActive = dataset.id === activeDatasetId;
                        const isRenaming = dataset.id === renamingDatasetId;
                        const isPending = dataset.id === pendingDatasetId;

                        return (
                            <article
                                key={dataset.id}
                                className={cn(
                                    'rounded-2xl border p-4 transition-colors',
                                    isActive
                                        ? 'border-cyan-400/40 bg-cyan-400/10'
                                        : 'border-white/10 bg-white/[0.04]'
                                )}
                            >
                                <div className="flex flex-col gap-4">
                                    <div className="flex items-start justify-between gap-3">
                                        <div className="min-w-0 flex-1">
                                            {isRenaming ? (
                                                <div className="flex flex-col gap-2 sm:flex-row">
                                                    <input
                                                        value={renameValue}
                                                        onChange={(event) => setRenameValue(event.target.value)}
                                                        disabled={isActionLocked}
                                                        className="min-w-0 flex-1 rounded-xl border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-white outline-none transition focus:border-cyan-400 disabled:cursor-not-allowed disabled:opacity-60"
                                                        maxLength={512}
                                                        placeholder="Veri seti adı"
                                                    />
                                                    <div className="flex items-center gap-2">
                                                        <button
                                                            type="button"
                                                            onClick={() => void submitRename(dataset.id)}
                                                            disabled={isActionLocked || renameValue.trim().length === 0}
                                                            className="inline-flex cursor-pointer items-center gap-2 rounded-xl border border-emerald-400/30 bg-emerald-400/10 px-3 py-2 text-xs font-medium text-emerald-200 transition hover:bg-emerald-400/20 disabled:cursor-not-allowed disabled:opacity-50"
                                                        >
                                                            <Check className="h-4 w-4" />
                                                            Kaydet
                                                        </button>
                                                        <button
                                                            type="button"
                                                            onClick={cancelRename}
                                                            disabled={pendingAction?.type === 'rename'}
                                                            className="inline-flex cursor-pointer items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs font-medium text-gray-200 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
                                                        >
                                                            <X className="h-4 w-4" />
                                                            Vazgeç
                                                        </button>
                                                    </div>
                                                </div>
                                            ) : (
                                                <div className="flex flex-wrap items-center gap-2">
                                                    <h3 className="truncate text-base font-semibold text-white">
                                                        {dataset.name}
                                                    </h3>
                                                    {isActive ? (
                                                        <span className="rounded-full border border-cyan-400/30 bg-cyan-400/15 px-2.5 py-1 text-[11px] font-medium text-cyan-100">
                                                            Aktif
                                                        </span>
                                                    ) : null}
                                                </div>
                                            )}

                                            <div className="mt-2 flex flex-wrap gap-2 text-xs text-gray-400">
                                                <span className="rounded-full border border-white/10 px-2.5 py-1">
                                                    {dataset.rows.toLocaleString('tr-TR')} satır
                                                </span>
                                                <span className="rounded-full border border-white/10 px-2.5 py-1">
                                                    {dataset.columns.toLocaleString('tr-TR')} sütun
                                                </span>
                                                <span className="rounded-full border border-white/10 px-2.5 py-1">
                                                    Son kayıt: {formatUpdatedAt(dataset.updatedAt)}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex flex-wrap items-center gap-2">
                                        <button
                                            type="button"
                                            onClick={() => void handleLoad(dataset.id)}
                                            disabled={isActionLocked}
                                            className="inline-flex cursor-pointer items-center gap-2 rounded-xl bg-cyan-400 px-3.5 py-2 text-sm font-medium text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-50"
                                        >
                                            <Play className="h-4 w-4" />
                                            {isPending && pendingAction?.type === 'load'
                                                ? 'Yükleniyor...'
                                                : isActive
                                                  ? 'Yeniden yükle'
                                                  : 'Yükle'}
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => startRename(dataset)}
                                            disabled={isActionLocked || isRenaming}
                                            className="inline-flex cursor-pointer items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3.5 py-2 text-sm font-medium text-gray-100 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
                                        >
                                            <Pencil className="h-4 w-4" />
                                            Yeniden adlandır
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => void handleDelete(dataset.id)}
                                            disabled={isActionLocked}
                                            className="inline-flex cursor-pointer items-center gap-2 rounded-xl border border-red-500/30 bg-red-500/10 px-3.5 py-2 text-sm font-medium text-red-100 transition hover:bg-red-500/15 disabled:cursor-not-allowed disabled:opacity-50"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                            {isPending && pendingAction?.type === 'delete' ? 'Siliniyor...' : 'Sil'}
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
