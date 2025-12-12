'use client';

import { useState } from 'react';
import { MethodSelector } from '../MethodSelector';
import { ColumnSelector } from '../ColumnSelector';
import { ColumnInfo, OutlierConfig, OutlierMethod } from '@/types/preprocessing';
import { Loader2 } from 'lucide-react';
import { theme } from '@/styles/theme';

interface OutliersProps {
    numericColumns: ColumnInfo[];
    onApply: (config: OutlierConfig) => Promise<void>;
    isLoading: boolean;
}

const METHODS = [
    { value: 'iqr_remove', label: 'IQR - Kaldır', icon: '📦', description: 'IQR yöntemi ile aykırı değerleri kaldır' },
    { value: 'iqr_cap', label: 'IQR - Sınırla', icon: '📦', description: 'IQR yöntemi ile aykırı değerleri sınırla' },
    { value: 'zscore_remove', label: 'Z-Score - Kaldır', icon: '📊', description: 'Z-Score ile aykırı değerleri kaldır' },
    { value: 'zscore_cap', label: 'Z-Score - Sınırla', icon: '📊', description: 'Z-Score ile aykırı değerleri sınırla' },
    { value: 'isolation_forest', label: 'Isolation Forest', icon: '🌲', description: 'ML tabanlı aykırı değer tespiti' },
    { value: 'lof', label: 'LOF', icon: '🎯', description: 'Local Outlier Factor algoritması' },
];

export function Outliers({ numericColumns, onApply, isLoading }: OutliersProps) {
    const [method, setMethod] = useState<OutlierMethod>('iqr_remove');
    const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
    const [threshold, setThreshold] = useState<string>('1.5');

    const handleApply = async () => {
        if (selectedColumns.length === 0) return;

        await onApply({
            method,
            columns: selectedColumns,
            threshold: parseFloat(threshold) || undefined,
        });

        setSelectedColumns([]);
    };

    const canApply = selectedColumns.length > 0;
    const showThreshold = method.startsWith('iqr') || method.startsWith('zscore');

    return (
        <div className="space-y-6">
            {/* Info */}
            <div
                className="p-4 rounded-xl border"
                style={{
                    borderColor: `${theme.colors.status.info}50`,
                    background: `${theme.colors.status.info}10`,
                }}
            >
                <p className="text-blue-400">
                    ℹ️ Aykırı değerler veri kalitesini ve model performansını etkileyebilir.
                </p>
            </div>

            {/* Method selector */}
            <MethodSelector
                label="Aykırı Değer Yöntemi"
                options={METHODS}
                value={method}
                onChange={(v) => setMethod(v as OutlierMethod)}
                disabled={isLoading}
            />

            {/* Threshold input */}
            {showThreshold && (
                <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-300">
                        Eşik Değeri {method.startsWith('iqr') ? '(IQR çarpanı)' : '(σ sayısı)'}
                    </label>
                    <input
                        type="number"
                        value={threshold}
                        onChange={(e) => setThreshold(e.target.value)}
                        step="0.1"
                        min="0.5"
                        max="5"
                        disabled={isLoading}
                        className="w-full px-4 py-2 rounded-lg border border-white/10 bg-white/5 text-white placeholder:text-gray-500 outline-none focus:border-cyan-500/50"
                    />
                    <p className="text-xs text-gray-500">
                        {method.startsWith('iqr')
                            ? 'Varsayılan: 1.5 (standart IQR kuralı)'
                            : 'Varsayılan: 3 (3 sigma kuralı)'
                        }
                    </p>
                </div>
            )}

            {/* Column selector */}
            <ColumnSelector
                columns={numericColumns}
                selectedColumns={selectedColumns}
                onChange={setSelectedColumns}
                label="Uygulanacak Sayısal Sütunlar"
                showMissing={false}
                disabled={isLoading}
            />

            {/* Apply button */}
            <button
                onClick={handleApply}
                disabled={!canApply || isLoading}
                className="w-full flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-medium text-white transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
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
