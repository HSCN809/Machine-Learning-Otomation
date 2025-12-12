'use client';

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
import { FeatureImportance as FeatureImportanceType } from '@/types/model-selection';
import { theme } from '@/styles/theme';

interface FeatureImportanceProps {
    data: FeatureImportanceType[];
    title?: string;
}

export function FeatureImportance({ data, title = 'Feature Importance' }: FeatureImportanceProps) {
    // Sort by importance and take top 10
    const sortedData = [...data]
        .sort((a, b) => b.importance - a.importance)
        .slice(0, 10)
        .map(d => ({
            ...d,
            importance: Math.round(d.importance * 100) / 100,
        }));

    return (
        <div className="p-6 rounded-xl border border-white/10 bg-white/5">
            <h4 className="font-semibold text-white mb-4">{title}</h4>

            <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                        data={sortedData}
                        layout="vertical"
                        margin={{ top: 5, right: 30, left: 80, bottom: 5 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis
                            type="number"
                            tick={{ fill: '#9CA3AF', fontSize: 12 }}
                            axisLine={{ stroke: '#374151' }}
                            domain={[0, 1]}
                        />
                        <YAxis
                            type="category"
                            dataKey="feature"
                            tick={{ fill: '#9CA3AF', fontSize: 12 }}
                            axisLine={{ stroke: '#374151' }}
                            width={70}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: theme.colors.background.secondary,
                                border: `1px solid ${theme.colors.border.default}`,
                                borderRadius: '8px',
                                color: theme.colors.text.primary,
                            }}
                            formatter={(value: number) => [`${(value * 100).toFixed(1)}%`, 'Önem']}
                        />
                        <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
                            {sortedData.map((entry, index) => (
                                <Cell
                                    key={`cell-${index}`}
                                    fill={index === 0
                                        ? theme.colors.primary.cyan
                                        : index < 3
                                            ? theme.colors.secondary.green
                                            : theme.colors.accent.purple
                                    }
                                    style={{
                                        filter: index < 3 ? `drop-shadow(0 0 6px ${theme.colors.primary.cyan}40)` : undefined,
                                    }}
                                />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
