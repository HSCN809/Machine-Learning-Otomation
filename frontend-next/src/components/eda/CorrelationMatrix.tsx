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
    const headerSizeClassName = isCompactMatrix ? 'w-16 h-7 text-xs' : 'w-20 h-8 text-sm';
    const rowHeaderSizeClassName = isCompactMatrix ? 'w-16 h-14 text-xs' : 'w-20 h-18 text-sm';
    const cornerSpacerClassName = isCompactMatrix ? 'w-16 h-7' : 'w-20 h-8';
    const cellSizeClassName = isCompactMatrix ? 'w-16 h-14 text-xs' : 'w-20 h-18 text-sm';
    const legendItems = [
        { label: '-1.0', color: theme.colors.status.error },
        { label: '-0.5', color: theme.colors.status.warning },
        { label: '0', color: theme.colors.status.info },
        { label: '+0.5', color: theme.colors.primary.cyan },
        { label: '+1.0', color: theme.colors.secondary.green },
    ];

    return (
        <ChartCard
            title="Korelasyon Matrisi"
            description={`${columns.length} değişken arasındaki korelasyon`}
            className="h-full"
        >
            <div className="h-[420px] overflow-auto">
                <div className="flex h-full items-center justify-center gap-8">
                    <div className="inline-block min-w-fit">
                        <div className="flex">
                            <div className={`${cornerSpacerClassName} m-0.5`} />
                            {columns.map((col) => (
                                <div
                                    key={`header-${col}`}
                                    className={`${headerSizeClassName} m-0.5 flex items-center justify-center font-medium text-gray-400 cursor-help`}
                                    title={col}
                                >
                                    {col.slice(0, 3)}
                                </div>
                            ))}
                        </div>

                        {columns.map((rowCol) => (
                            <div key={`row-${rowCol}`} className="flex">
                                <div
                                    className={`${rowHeaderSizeClassName} m-0.5 flex items-center justify-center font-medium text-gray-400 cursor-help`}
                                    title={rowCol}
                                >
                                    {rowCol.slice(0, 3)}
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

                    <div className="flex flex-col gap-3 self-center text-sm text-gray-400">
                        {legendItems.map((item) => (
                            <div key={item.label} className="flex items-center gap-2">
                                <div className="h-4 w-4 rounded" style={{ backgroundColor: item.color }} />
                                <span>{item.label}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </ChartCard>
    );
}
