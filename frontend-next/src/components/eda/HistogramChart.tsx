'use client';

import { ReactNode } from 'react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Cell,
} from 'recharts';
import { HistogramData } from '@/types/eda';
import { theme } from '@/styles/theme';
import { ChartCard } from './ChartCard';

interface HistogramChartProps {
    data: HistogramData[];
    column: string;
    headerActions?: ReactNode;
}

export function HistogramChart({ data, column, headerActions }: HistogramChartProps) {
    return (
        <ChartCard
            title={`Histogram: ${column}`}
            description="Değer dağılımı"
            headerActions={headerActions}
        >
            <div className="mx-auto h-[420px] w-full max-w-[860px]">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis
                            dataKey="bin"
                            tick={{ fill: '#9CA3AF', fontSize: 12 }}
                            axisLine={{ stroke: '#374151' }}
                        />
                        <YAxis
                            tick={{ fill: '#9CA3AF', fontSize: 12 }}
                            axisLine={{ stroke: '#374151' }}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: theme.colors.background.secondary,
                                border: `1px solid ${theme.colors.border.default}`,
                                borderRadius: '8px',
                                color: theme.colors.text.primary,
                            }}
                            labelStyle={{ color: theme.colors.text.primary }}
                            itemStyle={{ color: '#FFFFFF' }}
                            formatter={(value: number, name: string) => {
                                if (name === 'count') return [value.toLocaleString('tr-TR'), 'Sayı'];
                                return [value, name];
                            }}
                        />
                        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                            {data.map((_, index) => (
                                <Cell
                                    key={`cell-${index}`}
                                    fill={theme.colors.primary.cyan}
                                    style={{
                                        filter: `drop-shadow(0 0 8px ${theme.colors.primary.cyan}50)`,
                                    }}
                                />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </ChartCard>
    );
}
