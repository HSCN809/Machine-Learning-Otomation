'use client';

import { ProblemType } from '@/types/model-selection';
import { cn } from '@/lib/utils';
import { theme } from '@/styles/theme';

interface TargetSelectorProps {
    columns: { name: string; type: string; uniqueValues: number }[];
    selectedColumn: string | null;
    problemType: ProblemType | null;
    onSelect: (column: string) => void;
    disabled?: boolean;
}

export function TargetSelector({
    columns,
    selectedColumn,
    problemType,
    onSelect,
    disabled = false,
}: TargetSelectorProps) {
    return (
        <div className="space-y-6">
            {/* Column selection */}
            <div className="space-y-3">
                <label className="text-sm font-medium text-gray-300">Hedef Değişken (Target)</label>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                    {columns.map((column) => {
                        const isSelected = selectedColumn === column.name;
                        const isNumeric = column.type === 'numeric';

                        return (
                            <button
                                key={column.name}
                                onClick={() => onSelect(column.name)}
                                disabled={disabled}
                                className={cn(
                                    'cursor-pointer p-4 rounded-xl border-2 text-left transition-all duration-200',
                                    isSelected
                                        ? 'border-cyan-500 bg-cyan-500/10'
                                        : 'border-white/10 bg-white/5 hover:border-cyan-500/30',
                                    disabled && 'opacity-50 cursor-not-allowed'
                                )}
                            >
                                <div className="flex items-center justify-between mb-2">
                                    <span className={cn(
                                        'font-medium',
                                        isSelected ? 'text-cyan-400' : 'text-white'
                                    )}>
                                        {column.name}
                                    </span>
                                    {isSelected && (
                                        <span className="text-cyan-400">✓</span>
                                    )}
                                </div>
                                <div className="flex items-center gap-2 text-xs">
                                    <span
                                        className={cn(
                                            'px-2 py-0.5 rounded',
                                            isNumeric ? 'bg-blue-500/20 text-blue-400' : 'bg-green-500/20 text-green-400'
                                        )}
                                    >
                                        {isNumeric ? 'Sayısal' : 'Kategorik'}
                                    </span>
                                    <span className="text-gray-500">
                                        {column.uniqueValues} unique
                                    </span>
                                </div>
                            </button>
                        );
                    })}
                </div>
            </div>

            {/* Problem type display */}
            {selectedColumn && problemType && (
                <div
                    className="p-6 rounded-xl border animate-fadeIn"
                    style={{
                        borderColor: problemType === 'classification'
                            ? `${theme.colors.secondary.green}50`
                            : `${theme.colors.primary.cyan}50`,
                        background: problemType === 'classification'
                            ? `${theme.colors.secondary.green}10`
                            : `${theme.colors.primary.cyan}10`,
                    }}
                >
                    <div className="flex items-center gap-4">
                        <span className="text-5xl">
                            {problemType === 'classification' ? '🏷️' : '📈'}
                        </span>
                        <div>
                            <h3 className="text-xl font-bold text-white">
                                {problemType === 'classification' ? 'Sınıflandırma Problemi' : 'Regresyon Problemi'}
                            </h3>
                            <p className="text-sm text-gray-400 mt-1">
                                {problemType === 'classification'
                                    ? 'Hedef değişken kategorik. Sınıflandırma modelleri önerilir.'
                                    : 'Hedef değişken sayısal. Regresyon modelleri önerilir.'}
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
