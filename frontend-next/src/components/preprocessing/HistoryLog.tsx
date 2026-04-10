'use client';

import { Clock, Undo2, Trash2 } from 'lucide-react';
import { ProcessingHistory } from '@/types/preprocessing';
import { theme } from '@/styles/theme';

interface HistoryLogProps {
    history: ProcessingHistory[];
    onUndo?: () => void;
    onClear?: () => void;
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

export function HistoryLog({ history, onUndo, onClear }: HistoryLogProps) {
    if (history.length === 0) {
        return (
            <div className="p-4 rounded-xl border border-white/10 bg-white/5 text-center">
                <Clock className="w-8 h-8 text-gray-500 mx-auto mb-2" />
                <p className="text-gray-400 text-sm">Henüz işlem yapılmadı</p>
            </div>
        );
    }

    return (
        <div className="rounded-xl border border-white/10 overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 bg-white/5 border-b border-white/10">
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
                            className="cursor-pointer flex items-center gap-1 px-2 py-1 rounded text-xs text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
                        >
                            <Undo2 className="w-3 h-3" />
                            Geri Al
                        </button>
                    )}
                    {onClear && history.length > 0 && (
                        <button
                            onClick={onClear}
                            className="cursor-pointer flex items-center gap-1 px-2 py-1 rounded text-xs text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors"
                        >
                            <Trash2 className="w-3 h-3" />
                            Temizle
                        </button>
                    )}
                </div>
            </div>

            {/* History items */}
            <div className="max-h-64 overflow-y-auto">
                {history.slice().reverse().map((item) => (
                    <div
                        key={item.id}
                        className="flex items-start gap-3 p-3 border-b border-white/5 last:border-0 hover:bg-white/5"
                    >
                        <div
                            className="w-2 h-2 rounded-full mt-2 flex-shrink-0"
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
                    </div>
                ))}
            </div>
        </div>
    );
}
