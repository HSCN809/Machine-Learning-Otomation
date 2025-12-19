'use client';

import {
    ComposedChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Cell,
    ReferenceLine,
} from 'recharts';
import { BoxPlotData } from '@/types/eda';
import { theme } from '@/styles/theme';
import { ChartCard } from './ChartCard';

interface BoxPlotChartProps {
    data: BoxPlotData;
    column: string;
}

// Transform box plot data for Recharts (single column)
function transformBoxPlotData(data: BoxPlotData) {
    return [{
        column: data.column,
        min: data.min,
        q1: data.q1,
        median: data.median,
        q3: data.q3,
        max: data.max,
        boxLow: data.q1,
        boxHigh: data.q3 - data.q1,
        whiskerLow: data.min,
        whiskerHigh: data.max,
        iqr: data.q3 - data.q1,
    }];
}

export function BoxPlotChart({ data, column }: BoxPlotChartProps) {
    const transformedData = transformBoxPlotData(data);

    return (
        <ChartCard
            title={`Box Plot - ${column}`}
            description="Seçilen sütunun dağılımı"
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
                            domain={['auto', 'auto']}
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
                        {/* Median line */}
                        <ReferenceLine
                            y={data.median}
                            stroke={theme.colors.secondary.green}
                            strokeWidth={2}
                            strokeDasharray="5 5"
                            label={{ value: `Medyan: ${data.median.toFixed(2)}`, fill: theme.colors.secondary.green, position: 'right' }}
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

            {/* Stats Summary */}
            <div className="grid grid-cols-5 gap-2 mt-4 text-sm">
                <div className="text-center p-2 rounded-lg bg-white/5">
                    <div className="text-gray-400">Min</div>
                    <div className="text-white font-medium">{data.min.toFixed(2)}</div>
                </div>
                <div className="text-center p-2 rounded-lg bg-white/5">
                    <div className="text-gray-400">Q1</div>
                    <div className="text-white font-medium">{data.q1.toFixed(2)}</div>
                </div>
                <div className="text-center p-2 rounded-lg bg-white/5" style={{ borderColor: theme.colors.secondary.green, borderWidth: 1 }}>
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

            {/* Outliers count */}
            {data.outliers && data.outliers.length > 0 && (
                <div className="mt-3 text-sm text-gray-400">
                    <span className="text-yellow-400">{data.outliers.length}</span> aykırı değer tespit edildi
                </div>
            )}

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

