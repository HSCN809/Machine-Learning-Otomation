'use client';

import { BarChart3, Hash, FileText, AlertTriangle, Copy } from 'lucide-react';
import { theme } from '@/styles/theme';
import { NumericStats, CategoricalStats, ColumnType } from '@/types/eda';

interface StatsSummaryProps {
    numericStats: NumericStats[];
    categoricalStats: CategoricalStats[];
    columnTypes: ColumnType[];
    duplicateRows: number;
}

import React from 'react';

export const StatsSummary = React.memo(function StatsSummary({
    numericStats,
    categoricalStats,
    columnTypes,
    duplicateRows,
}: StatsSummaryProps) {
    const totalRows = numericStats[0]?.count || categoricalStats[0]?.count || 0;
    const totalColumns = columnTypes.length;
    const numericCount = numericStats.length;
    const categoricalCount = categoricalStats.length;
    const totalNulls = columnTypes.reduce((sum, col) => sum + col.nullCount, 0);
    const nullPercentage = totalRows > 0 ? (totalNulls / (totalRows * totalColumns)) * 100 : 0;

    const stats = [
        {
            label: 'Toplam Satır',
            value: totalRows.toLocaleString('tr-TR'),
            icon: BarChart3,
            color: theme.colors.primary.cyan,
        },
        {
            label: 'Toplam Sütun',
            value: totalColumns.toString(),
            icon: Hash,
            color: theme.colors.secondary.green,
        },
        {
            label: 'Sayısal Sütun',
            value: numericCount.toString(),
            icon: FileText,
            color: theme.colors.accent.purple,
        },
        {
            label: 'Kategorik Sütun',
            value: categoricalCount.toString(),
            icon: FileText,
            color: theme.colors.status.info,
        },
        {
            label: 'Eksik Değer',
            value: `${nullPercentage.toFixed(1)}%`,
            icon: AlertTriangle,
            color: nullPercentage > 5 ? theme.colors.status.warning : theme.colors.status.success,
        },
        {
            label: 'Tekrarlayan Satır',
            value: duplicateRows.toLocaleString('tr-TR'),
            icon: Copy,
            color: duplicateRows > 0 ? theme.colors.status.warning : theme.colors.status.success,
        },
    ];

    return (
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
            {stats.map((stat) => {
                const Icon = stat.icon;
                return (
                    <div
                        key={stat.label}
                        className="p-4 rounded-xl border border-white/10"
                        style={{
                            background: `linear-gradient(135deg, ${stat.color}10 0%, transparent 100%)`,
                        }}
                    >
                        <div className="flex items-center gap-2 mb-2">
                            <Icon className="w-4 h-4" style={{ color: stat.color }} />
                            <span className="text-sm text-gray-400">{stat.label}</span>
                        </div>
                        <p className="text-2xl font-bold" style={{ color: stat.color }}>
                            {stat.value}
                        </p>
                    </div>
                );
            })}
        </div>
    );
});
