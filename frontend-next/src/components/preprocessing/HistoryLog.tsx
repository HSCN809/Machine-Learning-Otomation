'use client';

import { Clock, Undo2 } from 'lucide-react';
import { ProcessingHistory } from '@/types/preprocessing';
import { theme } from '@/styles/theme';

interface HistoryLogProps {
    history: ProcessingHistory[];
    onUndo?: () => void | Promise<void>;
    onUndoItem?: (historyIndex: number) => void | Promise<void>;
    isLoading?: boolean;
    variant?: 'card' | 'timeline';
}

const stepLabels: Record<string, string> = {
    missing_values: 'Missing Values',
    outliers: 'Outliers',
    feature_engineering: 'Feature Engineering',
    encoding: 'Encoding',
    scaling: 'Scaling',
};

const actionLabels: Record<string, string> = {
    fill_missing: 'Eksik değer doldurma',
    handle_outliers: 'Aykırı değer işleme',
    encode_categorical: 'Kategorik kodlama',
    scale_numeric: 'Ölçeklendirme',
    create_feature: 'Özellik oluşturma',
};

const methodLabels: Record<string, string> = {
    create_numeric: 'Sayısal İşlem',
    polynomial: 'Polinom Özellik',
    binning: 'Binning',
    create_datetime: 'Tarih/Zaman',
    create_categorical: 'Kategorik Kombinasyon',
    add: 'Toplama',
    subtract: 'Çıkarma',
    multiply: 'Çarpma',
    divide: 'Bölme',
    custom: 'Özel İfade',
    equal_width: 'Equal Width',
    quantile: 'Quantile',
};

