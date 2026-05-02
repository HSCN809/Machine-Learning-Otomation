'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { Minus, Plus, RotateCcw } from 'lucide-react';
import { CorrelationData } from '@/types/eda';
import { theme } from '@/styles/theme';
import { ChartCard } from './ChartCard';

interface CorrelationMatrixProps {
    data: CorrelationData[];
    columns: string[];
}

export function CorrelationMatrix({ data, columns }: CorrelationMatrixProps) {
    const [zoom, setZoom] = useState(1);
    const [pan, setPan] = useState({ x: 0, y: 0 });
    const [dragStart, setDragStart] = useState<{ x: number; y: number } | null>(null);
    const viewportRef = useRef<HTMLDivElement | null>(null);
    const stageRef = useRef<HTMLDivElement | null>(null);
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
    const canZoomOut = zoom > 0.7;
    const canZoomIn = zoom < 1.6;
    const isDragging = dragStart !== null;
    const minZoom = 0.7;
    const maxZoom = 1.6;

    const centerStage = () => {
        const viewport = viewportRef.current;
        const stage = stageRef.current;
        if (!viewport || !stage) {
            return;
        }

        const viewportRect = viewport.getBoundingClientRect();
        const stageRect = stage.getBoundingClientRect();

        setPan({
            x: (viewportRect.width - stageRect.width) / 2,
            y: (viewportRect.height - stageRect.height) / 2,
        });
    };

    const handleResetView = () => {
        setZoom(1);
        requestAnimationFrame(centerStage);
    };

    useEffect(() => {
        centerStage();
    }, [columns.length]);

    return (
        <ChartCard
            title="Korelasyon Matrisi"
            description={`${columns.length} değişken arasındaki korelasyon`}
            className="h-full"
            headerActions={
                <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400">{Math.round(zoom * 100)}%</span>
                    <button
                        type="button"
                        onClick={() => setZoom((current) => Math.max(minZoom, Number((current - 0.15).toFixed(2))))}
                        disabled={!canZoomOut}
                        className="rounded-lg border border-white/10 p-2 text-gray-300 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
                        title="Uzaklaştır"
                    >
                        <Minus className="h-4 w-4" />
                    </button>
                    <button
                        type="button"
                        onClick={handleResetView}
                        disabled={zoom === 1 && pan.x === 0 && pan.y === 0}
                        className="rounded-lg border border-white/10 p-2 text-gray-300 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
                        title="Görünümü sıfırla"
                    >
                        <RotateCcw className="h-4 w-4" />
                    </button>
                    <button
                        type="button"
                        onClick={() => setZoom((current) => Math.min(maxZoom, Number((current + 0.15).toFixed(2))))}
                        disabled={!canZoomIn}
                        className="rounded-lg border border-white/10 p-2 text-gray-300 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
                        title="Yakınlaştır"
                    >
                        <Plus className="h-4 w-4" />
                    </button>
                </div>
            }
        >
            <div
                ref={viewportRef}
                className="h-[420px] overflow-hidden select-none"
                onWheel={(event) => {
                    event.preventDefault();
                    const delta = -event.deltaY * 0.0015;
                    setZoom((current) => {
                        const next = Number((current + delta).toFixed(3));
                        return Math.min(maxZoom, Math.max(minZoom, next));
                    });
                }}
                onMouseDown={(event) => {
                    if (event.button !== 0) {
                        return;
                    }

                    setDragStart({
                        x: event.clientX - pan.x,
                        y: event.clientY - pan.y,
                    });
                }}
                onMouseMove={(event) => {
                    if (!dragStart) {
                        return;
                    }

                    setPan({
                        x: event.clientX - dragStart.x,
                        y: event.clientY - dragStart.y,
                    });
                }}
                onMouseUp={() => setDragStart(null)}
                onMouseLeave={() => setDragStart(null)}
                style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
            >
                <div
                    ref={stageRef}
                    className="flex h-full w-max items-center gap-8"
                    style={{
                        transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                        transformOrigin: 'top left',
                    }}
                >
                    <div
                        className="inline-block min-w-fit"
                    >
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

