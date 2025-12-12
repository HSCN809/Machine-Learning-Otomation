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
    PieChart,
    Pie,
    Legend,
} from 'recharts';
import { CategoryData } from '@/types/eda';
import { theme } from '@/styles/theme';
import { ChartCard } from './ChartCard';

interface CategoryDistributionProps {
    data: CategoryData[];
    column: string;
    chartType?: 'bar' | 'pie';
}

const COLORS = [
    theme.colors.primary.cyan,
    theme.colors.secondary.green,
    theme.colors.accent.purple,
    theme.colors.status.warning,
    theme.colors.status.info,
];

export function CategoryDistribution({ data, column, chartType = 'bar' }: CategoryDistributionProps) {
    // Recharts için veriyi uygun formata dönüştür
    const chartData = data.map(d => ({
        name: d.name,
        value: d.value,
        percentage: d.percentage,
    }));

    if (chartType === 'pie') {
        return (
            <ChartCard
                title={`Kategorik Dağılım: ${column}`}
                description="Pasta grafiği"
            >
                <div className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={chartData}
                                dataKey="value"
                                nameKey="name"
                                cx="50%"
                                cy="50%"
                                outerRadius={100}
                                labelLine={{ stroke: '#6B7280' }}
                            >
                                {chartData.map((entry, index) => (
                                    <Cell
                                        key={`cell-${index}`}
                                        fill={COLORS[index % COLORS.length]}
                                        style={{
                                            filter: `drop-shadow(0 0 6px ${COLORS[index % COLORS.length]}40)`,
                                        }}
                                    />
                                ))}
                            </Pie>
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: theme.colors.background.secondary,
                                    border: `1px solid ${theme.colors.border.default}`,
                                    borderRadius: '8px',
                                    color: theme.colors.text.primary,
                                }}
                                formatter={(value: number) => [`${value.toLocaleString('tr-TR')}`, 'Değer']}
                            />
                            <Legend
                                wrapperStyle={{ color: theme.colors.text.secondary }}
                            />
                        </PieChart>
                    </ResponsiveContainer>
                </div>
            </ChartCard>
        );
    }

    return (
        <ChartCard
            title={`Kategorik Dağılım: ${column}`}
            description="Değer sayıları"
        >
            <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                        data={chartData}
                        layout="vertical"
                        margin={{ top: 10, right: 30, left: 80, bottom: 10 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis
                            type="number"
                            tick={{ fill: '#9CA3AF', fontSize: 12 }}
                            axisLine={{ stroke: '#374151' }}
                        />
                        <YAxis
                            type="category"
                            dataKey="name"
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
                            formatter={(value: number) => {
                                const item = chartData.find(d => d.value === value);
                                return [`${value.toLocaleString('tr-TR')} (${item?.percentage.toFixed(1)}%)`, 'Sayı'];
                            }}
                        />
                        <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                            {chartData.map((entry, index) => (
                                <Cell
                                    key={`cell-${index}`}
                                    fill={COLORS[index % COLORS.length]}
                                    style={{
                                        filter: `drop-shadow(0 0 6px ${COLORS[index % COLORS.length]}40)`,
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
