'use client';

import { useMemo } from 'react';
import { CorrelationData } from '@/types/eda';
import { theme } from '@/styles/theme';
import { ChartCard } from './ChartCard';

interface CorrelationMatrixProps {
    data: CorrelationData[];
    columns: string[];
}

export function CorrelationMatrix({ data, columns }: CorrelationMatrixProps) {
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

    return (
        <ChartCard
            title="Korelasyon Matrisi"
            description="Sayısal değişkenler arasındaki korelasyon"
        >
            <div className="overflow-x-auto">
                <div className="inline-block min-w-full">
                    {/* Header row */}
                    <div className="flex">
                        <div className="w-24 h-10 flex-shrink-0" /> {/* Empty corner cell */}
                        {columns.map(col => (
                            <div
                                key={`header-${col}`}
                                className="w-16 h-10 flex items-center justify-center text-xs text-gray-400 font-medium"
                                style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}
                            >
                                {col}
                            </div>
                        ))}
                    </div>

                    {/* Matrix rows */}
                    {columns.map(rowCol => (
                        <div key={`row-${rowCol}`} className="flex">
                            {/* Row label */}
                            <div className="w-24 h-14 flex items-center justify-end pr-3 text-xs text-gray-400 font-medium flex-shrink-0">
                                {rowCol}
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
        </ChartCard>
    );
}
