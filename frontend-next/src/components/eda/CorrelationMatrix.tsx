'use client';

import { useState, useMemo } from 'react';
import { ChevronDown, ChevronUp, Grid3X3 } from 'lucide-react';
import { CorrelationData } from '@/types/eda';
import { theme } from '@/styles/theme';

interface CorrelationMatrixProps {
    data: CorrelationData[];
    columns: string[];
}

export function CorrelationMatrix({ data, columns }: CorrelationMatrixProps) {
    const [isExpanded, setIsExpanded] = useState(true);

    // Create a matrix from the correlation data
    const matrix = useMemo(() => {
        const matrixData: Record<string, Record<string, number>> = {};
        data.forEach(d => {
            if (!matrixData[d.y]) matrixData[d.y] = {};
            matrixData[d.y][d.x] = d.value;
        });
        return matrixData;
    }, [data]);

    // Get color based on correlation value
    const getColor = (value: number) => {
        if (value >= 0.7) return theme.colors.secondary.green;
        if (value >= 0.4) return theme.colors.primary.cyan;
        if (value >= 0) return theme.colors.status.info;
        if (value >= -0.4) return theme.colors.status.warning;
        return theme.colors.status.error;
    };

    const getOpacity = (value: number) => {
        return Math.abs(value) * 0.8 + 0.2;
    };

    // Calculate container width based on columns (96px for row labels + 68px per column cell)
    const containerWidth = 68 + (columns.length * 68) + 32; // +32 for padding

    return (
        <div
            className="rounded-xl border border-white/10 overflow-hidden mx-auto"
            style={{
                background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.6) 0%, rgba(31, 41, 55, 0.4) 100%)',
                width: `${containerWidth}px`,
                maxWidth: '100%',
            }}
        >
            {/* Collapsible Header */}
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full flex items-center justify-between px-4 py-3 border-b border-white/10 hover:bg-white/5 transition-colors cursor-pointer"
            >
                <div className="flex items-center gap-3">
                    <Grid3X3 className="w-5 h-5 text-cyan-400" />
                    <div className="text-left">
                        <span className="font-semibold text-white">Korelasyon Matrisi</span>
                        <p className="text-sm text-gray-400 mt-0.5">
                            {columns.length} değişken arasındaki korelasyon
                        </p>
                    </div>
                </div>
                {isExpanded ? (
                    <ChevronUp className="w-5 h-5 text-gray-400" />
                ) : (
                    <ChevronDown className="w-5 h-5 text-gray-400" />
                )}
            </button>

            {/* Collapsible Content */}
            {isExpanded && (
                <div className="p-4">
                    <div className="flex justify-center">
                        <div className="inline-block">
                            {/* Header row */}
                            <div className="flex">
                                <div className="w-16 h-6 flex-shrink-0" /> {/* Empty corner cell */}
                                {columns.map(col => (
                                    <div
                                        key={`header-${col}`}
                                        className="w-16 h-6 flex items-center justify-center text-xs text-gray-400 font-medium cursor-help m-0.5"
                                        title={col}
                                    >
                                        {col.length > 3 ? `${col.slice(0, 3)}..` : col}
                                    </div>
                                ))}
                            </div>

                            {/* Matrix rows */}
                            {columns.map(rowCol => (
                                <div key={`row-${rowCol}`} className="flex">
                                    {/* Row label */}
                                    <div
                                        className="w-16 h-14 flex items-center justify-center text-xs text-gray-400 font-medium flex-shrink-0 cursor-help m-0.5"
                                        title={rowCol}
                                    >
                                        {rowCol.length > 3 ? `${rowCol.slice(0, 3)}..` : rowCol}
                                    </div>

                                    {/* Cells */}
                                    {columns.map(colCol => {
                                        const value = matrix[rowCol]?.[colCol] ?? 0;
                                        const isMainDiagonal = rowCol === colCol;

                                        return (
                                            <div
                                                key={`cell-${rowCol}-${colCol}`}
                                                className="w-16 h-14 flex items-center justify-center text-xs font-medium border border-white/5 rounded-md m-0.5 transition-all duration-200 hover:scale-110 cursor-pointer"
                                                style={{
                                                    backgroundColor: getColor(value),
                                                    opacity: getOpacity(value),
                                                    color: isMainDiagonal ? 'white' : Math.abs(value) > 0.5 ? 'white' : theme.colors.text.primary,
                                                    boxShadow: Math.abs(value) > 0.6 ? `0 0 10px ${getColor(value)}40` : undefined,
                                                }}
                                                title={`${rowCol} ↔ ${colCol}: ${value.toFixed(3)}`}
                                            >
                                                {value.toFixed(2)}
                                            </div>
                                        );
                                    })}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Legend */}
                    <div className="flex items-center justify-center gap-4 mt-4 text-xs text-gray-400">
                        <div className="flex items-center gap-6">
                            <div className="flex items-center gap-1">
                                <div className="w-4 h-4 rounded" style={{ backgroundColor: theme.colors.status.error }} />
                                <span>-1.0</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <div className="w-4 h-4 rounded" style={{ backgroundColor: theme.colors.status.warning }} />
                                <span>-0.5</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <div className="w-4 h-4 rounded" style={{ backgroundColor: theme.colors.status.info }} />
                                <span>0</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <div className="w-4 h-4 rounded" style={{ backgroundColor: theme.colors.primary.cyan }} />
                                <span>+0.5</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <div className="w-4 h-4 rounded" style={{ backgroundColor: theme.colors.secondary.green }} />
                                <span>+1.0</span>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
