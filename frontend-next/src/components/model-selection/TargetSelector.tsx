'use client';

import { ProblemType } from '@/types/model-selection';
import { cn } from '@/lib/utils';
import { theme } from '@/styles/theme';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface TargetSelectorProps {
    columns: { name: string; type: string; uniqueValues: number }[];
    selectedColumn: string | null;
    problemType: ProblemType | null;
    onSelect: (column: string) => void;
    disabled?: boolean;
}

import React from 'react';

export const TargetSelector = React.memo(function TargetSelector({
    columns,
    selectedColumn,
    problemType,
    onSelect,
    disabled = false,
}: TargetSelectorProps) {
    if (columns.length === 0) {
        return (
            <div className="space-y-6">
                <div className="space-y-3">
                    <label className="text-sm font-medium text-gray-300">Hedef Değişken (Target)</label>
                    <div className="rounded-2xl border border-white/10 bg-white/5 px-6 py-10 text-center text-gray-400">
                        Kullanılabilir sütun bulunamadı.
                    </div>
                </div>
            </div>
        );
    }

    const selectedIndex = columns.findIndex((column) => column.name === selectedColumn);
    const currentIndex = selectedIndex >= 0 ? selectedIndex : 0;
    const currentColumn = columns[currentIndex];
    const isCurrentSelected = selectedColumn === currentColumn.name;
    const isNumeric = currentColumn.type === 'numeric';

    const handleSelectColumn = (index: number) => {
        if (disabled || index < 0 || index >= columns.length) {
            return;
        }

        onSelect(columns[index].name);
    };

    return (
        <div className="space-y-6">
            {/* Column selection */}
            <div className="space-y-3">
                <label className="text-sm font-medium text-gray-300">Hedef Değişken (Target)</label>
                <div className="mx-auto flex max-w-5xl items-center gap-3">
                    <button
                        type="button"
                        onClick={() => handleSelectColumn(currentIndex - 1)}
                        disabled={disabled || currentIndex === 0}
                        className={cn(
                            'flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-gray-300 transition-all duration-200',
                            !disabled && currentIndex > 0 && 'cursor-pointer hover:border-cyan-500/30 hover:bg-white/10 hover:text-white',
                            (disabled || currentIndex === 0) && 'cursor-not-allowed opacity-50'
                        )}
                    >
                        <ChevronLeft className="h-5 w-5" />
                    </button>

                    <button
                        type="button"
                        onClick={() => handleSelectColumn(currentIndex)}
                        disabled={disabled}
                        className={cn(
                            'flex-1 rounded-xl border-2 p-4 md:p-5 text-left transition-all duration-200',
                            isCurrentSelected
                                ? 'border-cyan-500 bg-cyan-500/10'
                                : 'border-white/10 bg-white/5 hover:border-cyan-500/30 hover:bg-white/10',
                            !disabled && 'cursor-pointer',
                            disabled && 'cursor-not-allowed opacity-50'
                        )}
                        style={isCurrentSelected ? { boxShadow: theme.glow.cyan } : undefined}
                    >
                        <div className="flex items-start justify-between gap-4">
                            <div>
                                <p className={cn('text-2xl font-semibold tracking-tight md:text-[2rem]', isCurrentSelected ? 'text-cyan-400' : 'text-white')}>
                                    {currentColumn.name}
                                </p>
                                <div className="mt-3 flex flex-wrap items-center gap-2.5 text-sm">
                                    <span
                                        className={cn(
                                            'rounded-full px-3 py-1',
                                            isNumeric ? 'bg-blue-500/20 text-blue-400' : 'bg-green-500/20 text-green-400'
                                        )}
                                    >
                                        {isNumeric ? 'Sayısal' : 'Kategorik'}
                                    </span>
                                    <span className="text-gray-400">{currentColumn.uniqueValues} unique</span>
                                    <span className="text-gray-500">
                                        {currentIndex + 1} / {columns.length}
                                    </span>
                                </div>
                            </div>

                            {isCurrentSelected && <span className="text-xl text-cyan-400">✓</span>}
                        </div>
                    </button>

                    <button
                        type="button"
                        onClick={() => handleSelectColumn(currentIndex + 1)}
                        disabled={disabled || currentIndex === columns.length - 1}
                        className={cn(
                            'flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-gray-300 transition-all duration-200',
                            !disabled && currentIndex < columns.length - 1 && 'cursor-pointer hover:border-cyan-500/30 hover:bg-white/10 hover:text-white',
                            (disabled || currentIndex === columns.length - 1) && 'cursor-not-allowed opacity-50'
                        )}
                    >
                        <ChevronRight className="h-5 w-5" />
                    </button>

                    {false && columns.map((column) => {
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
});
