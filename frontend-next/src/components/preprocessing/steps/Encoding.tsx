'use client';

import { useState } from 'react';
import { MethodSelector } from '../MethodSelector';
import { ColumnSelector } from '../ColumnSelector';
import { ColumnInfo, EncodingConfig, EncodingMethod } from '@/types/preprocessing';
import { Loader2 } from 'lucide-react';
import { theme } from '@/styles/theme';

interface EncodingProps {
    categoricalColumns: ColumnInfo[];
    onApply: (config: EncodingConfig) => Promise<void>;
    isLoading: boolean;
}

const METHODS = [
    { value: 'label', label: 'Label Encoding', icon: '🏷️', description: 'Her kategoriye sayı ata' },
    { value: 'onehot', label: 'One-Hot Encoding', icon: '🔢', description: 'Her kategori için ayrı sütun' },
    { value: 'ordinal', label: 'Ordinal Encoding', icon: '📊', description: 'Sıralı kategoriler için' },
    { value: 'binary', label: 'Binary Encoding', icon: '💻', description: 'İkili sayı sistemine dönüştür' },
    { value: 'frequency', label: 'Frequency Encoding', icon: '📈', description: 'Frekansa göre değer ata' },
];

export function Encoding({ categoricalColumns, onApply, isLoading }: EncodingProps) {
    const [method, setMethod] = useState<EncodingMethod>('label');
    const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
    const [dropFirst, setDropFirst] = useState(true);

    const handleApply = async () => {
        if (selectedColumns.length === 0) return;

        await onApply({
            method,
            columns: selectedColumns,
            dropFirst: method === 'onehot' ? dropFirst : undefined,
        });

        setSelectedColumns([]);
    };

    const canApply = selectedColumns.length > 0;

    return (
        <div className="space-y-6">
            {/* Info */}
            {categoricalColumns.length === 0 ? (
                <div
                    className="p-4 rounded-xl border"
                    style={{
                        borderColor: `${theme.colors.status.info}50`,
                        background: `${theme.colors.status.info}10`,
                    }}
                >
                    <p className="text-blue-400">ℹ️ Kategorik sütun bulunamadı.</p>
                </div>
            ) : (
                <div
                    className="p-4 rounded-xl border"
                    style={{
                        borderColor: `${theme.colors.status.info}50`,
                        background: `${theme.colors.status.info}10`,
                    }}
                >
                    <p className="text-blue-400">
                        ℹ️ {categoricalColumns.length} kategorik sütun kodlanmaya hazır.
                    </p>
                </div>
            )}

            {/* Method selector */}
            <MethodSelector
                label="Encoding Yöntemi"
                options={METHODS}
                value={method}
                onChange={(v) => setMethod(v as EncodingMethod)}
                disabled={isLoading}
            />

            {/* One-hot specific option */}
            {method === 'onehot' && (
                <div className="flex items-center gap-3">
                    <input
                        type="checkbox"
                        id="dropFirst"
                        checked={dropFirst}
                        onChange={(e) => setDropFirst(e.target.checked)}
                        disabled={isLoading}
                        className="w-4 h-4 rounded border-white/30 bg-white/5"
                    />
                    <label htmlFor="dropFirst" className="text-sm text-gray-300">
                        İlk sütunu düşür (multicollinearity önlemek için)
                    </label>
                </div>
            )}

            {/* Column selector */}
            <ColumnSelector
                columns={categoricalColumns}
                selectedColumns={selectedColumns}
                onChange={setSelectedColumns}
                label="Uygulanacak Kategorik Sütunlar"
                showMissing={false}
                disabled={isLoading || categoricalColumns.length === 0}
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
