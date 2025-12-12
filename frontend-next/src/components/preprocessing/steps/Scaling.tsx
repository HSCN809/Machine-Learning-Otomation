'use client';

import { useState } from 'react';
import { MethodSelector } from '../MethodSelector';
import { ColumnSelector } from '../ColumnSelector';
import { ColumnInfo, ScalingConfig, ScalingMethod } from '@/types/preprocessing';
import { Loader2 } from 'lucide-react';
import { theme } from '@/styles/theme';

interface ScalingProps {
    numericColumns: ColumnInfo[];
    onApply: (config: ScalingConfig) => Promise<void>;
    isLoading: boolean;
}

const METHODS = [
    { value: 'standard', label: 'Standard Scaler', icon: '📐', description: 'Ortalama 0, std 1 olacak şekilde' },
    { value: 'minmax', label: 'MinMax Scaler', icon: '📏', description: '0-1 aralığına dönüştür' },
    { value: 'robust', label: 'Robust Scaler', icon: '🛡️', description: 'Aykırı değerlere dayanıklı' },
    { value: 'maxabs', label: 'MaxAbs Scaler', icon: '📊', description: '-1 ile 1 arasına ölçekle' },
    { value: 'normalizer', label: 'Normalizer', icon: '🔄', description: 'Birim norm\'a normalize et' },
];

export function Scaling({ numericColumns, onApply, isLoading }: ScalingProps) {
    const [method, setMethod] = useState<ScalingMethod>('standard');
    const [selectedColumns, setSelectedColumns] = useState<string[]>([]);

    const handleApply = async () => {
        if (selectedColumns.length === 0) return;

        await onApply({
            method,
            columns: selectedColumns,
        });

        setSelectedColumns([]);
    };

    const canApply = selectedColumns.length > 0;

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
                    ℹ️ Ölçeklendirme, ML algoritmalarının daha iyi performans göstermesini sağlar.
                </p>
            </div>

            {/* Method selector */}
            <MethodSelector
                label="Ölçeklendirme Yöntemi"
                options={METHODS}
                value={method}
                onChange={(v) => setMethod(v as ScalingMethod)}
                disabled={isLoading}
            />

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
