'use client';

import { ReactNode } from 'react';
import { BoxPlotData } from '@/types/eda';
import { theme } from '@/styles/theme';
import { ChartCard } from './ChartCard';

interface BoxPlotChartProps {
    data: BoxPlotData;
    column: string;
    headerActions?: ReactNode;
}

export function BoxPlotChart({ data, column, headerActions }: BoxPlotChartProps) {
    const iqr = data.q3 - data.q1;
    const lowerFence = data.q1 - 1.5 * iqr;
    const upperFence = data.q3 + 1.5 * iqr;

    const whiskerLow = Math.max(data.min, lowerFence);
    const whiskerHigh = Math.min(data.max, upperFence);

    const padding = { top: 28, bottom: 34, left: 68, right: 48 };
    const chartHeight = 300;
    const chartWidth = 420;

    const dataMin = data.min;
    const dataMax = data.max;
    const range = dataMax - dataMin || 1;

    const normalizeY = (value: number) => {
        const normalized = (value - dataMin) / range;
        return chartHeight - padding.bottom - normalized * (chartHeight - padding.top - padding.bottom);
    };

    const boxCenterX = chartWidth / 2;
    const boxWidth = 96;
    const whiskerWidth = 52;

    const yWhiskerLow = normalizeY(whiskerLow);
    const yQ1 = normalizeY(data.q1);
    const yMedian = normalizeY(data.median);
    const yQ3 = normalizeY(data.q3);
    const yWhiskerHigh = normalizeY(whiskerHigh);

    const tickCount = 5;
    const tickStep = range / (tickCount - 1);
    const ticks = Array.from({ length: tickCount }, (_, i) => dataMin + i * tickStep);

    return (
        <ChartCard
            title={`Box Plot - ${column}`}
            description="Seçilen sütunun dağılımı"
            headerActions={headerActions}
        >
            <div className="flex h-[420px] w-full flex-col">
                <div className="h-[300px] w-full">
                    <svg
                        viewBox={`0 0 ${chartWidth} ${chartHeight}`}
                        className="w-full h-full"
                        preserveAspectRatio="xMidYMid meet"
                    >
                        {ticks.map((tick, i) => (
                            <g key={i}>
                                <line
                                    x1={padding.left}
                                    y1={normalizeY(tick)}
                                    x2={chartWidth - padding.right}
                                    y2={normalizeY(tick)}
                                    stroke="#374151"
                                    strokeDasharray="3 3"
                                />
                                <text
                                    x={padding.left - 10}
                                    y={normalizeY(tick)}
                                    fill="#9CA3AF"
                                    fontSize="12"
                                    textAnchor="end"
                                    dominantBaseline="middle"
                                >
                                    {tick.toFixed(1)}
                                </text>
                            </g>
                        ))}

                        <line
                            x1={padding.left}
                            y1={padding.top}
                            x2={padding.left}
                            y2={chartHeight - padding.bottom}
                            stroke="#374151"
                        />

                        <line
                            x1={boxCenterX}
                            y1={yWhiskerLow}
                            x2={boxCenterX}
                            y2={yQ1}
                            stroke={theme.colors.primary.cyan}
                            strokeWidth="2"
                        />
                        <line
                            x1={boxCenterX - whiskerWidth / 2}
                            y1={yWhiskerLow}
                            x2={boxCenterX + whiskerWidth / 2}
                            y2={yWhiskerLow}
                            stroke={theme.colors.primary.cyan}
                            strokeWidth="2"
                        />

                        <line
                            x1={boxCenterX}
                            y1={yQ3}
                            x2={boxCenterX}
                            y2={yWhiskerHigh}
                            stroke={theme.colors.primary.cyan}
                            strokeWidth="2"
                        />
                        <line
                            x1={boxCenterX - whiskerWidth / 2}
                            y1={yWhiskerHigh}
                            x2={boxCenterX + whiskerWidth / 2}
                            y2={yWhiskerHigh}
                            stroke={theme.colors.primary.cyan}
                            strokeWidth="2"
                        />

                        <rect
                            x={boxCenterX - boxWidth / 2}
                            y={yQ3}
                            width={boxWidth}
                            height={yQ1 - yQ3}
                            fill={`${theme.colors.primary.cyan}30`}
                            stroke={theme.colors.primary.cyan}
                            strokeWidth="2"
                            rx="4"
                        />

                        <line
                            x1={boxCenterX - boxWidth / 2}
                            y1={yMedian}
                            x2={boxCenterX + boxWidth / 2}
                            y2={yMedian}
                            stroke={theme.colors.secondary.green}
                            strokeWidth="3"
                        />

                        {data.outliers?.map((outlier, i) => (
                            <circle
                                key={i}
                                cx={boxCenterX}
                                cy={normalizeY(outlier)}
                                r="4"
                                fill={theme.colors.status.warning}
                                stroke={theme.colors.status.warning}
                                strokeWidth="1"
                            />
                        ))}

                        <text
                            x={boxCenterX}
                            y={chartHeight - 6}
                            fill="#9CA3AF"
                            fontSize="12"
                            textAnchor="middle"
                        >
                            {column}
                        </text>
                    </svg>
                </div>

                <div className="mt-4 grid grid-cols-5 gap-2 text-xs">
                    <div className="text-center p-2 rounded-lg bg-white/5">
                        <div className="text-gray-400">Min</div>
                        <div className="text-white font-medium">{data.min.toFixed(2)}</div>
                    </div>
                    <div className="text-center p-2 rounded-lg bg-white/5">
                        <div className="text-gray-400">Q1</div>
                        <div className="text-white font-medium">{data.q1.toFixed(2)}</div>
                    </div>
                    <div className="text-center p-2 rounded-lg bg-white/5">
                        <div className="text-gray-400">Medyan</div>
                        <div className="text-white font-medium">{data.median.toFixed(2)}</div>
                    </div>
                    <div className="text-center p-2 rounded-lg bg-white/5">
                        <div className="text-gray-400">Q3</div>
                        <div className="text-white font-medium">{data.q3.toFixed(2)}</div>
                    </div>
                    <div className="text-center p-2 rounded-lg bg-white/5">
                        <div className="text-gray-400">Max</div>
                        <div className="text-white font-medium">{data.max.toFixed(2)}</div>
                    </div>
                </div>

                <div className="mt-4 flex items-center justify-center gap-6 text-xs text-gray-400">
                    <div className="flex items-center gap-2">
                        <div
                            className="w-4 h-4 rounded border-2"
                            style={{
                                borderColor: theme.colors.primary.cyan,
                                backgroundColor: `${theme.colors.primary.cyan}30`,
                            }}
                        />
                        <span>IQR</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-4 h-1 rounded" style={{ backgroundColor: theme.colors.secondary.green }} />
                        <span>Medyan</span>
                    </div>
                    {data.outliers && data.outliers.length > 0 && (
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: theme.colors.status.warning }} />
                            <span>{data.outliers.length} aykırı</span>
                        </div>
                    )}
                </div>
            </div>
        </ChartCard>
    );
}
