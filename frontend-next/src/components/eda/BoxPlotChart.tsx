'use client';

import {
    ComposedChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ErrorBar,
    Cell,
    ReferenceLine,
} from 'recharts';
import { BoxPlotData } from '@/types/eda';
import { theme } from '@/styles/theme';
import { ChartCard } from './ChartCard';

interface BoxPlotChartProps {
    data: BoxPlotData[];
}

// Transform box plot data for Recharts
function transformBoxPlotData(data: BoxPlotData[]) {
    return data.map(d => ({
        column: d.column,
        min: d.min,
        q1: d.q1,
        median: d.median,
        q3: d.q3,
        max: d.max,
        boxLow: d.q1,
        boxHigh: d.q3 - d.q1,
        whiskerLow: d.min,
        whiskerHigh: d.max,
        iqr: d.q3 - d.q1,
    }));
}

export function BoxPlotChart({ data }: BoxPlotChartProps) {
    const transformedData = transformBoxPlotData(data);

    return (
        <ChartCard
            title="Box Plot"
            description="Sayısal sütunların dağılımı"
        >
            <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart
                        data={transformedData}
                        margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis
                            dataKey="column"
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
                            formatter={(value: number, name: string) => {
                                const labels: Record<string, string> = {
                                    min: 'Min',
                                    q1: 'Q1',
                                    median: 'Medyan',
                                    q3: 'Q3',
                                    max: 'Max',
                                    boxHigh: 'IQR',
                                };
                                return [value.toFixed(2), labels[name] || name];
                            }}
                        />
                        {/* Box */}
                        <Bar dataKey="boxHigh" stackId="box" fill={theme.colors.primary.cyan} radius={[4, 4, 4, 4]}>
                            {transformedData.map((entry, index) => (
                                <Cell
                                    key={`cell-${index}`}
                                    fill={theme.colors.primary.cyan}
                                    style={{
                                        filter: `drop-shadow(0 0 6px ${theme.colors.primary.cyan}40)`,
                                    }}
                                />
                            ))}
                        </Bar>
                    </ComposedChart>
                </ResponsiveContainer>
            </div>

            {/* Legend */}
            <div className="flex items-center justify-center gap-6 mt-4 text-sm text-gray-400">
                <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded" style={{ backgroundColor: theme.colors.primary.cyan }} />
                    <span>IQR (Q1-Q3)</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-4 h-0.5" style={{ backgroundColor: theme.colors.secondary.green }} />
                    <span>Medyan</span>
                </div>
            </div>
        </ChartCard>
    );
}
