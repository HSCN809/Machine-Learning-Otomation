'use client';

import { useState } from 'react';
import { MethodSelector } from '../MethodSelector';
import { ColumnSelector } from '../ColumnSelector';
import { ColumnInfo, MissingValueConfig, MissingValueMethod } from '@/types/preprocessing';
import { Loader2 } from 'lucide-react';
import { theme } from '@/styles/theme';

interface MissingValuesProps {
    columns: ColumnInfo[];
    columnsWithMissing: ColumnInfo[];
    onApply: (config: MissingValueConfig) => Promise<void>;
    isLoading: boolean;
}

const METHODS = [
    { value: 'fill_mean', label: 'Ortalama', icon: '📊', description: 'Sayısal sütunlar için ortalama değer' },
    { value: 'fill_median', label: 'Medyan', icon: '📈', description: 'Sayısal sütunlar için medyan değer' },
    { value: 'fill_mode', label: 'Mod', icon: '📉', description: 'En sık görülen değer' },
    { value: 'fill_constant', label: 'Sabit Değer', icon: '✏️', description: 'Kullanıcı tanımlı değer' },
    { value: 'fill_ffill', label: 'Forward Fill', icon: '⬇️', description: 'Önceki değerle doldur' },
    { value: 'fill_bfill', label: 'Backward Fill', icon: '⬆️', description: 'Sonraki değerle doldur' },
    { value: 'drop_rows', label: 'Satırları Sil', icon: '🗑️', description: 'Eksik değerli satırları kaldır' },
    { value: 'drop_columns', label: 'Sütunları Sil', icon: '❌', description: 'Eksik değerli sütunları kaldır' },
];

export function MissingValues({ columns, columnsWithMissing, onApply, isLoading }: MissingValuesProps) {
    const [method, setMethod] = useState<MissingValueMethod>('fill_mean');
    const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
    const [fillValue, setFillValue] = useState<string>('');

    const handleApply = async () => {
        if (selectedColumns.length === 0) return;

        await onApply({
            method,
            columns: selectedColumns,
            fillValue: method === 'fill_constant' ? fillValue : undefined,
        });

        // Reset after apply
        setSelectedColumns([]);
        setFillValue('');
    };

    const canApply = selectedColumns.length > 0 && (method !== 'fill_constant' || fillValue.trim());

    return (
        <div className="space-y-6">
            {/* Info */}
            {columnsWithMissing.length === 0 ? (
                <div
                    className="p-4 rounded-xl border"
                    style={{
                        borderColor: `${theme.colors.status.success}50`,
                        background: `${theme.colors.status.success}10`,
                    }}
                >
                    <p className="text-green-400">✅ Veri setinde eksik değer bulunmuyor!</p>
                </div>
            ) : (
                <div
                    className="p-4 rounded-xl border"
                    style={{
                        borderColor: `${theme.colors.status.warning}50`,
                        background: `${theme.colors.status.warning}10`,
                    }}
                >
                    <p className="text-yellow-400">
                        ⚠️ {columnsWithMissing.length} sütunda eksik değer tespit edildi.
                    </p>
                </div>
            )}

            {/* Method selector */}
            <MethodSelector
                label="Doldurma Yöntemi"
                options={METHODS}
                value={method}
                onChange={(v) => setMethod(v as MissingValueMethod)}
                disabled={isLoading}
            />

            {/* Constant value input */}
            {method === 'fill_constant' && (
                <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-300">Sabit Değer</label>
                    <input
                        type="text"
                        value={fillValue}
                        onChange={(e) => setFillValue(e.target.value)}
                        placeholder="Doldurulacak değeri girin..."
                        disabled={isLoading}
                        className="w-full px-4 py-2 rounded-lg border border-white/10 bg-white/5 text-white placeholder:text-gray-500 outline-none focus:border-cyan-500/50"
                    />
                </div>
            )}

            {/* Column selector */}
            <ColumnSelector
                columns={method.includes('drop') ? columnsWithMissing : columns}
                selectedColumns={selectedColumns}
                onChange={setSelectedColumns}
                label="Uygulanacak Sütunları Seç"
                disabled={isLoading}
            />

            {/* Apply button */}
            <button
                onClick={handleApply}
                disabled={!canApply || isLoading}
                className={`w-full flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-medium text-white transition-all duration-200 ${
                    !canApply || isLoading ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'
                }`}
                style={{
                    background: canApply && !isLoading ? theme.gradients.primary : 'rgba(255,255,255,0.1)',
                    boxShadow: canApply && !isLoading ? theme.glow.cyan : undefined,
                }}
            >
                {isLoading ? (
                    <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        İşleniyor...
                    </>
                ) : (
                    <>Uygula</>
                )}
            </button>
        </div>
    );
}
