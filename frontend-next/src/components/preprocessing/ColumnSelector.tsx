'use client';

import { useState } from 'react';
import { Check, Search } from 'lucide-react';
import { cn } from '@/lib/utils';
import { theme } from '@/styles/theme';
import { ColumnInfo } from '@/types/preprocessing';

interface ColumnSelectorProps {
    columns: ColumnInfo[];
    selectedColumns: string[];
    onChange: (columns: string[]) => void;
    label?: string;
    multiSelect?: boolean;
    showType?: boolean;
    showUniqueCount?: boolean;
    showMissing?: boolean;
    showOutliers?: boolean;
    showSummary?: boolean;
    disabled?: boolean;
}

export function ColumnSelector({
    columns,
    selectedColumns,
    onChange,
    label = 'Sütun Seç',
    multiSelect = true,
    showType = true,
    showUniqueCount = false,
    showMissing = true,
    showOutliers = false,
    showSummary = false,
    disabled = false,
}: ColumnSelectorProps) {
    const [search, setSearch] = useState('');

    const filteredColumns = columns.filter(col =>
        col.name.toLowerCase().includes(search.toLowerCase())
    );

    const toggleColumn = (columnName: string) => {
        if (disabled) return;

        if (multiSelect) {
            if (selectedColumns.includes(columnName)) {
                onChange(selectedColumns.filter(c => c !== columnName));
            } else {
                onChange([...selectedColumns, columnName]);
            }
        } else {
            onChange([columnName]);
        }
    };

    const selectAll = () => {
        if (disabled) return;
        onChange(filteredColumns.map(c => c.name));
    };

    const clearAll = () => {
        if (disabled) return;
        onChange([]);
    };

    const getTypeColor = (type: string) => {
        switch (type) {
            case 'numeric': return theme.colors.primary.cyan;
            case 'categorical': return theme.colors.secondary.green;
            case 'datetime': return theme.colors.accent.purple;
            default: return theme.colors.text.secondary;
        }
    };

    return (
        <div className="space-y-3">
            <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-gray-300">{label}</label>
                {multiSelect && (
                    <div className="flex items-center gap-2 text-xs">
                        <button
                            onClick={selectAll}
                            disabled={disabled}
                            className={`text-cyan-400 hover:underline ${disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}
                        >
                            Tümünü Seç
                        </button>
                        <span className="text-gray-500">|</span>
                        <button
                            onClick={clearAll}
                            disabled={disabled}
                            className={`text-gray-400 hover:underline ${disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}
                        >
                            Temizle
                        </button>
                    </div>
                )}
            </div>

            {/* Search */}
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Sütun ara..."
                    disabled={disabled}
                    className={cn(
                        'w-full pl-10 pr-4 py-2 rounded-lg border border-white/10 bg-white/5',
                        'text-white placeholder:text-gray-500 outline-none',
                        'focus:border-cyan-500/50',
                        disabled && 'opacity-50 cursor-not-allowed'
                    )}
                />
            </div>

            {/* Column list */}
            <div className="max-h-64 overflow-y-auto rounded-lg border border-white/10 bg-white/5">
                {filteredColumns.length === 0 ? (
                    <p className="p-4 text-center text-gray-500 text-sm">Sütun bulunamadı</p>
                ) : (
                    <div className="divide-y divide-white/5">
                        {filteredColumns.map((column) => {
                            const isSelected = selectedColumns.includes(column.name);
                            return (
                                <button
                                    key={column.name}
                                    onClick={() => toggleColumn(column.name)}
                                    disabled={disabled}
                                    className={cn(
                                        'w-full flex items-center gap-3 p-3 text-left transition-colors',
                                        isSelected ? 'bg-cyan-500/10' : 'hover:bg-white/5',
                                        disabled ? 'cursor-not-allowed' : 'cursor-pointer'
                                    )}
                                >
                                    {/* Checkbox */}
                                    <div
                                        className={cn(
                                            'w-5 h-5 rounded border flex items-center justify-center transition-colors',
                                            isSelected
                                                ? 'border-cyan-500 bg-cyan-500'
                                                : 'border-white/30 bg-transparent'
                                        )}
                                    >
                                        {isSelected && <Check className="w-3 h-3 text-white" />}
                                    </div>

                                    {/* Column info */}
                                    <div className="flex-1 min-w-0">
                                        <p className={cn(
                                            'font-medium truncate',
                                            isSelected ? 'text-cyan-400' : 'text-white'
                                        )}>
                                            {column.name}
                                        </p>
                                        <div className="mt-0.5 flex flex-wrap items-center gap-2">
                                            {showType && (
                                                <span
                                                    className="text-xs px-1.5 py-0.5 rounded"
                                                    style={{
                                                        backgroundColor: `${getTypeColor(column.type)}20`,
                                                        color: getTypeColor(column.type),
                                                    }}
                                                >
                                                    {column.type}
                                                </span>
                                            )}
                                            {showUniqueCount && (
                                                <span className="text-xs text-gray-400">
                                                    {column.uniqueCount} benzersiz
                                                </span>
                                            )}
                                            {showMissing && column.missingCount > 0 && (
                                                <span className="text-xs text-yellow-400">
                                                    {column.missingPercentage.toFixed(1)}% eksik
                                                </span>
                                            )}
                                            {showOutliers && (column.outlierCount ?? 0) > 0 && (
                                                <span className="text-xs text-rose-400">
                                                    {(column.outlierPercentage ?? 0).toFixed(1)}% aykırı
                                                </span>
                                            )}
                                            {showSummary && column.distributionSummary && (
                                                <span className="text-xs text-gray-400">
                                                    {column.distributionSummary}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </button>
                            );
                        })}
                    </div>
                )}
            </div>

            {/* Selection count */}
            {multiSelect && (
                <p className="text-xs text-gray-400">
                    {selectedColumns.length} / {columns.length} sütun seçildi
                </p>
            )}
        </div>
    );
}
