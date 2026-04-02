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
    const matrix = useMemo(() => {
        const matrixData: Record<string, Record<string, number>> = {};
        data.forEach((d) => {
            if (!matrixData[d.y]) matrixData[d.y] = {};
            matrixData[d.y][d.x] = d.value;
        });
        return matrixData;
    }, [data]);

    const getColor = (value: number) => {
        if (value >= 0.7) return theme.colors.secondary.green;
        if (value >= 0.4) return theme.colors.primary.cyan;
        if (value >= 0) return theme.colors.status.info;
        if (value >= -0.4) return theme.colors.status.warning;
        return theme.colors.status.error;
    };

    const getOpacity = (value: number) => Math.abs(value) * 0.8 + 0.2;
    const isCompactMatrix = columns.length > 4;
    const headerSizeClassName = isCompactMatrix ? 'w-16 h-6 text-xs' : 'w-20 h-8 text-sm';
    const rowLabelSizeClassName = isCompactMatrix ? 'w-16 h-14 text-xs' : 'w-20 h-18 text-sm';
    const cellSizeClassName = isCompactMatrix ? 'w-16 h-14 text-xs' : 'w-20 h-18 text-sm';

    return (
        <ChartCard
            title="Korelasyon Matrisi"
            description={`${columns.length} değişken arasındaki korelasyon`}
            className="h-full"
        >
            <div className="h-[420px] overflow-auto">
                <div className="flex h-full items-center justify-center">
                    <div className="inline-block min-w-fit">
                        <div className="flex">
                            <div className={`${rowLabelSizeClassName} flex-shrink-0`} />
                            {columns.map((col) => (
                                <div
                                    key={`header-${col}`}
                                    className={`${headerSizeClassName} m-0.5 flex items-center justify-center font-medium text-gray-400 cursor-help`}
                                    title={col}
                                >
                                    {col.length > 3 ? `${col.slice(0, 3)}..` : col}
                                </div>
                            ))}
                        </div>

                        {columns.map((rowCol) => (
                            <div key={`row-${rowCol}`} className="flex">
                                <div
                                    className={`${rowLabelSizeClassName} m-0.5 flex flex-shrink-0 items-center justify-center font-medium text-gray-400 cursor-help`}
                                    title={rowCol}
                                >
                                    {rowCol.length > 3 ? `${rowCol.slice(0, 3)}..` : rowCol}
                                </div>

                                {columns.map((colCol) => {
                                    const value = matrix[rowCol]?.[colCol] ?? 0;
                                    const isMainDiagonal = rowCol === colCol;

                                    return (
                                        <div
                                            key={`cell-${rowCol}-${colCol}`}
                                            className={`${cellSizeClassName} m-0.5 flex items-center justify-center rounded-md border border-white/5 font-medium transition-all duration-200 hover:scale-110 cursor-pointer`}
                                            style={{
                                                backgroundColor: getColor(value),
                                                opacity: getOpacity(value),
                                                color: isMainDiagonal
                                                    ? 'white'
                                                    : Math.abs(value) > 0.5
                                                      ? 'white'
                                                      : theme.colors.text.primary,
                                                boxShadow:
                                                    Math.abs(value) > 0.6
                                                        ? `0 0 10px ${getColor(value)}40`
                                                        : undefined,
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
        </ChartCard>
    );
}
