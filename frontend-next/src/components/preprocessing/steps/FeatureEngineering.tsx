'use client';

import { useState } from 'react';
import { ColumnSelector } from '../ColumnSelector';
import { ColumnInfo, FeatureConfig, FeatureOperation } from '@/types/preprocessing';
import { Loader2, Plus } from 'lucide-react';
import { theme } from '@/styles/theme';

interface FeatureEngineeringProps {
    columns: ColumnInfo[];
    numericColumns: ColumnInfo[];
    onApply: (config: FeatureConfig) => Promise<void>;
    isLoading: boolean;
}

const OPERATIONS = [
    { value: 'create_numeric', label: 'Sayısal İşlem', icon: '🔢', description: 'Matematiksel işlem uygula' },
    { value: 'polynomial', label: 'Polinom Özellik', icon: '📈', description: 'x², x³ gibi özellikler oluştur' },
    { value: 'binning', label: 'Binning', icon: '📊', description: 'Sayısal değeri kategorize et' },
];

export function FeatureEngineering({ columns, numericColumns, onApply, isLoading }: FeatureEngineeringProps) {
    const [operation, setOperation] = useState<FeatureOperation>('create_numeric');
    const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
    const [newColumnName, setNewColumnName] = useState('');
    const [expression, setExpression] = useState('');

    const handleApply = async () => {
        if (selectedColumns.length === 0 || !newColumnName.trim()) return;

        await onApply({
            operation,
            sourceColumns: selectedColumns,
            newColumnName: newColumnName.trim(),
            expression: expression.trim() || undefined,
        });

        setSelectedColumns([]);
        setNewColumnName('');
        setExpression('');
    };

    const canApply = selectedColumns.length > 0 && newColumnName.trim();

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
                    💡 Feature engineering ile yeni özellikler oluşturarak model performansını artırabilirsiniz.
                </p>
            </div>

            {/* Operation selector */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-gray-300">İşlem Türü</label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {OPERATIONS.map((op) => (
                        <button
                            key={op.value}
                            onClick={() => setOperation(op.value as FeatureOperation)}
                            disabled={isLoading}
                            className={`p-4 rounded-xl border text-left transition-all ${operation === op.value
                                    ? 'border-cyan-500/50 bg-cyan-500/10'
                                    : 'border-white/10 bg-white/5 hover:border-cyan-500/30'
                                }`}
                        >
                            <span className="text-xl">{op.icon}</span>
                            <p className="font-medium text-white mt-2">{op.label}</p>
                            <p className="text-xs text-gray-400 mt-1">{op.description}</p>
                        </button>
                    ))}
                </div>
            </div>

            {/* Column selector */}
            <ColumnSelector
                columns={operation === 'create_numeric' || operation === 'polynomial' ? numericColumns : columns}
                selectedColumns={selectedColumns}
                onChange={setSelectedColumns}
                label="Kaynak Sütunlar"
                disabled={isLoading}
            />

            {/* New column name */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-gray-300">Yeni Sütun Adı</label>
                <input
                    type="text"
                    value={newColumnName}
                    onChange={(e) => setNewColumnName(e.target.value)}
                    placeholder="örn: age_squared, salary_binned"
                    disabled={isLoading}
                    className="w-full px-4 py-2 rounded-lg border border-white/10 bg-white/5 text-white placeholder:text-gray-500 outline-none focus:border-cyan-500/50"
                />
            </div>

            {/* Expression for numeric operations */}
            {operation === 'create_numeric' && (
                <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-300">
                        İfade (opsiyonel)
                    </label>
                    <input
                        type="text"
                        value={expression}
                        onChange={(e) => setExpression(e.target.value)}
                        placeholder="örn: col1 + col2, col1 * 2"
                        disabled={isLoading}
                        className="w-full px-4 py-2 rounded-lg border border-white/10 bg-white/5 text-white placeholder:text-gray-500 outline-none focus:border-cyan-500/50"
                    />
                    <p className="text-xs text-gray-500">
                        Sütun adlarını kullanarak matematiksel ifade yazın.
                    </p>
                </div>
            )}

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
                        Oluşturuluyor...
                    </>
                ) : (
                    <>
                        <Plus className="w-5 h-5" />
                        Özellik Oluştur
                    </>
                )}
            </button>
        </div>
    );
}
