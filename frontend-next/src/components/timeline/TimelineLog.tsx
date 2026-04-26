'use client';

import { useMemo, useState } from 'react';
import { Clock, Search, Undo2 } from 'lucide-react';
import { theme } from '@/styles/theme';
import type { TimelineEvent } from '@/types/timeline';

interface TimelineLogProps {
    events: TimelineEvent[];
    canUndoLast: boolean;
    isLoading?: boolean;
    onUndoLast?: () => void | Promise<void>;
}

const stepLabels: Record<string, string> = {
    missing_values: 'Eksik Değerler',
    outliers: 'Aykırı Değerler',
    feature_engineering: 'Özellik Mühendisliği',
    encoding: 'Kodlama',
    scaling: 'Ölçeklendirme',
};

const eventCategoryLabels: Record<string, string> = {
    upload: 'Yükleme',
    editor: 'Düzenleyici',
    preprocessing: 'Ön İşleme',
    model: 'Model',
};

const preprocessingActionLabels: Record<string, string> = {
    fill_mean: 'Eksik değer doldurma',
    fill_median: 'Eksik değer doldurma',
    fill_mode: 'Eksik değer doldurma',
    fill_knn: 'Eksik değer doldurma',
    fill_interpolation: 'Eksik değer doldurma',
    fill_regression: 'Eksik değer doldurma',
    fill_ffill: 'Eksik değer doldurma',
    fill_bfill: 'Eksik değer doldurma',
    drop_columns: 'Sütun silme',
    iqr_cap: 'Aykırı değer işlemi',
    iqr_winsorize: 'Aykırı değer işlemi',
    label: 'Kodlama',
    onehot: 'Kodlama',
    ordinal: 'Kodlama',
    binary: 'Kodlama',
    frequency: 'Kodlama',
    standard: 'Ölçeklendirme',
    minmax: 'Ölçeklendirme',
    robust: 'Ölçeklendirme',
    maxabs: 'Ölçeklendirme',
    normalizer: 'Ölçeklendirme',
    polynomial: 'Özellik mühendisliği',
    create_numeric: 'Özellik mühendisliği',
    create_datetime: 'Özellik mühendisliği',
    create_categorical: 'Özellik mühendisliği',
    binning: 'Özellik mühendisliği',
};

function getTitle(event: TimelineEvent): string {
    if (event.title) {
        return event.title;
    }

    if (event.category === 'preprocessing' && event.action) {
        return preprocessingActionLabels[event.action] || event.action;
    }

    return 'İşlem';
}

function getDescription(event: TimelineEvent): string {
    if (event.description) {
        return event.description;
    }

    return 'İşlem ayrıntısı kaydedildi.';
}

function getDetailLines(event: TimelineEvent): string[] {
    const payload = event.payload;
    const metadata = event.metadata;

    if (event.category === 'preprocessing') {
        const columns = Array.isArray(payload.columns)
            ? payload.columns
            : Array.isArray(payload.source_columns)
              ? payload.source_columns
              : [];
        const newColumns = Array.isArray(payload.new_columns) ? payload.new_columns : [];
        const lines: string[] = [];

        if (columns.length > 0) {
            lines.push(`Sütunlar: ${columns.join(', ')}`);
        }
        if (newColumns.length > 0) {
            lines.push(`Yeni sütunlar: ${newColumns.join(', ')}`);
        }
        if (typeof payload.affected_rows === 'number' && payload.affected_rows > 0) {
            lines.push(`${payload.affected_rows} satır etkilendi`);
        }
        return lines;
    }

    if (event.category === 'upload') {
        const rows = typeof metadata.rows === 'number' ? metadata.rows : null;
        const columns = typeof metadata.columns === 'number' ? metadata.columns : null;
        return rows !== null && columns !== null ? [`${rows} satır, ${columns} sütun`] : [];
    }

    if (event.category === 'editor') {
        const lines: string[] = [];
        if (typeof metadata.updated_cells === 'number' && metadata.updated_cells > 0) {
            lines.push(`${metadata.updated_cells} hücre güncellendi`);
        }
        if (typeof metadata.cleared_cells === 'number' && metadata.cleared_cells > 0) {
            lines.push(`${metadata.cleared_cells} hücre temizlendi`);
        }
        if (typeof metadata.deleted_rows === 'number' && metadata.deleted_rows > 0) {
            lines.push(`${metadata.deleted_rows} satır silindi`);
        }
        if (typeof metadata.renamed_columns === 'number' && metadata.renamed_columns > 0) {
            lines.push(`${metadata.renamed_columns} sütun yeniden adlandırıldı`);
        }
        return lines;
    }

    if (event.category === 'model') {
        const models = Array.isArray(metadata.models)
            ? metadata.models
            : Array.isArray(metadata.model_ids)
              ? metadata.model_ids
              : [];
        return models.length > 0 ? [`Modeller: ${models.join(', ')}`] : [];
    }

    return [];
}

