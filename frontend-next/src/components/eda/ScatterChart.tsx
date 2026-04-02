'use client';

import { ReactNode } from 'react';
import {
    ScatterChart as RechartsScatterChart,
    Scatter,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
} from 'recharts';
import { theme } from '@/styles/theme';
import { ChartCard } from './ChartCard';

interface ScatterChartProps {
    data: { x: number; y: number }[];
    xColumn: string;
    yColumn: string;
    headerActions?: ReactNode;
}

export function ScatterChart({ data, xColumn, yColumn, headerActions }: ScatterChartProps) {
    return (
        <ChartCard
            title={`Scatter Plot: ${xColumn} vs ${yColumn}`}
            description="İki sayısal değişken arasındaki ilişki"
            className="h-full"
            headerActions={headerActions}
        >
            <div className="h-[420px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <RechartsScatterChart margin={{ top: 24, right: 28, bottom: 24, left: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis
                            type="number"
                            dataKey="x"
                            name={xColumn}
                            tick={{ fill: '#9CA3AF', fontSize: 12 }}
                            axisLine={{ stroke: '#374151' }}
                            label={{
                                value: xColumn,
                                position: 'insideBottom',
                                offset: -8,
                                fill: '#9CA3AF',
                                fontSize: 12,
                            }}
                        />
                        <YAxis
                            type="number"
                            dataKey="y"
                            name={yColumn}
                            tick={{ fill: '#9CA3AF', fontSize: 12 }}
                            axisLine={{ stroke: '#374151' }}
                            label={{
                                value: yColumn,
                                angle: -90,
                                position: 'insideLeft',
                                offset: -2,
                                fill: '#9CA3AF',
                                fontSize: 12,
                            }}
                        />
                        <Tooltip
                            cursor={{ strokeDasharray: '3 3' }}
                            contentStyle={{
                                backgroundColor: theme.colors.background.secondary,
                                border: `1px solid ${theme.colors.border.default}`,
                                borderRadius: '8px',
                            }}
                            labelStyle={{ color: 'white' }}
                            itemStyle={{ color: 'white' }}
                            formatter={(value: number, name: string) => [value.toFixed(2), name]}
                        />
                        <Scatter
                            data={data}
                            fill={theme.colors.primary.cyan}
                            style={{
                                filter: `drop-shadow(0 0 4px ${theme.colors.primary.cyan}60)`,
                            }}
                        />
                    </RechartsScatterChart>
                </ResponsiveContainer>
            </div>
        </ChartCard>
    );
}