export function HistoryLog({
    history,
    onUndo,
    onUndoItem,
    isLoading = false,
    variant = 'card',
}: HistoryLogProps) {
    const isTimeline = variant === 'timeline';

    if (history.length === 0) {
        return (
            <div
                className={isTimeline ? 'rounded-2xl border border-white/10 bg-white/5 p-5 text-left' : 'p-4 rounded-xl border border-white/10 bg-white/5 text-center'}
            >
                <Clock className={`${isTimeline ? 'mb-3 h-8 w-8 text-cyan-400' : 'w-8 h-8 text-gray-500 mx-auto mb-2'}`} />
                <p className={`${isTimeline ? 'text-sm text-gray-300' : 'text-gray-400 text-sm'}`}>Henüz işlem yapılmadı</p>
                {isTimeline && (
                    <p className="mt-1 text-xs text-gray-500">
                        Uyguladığınız preprocessing işlemleri burada zaman akışıyla listelenecek.
                    </p>
                )}
            </div>
        );
    }

    const orderedHistory = isTimeline ? history : history.slice().reverse();

    return (
        <div className={`overflow-hidden border border-white/10 ${isTimeline ? 'rounded-2xl bg-white/5' : 'rounded-xl'}`}>
            {/* Header */}
            <div className="flex items-center justify-between border-b border-white/10 bg-white/5 px-4 py-3">
                <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-cyan-400" />
                    <span className="font-medium text-white">İşlem Geçmişi</span>
                    <span className="px-2 py-0.5 rounded-full text-xs bg-cyan-500/20 text-cyan-400">
                        {history.length}
                    </span>
                </div>
                <div className="flex items-center gap-2">
                    {onUndo && history.length > 0 && (
                        <button
                            onClick={onUndo}
                            disabled={isLoading}
                            className={`flex items-center gap-1 rounded px-2 py-1 text-xs transition-colors ${
                                isLoading
                                    ? 'cursor-not-allowed text-gray-500'
                                    : 'cursor-pointer text-gray-400 hover:bg-white/10 hover:text-white'
                            }`}
                        >
                            <Undo2 className="w-3 h-3" />
                            Geri Al
                        </button>
                    )}
                </div>
            </div>

            {/* History items */}
            <div className={isTimeline ? 'max-h-[70vh] overflow-y-auto px-5 py-4' : 'max-h-64 overflow-y-auto'}>
                {orderedHistory.map((item, index) => (
                    <div
                        key={item.id}
                        className={
                            isTimeline
                                ? 'relative pl-8 pb-6 last:pb-0'
                                : 'flex items-start gap-3 border-b border-white/5 p-3 last:border-0 hover:bg-white/5'
                        }
                    >
                        {isTimeline ? (
                            <>
                                {index < orderedHistory.length - 1 && (
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
                                    <div className="flex flex-col gap-4">
                                        <div className="flex items-start justify-between gap-3">
                                            <div className="min-w-0">
                                            <div className="flex flex-wrap items-center gap-2">
                                                <span className="text-sm font-medium text-white">
                                                    {actionLabels[item.action] || item.action}
                                                </span>
                                                <span className="rounded bg-white/10 px-1.5 py-0.5 text-xs text-gray-400">
                                                    {stepLabels[item.stepKey] || item.stepKey}
                                                </span>
                                            </div>
                                            <p className="mt-1 text-sm text-gray-400">
                                                {item.columns?.length
                                                    ? `Sütunlar: ${item.columns.join(', ')}`
                                                    : item.column
                                                        ? `Sütun: ${item.column}`
                                                        : ''
                                                }
                                                {item.method && ` • Yöntem: ${item.method}`}
                                            </p>
                                            {(item.newColumns?.length || item.method) && (
                                                <p className="mt-1 text-xs text-gray-500">
                                                    {item.newColumns?.length ? `Yeni sütunlar: ${item.newColumns.join(', ')}` : ''}
                                                    {item.method ? `${item.newColumns?.length ? ' • ' : ''}Yöntem etiketi: ${methodLabels[item.method] || item.method}` : ''}
                                                </p>
                                            )}
                                            {item.affectedRows ? (
                                                <p className="mt-1 text-xs text-gray-500">
                                                    {item.affectedRows} satır etkilendi
                                                </p>
                                            ) : null}
                                        </div>
                                            <span className="shrink-0 text-xs text-gray-500">
                                                {new Date(item.timestamp).toLocaleTimeString('tr-TR', {
                                                    hour: '2-digit',
                                                    minute: '2-digit',
                                                })}
                                            </span>
                                            </div>
                                        {onUndoItem && (
                                            <div className="flex items-center justify-end gap-2">
                                                <button
                                                    type="button"
                                                    onClick={() => onUndoItem(item.historyIndex)}
                                                    disabled={isLoading}
                                                    className={`flex items-center gap-1 rounded-lg border px-3 py-2 text-xs transition-colors ${
                                                        isLoading
                                                            ? 'cursor-not-allowed border-white/10 text-gray-500'
                                                            : 'cursor-pointer border-white/10 text-gray-300 hover:bg-white/10 hover:text-white'
                                                    }`}
                                                >
                                                    <Undo2 className="h-3.5 w-3.5" />
                                                    Geri Al
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </>
                        ) : (
                            <>
                                <div
                                    className="mt-2 h-2 w-2 flex-shrink-0 rounded-full"
                                    style={{ background: theme.colors.primary.cyan }}
                                />
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                        <span className="text-sm font-medium text-white">
                                            {actionLabels[item.action] || item.action}
                                        </span>
                                        <span className="text-xs px-1.5 py-0.5 rounded bg-white/10 text-gray-400">
                                            {stepLabels[item.stepKey] || item.stepKey}
                                        </span>
                                    </div>
                                    <p className="text-sm text-gray-400 mt-0.5">
                                        {item.columns?.length
                                            ? `Sütunlar: ${item.columns.join(', ')}`
                                            : item.column
                                                ? `Sütun: ${item.column}`
                                                : ''
                                        }
                                        {item.method && ` • Yöntem: ${item.method}`}
                                    </p>
                                    {(item.newColumns?.length || item.method) && (
                                        <p className="text-xs text-gray-500 mt-1">
                                            {item.newColumns?.length ? `Yeni sütunlar: ${item.newColumns.join(', ')}` : ''}
                                            {item.method ? `${item.newColumns?.length ? ' • ' : ''}Yöntem etiketi: ${methodLabels[item.method] || item.method}` : ''}
                                        </p>
                                    )}
                                    {item.affectedRows && (
                                        <p className="text-xs text-gray-500 mt-0.5">
                                            {item.affectedRows} satır etkilendi
                                        </p>
                                    )}
                                </div>
                                <span className="text-xs text-gray-500 flex-shrink-0">
                                    {new Date(item.timestamp).toLocaleTimeString('tr-TR', {
                                        hour: '2-digit',
                                        minute: '2-digit',
                                    })}
                                </span>
                            </>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}