function formatTimestamp(date: Date): string {
    return date.toLocaleString('tr-TR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    });
}

export function TimelineLog({
    events,
    canUndoLast,
    isLoading = false,
    onUndoLast,
}: TimelineLogProps) {
    const [searchTerm, setSearchTerm] = useState('');
    const normalizedSearchTerm = searchTerm.trim().toLocaleLowerCase('tr-TR');
    const filteredEvents = useMemo(() => {
        if (!normalizedSearchTerm) {
            return events;
        }

        return events.filter((event) => {
            const details = getDetailLines(event).join(' ');
            const searchableText = [
                getTitle(event),
                getDescription(event),
                event.action || '',
                event.category,
                eventCategoryLabels[event.category] || '',
                event.step || '',
                event.step ? stepLabels[event.step] || '' : '',
                details,
                formatTimestamp(event.createdAt),
            ]
                .join(' ')
                .toLocaleLowerCase('tr-TR');

            return searchableText.includes(normalizedSearchTerm);
        });
    }, [events, normalizedSearchTerm]);

    if (events.length === 0) {
        return (
            <div className="rounded-2xl border border-white/10 bg-white/5 p-5 text-left">
                <Clock className="mb-3 h-8 w-8 text-cyan-400" />
                <p className="text-sm text-gray-300">Henüz işlem geçmişi kaydı yok.</p>
                <p className="mt-1 text-xs text-gray-500">
                    Veri yükleme, düzenleme, ön işleme ve model seçimi işlemleri burada listelenecek.
                </p>
            </div>
        );
    }

    return (
        <div className="overflow-hidden rounded-2xl border border-white/10 bg-white/5">
            <div className="flex items-center justify-between border-b border-white/10 bg-white/5 px-4 py-3">
                <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-cyan-400" />
                    <span className="font-medium text-white">İşlem Timeline</span>
                    <span className="rounded-full bg-cyan-500/20 px-2 py-0.5 text-xs text-cyan-400">
                        {events.length}
                    </span>
                </div>
                {onUndoLast && (
                    <button
                        type="button"
                        onClick={onUndoLast}
                        disabled={!canUndoLast || isLoading}
                        className={`flex items-center gap-1 rounded px-2 py-1 text-xs transition-colors ${
                            !canUndoLast || isLoading
                                ? 'cursor-not-allowed text-gray-500'
                                : 'cursor-pointer text-gray-300 hover:bg-white/10 hover:text-white'
                        }`}
                    >
                        <Undo2 className="h-3 w-3" />
                        Son İşlemi Geri Al
                    </button>
                )}
            </div>

            <div className="border-b border-white/10 px-4 py-3">
                <label className="relative block">
                    <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
                    <input
                        type="text"
                        value={searchTerm}
                        onChange={(event) => setSearchTerm(event.target.value)}
                        placeholder="Tarih, saat, işlem adı veya açıklama ara"
                        className="w-full rounded-xl border border-white/10 bg-slate-950/50 py-2 pl-9 pr-3 text-sm text-white outline-none transition-colors placeholder:text-gray-500 focus:border-cyan-400/50"
                    />
                </label>
            </div>

            <div className="max-h-[70vh] overflow-y-auto px-5 py-4">
                {filteredEvents.length === 0 && (
                    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm text-gray-400">
                        Aramanızla eşleşen timeline kaydı bulunamadı.
                    </div>
                )}

                {filteredEvents.map((event, index) => {
                    const details = getDetailLines(event);

                    return (
                        <div key={event.id} className="relative pl-8 pb-6 last:pb-0">
                            {index < filteredEvents.length - 1 && (
                                <div className="absolute bottom-0 left-[0.4375rem] top-3 w-px bg-white/10" />
                            )}
                            <div
                                className="absolute left-0 top-2 h-3.5 w-3.5 rounded-full border-2"
                                style={{
                                    background: theme.colors.background.elevated,
                                    borderColor: theme.colors.primary.cyan,
                                    boxShadow: theme.glow.cyan,
                                }}
                            />
                            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                                <div className="flex items-start justify-between gap-3">
                                    <div className="min-w-0">
                                        <div className="flex flex-wrap items-center gap-2">
                                            <span className="text-sm font-medium text-white">{getTitle(event)}</span>
                                            <span className="rounded bg-white/10 px-1.5 py-0.5 text-xs text-gray-400">
                                                {eventCategoryLabels[event.category] || event.category}
                                            </span>
                                            {event.step && (
                                                <span className="rounded bg-cyan-500/10 px-1.5 py-0.5 text-xs text-cyan-300">
                                                    {stepLabels[event.step] || event.step}
                                                </span>
                                            )}
                                        </div>
                                        <p className="mt-1 text-sm text-gray-400">{getDescription(event)}</p>
                                        {details.map((detail) => (
                                            <p key={detail} className="mt-1 text-xs text-gray-500">
                                                {detail}
                                            </p>
                                        ))}
                                    </div>
                                    <span className="shrink-0 text-xs text-gray-500">
                                        {formatTimestamp(event.createdAt)}
                                    </span>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
