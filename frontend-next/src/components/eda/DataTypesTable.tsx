'use client';

import { Database } from 'lucide-react';
import { ColumnType } from '@/types/eda';
import { theme } from '@/styles/theme';

interface DataTypesTableProps {
    columnTypes: ColumnType[];
}

export function DataTypesTable({ columnTypes }: DataTypesTableProps) {
    const getTypeColor = (type: string) => {
        switch (type) {
            case 'numeric':
                return theme.colors.primary.cyan;
            case 'categorical':
                return theme.colors.secondary.green;
            case 'datetime':
                return theme.colors.accent.purple;
            default:
                return theme.colors.text.secondary;
        }
    };

    const getTypeLabel = (type: string) => {
        switch (type) {
            case 'numeric':
                return 'Sayisal';
            case 'categorical':
                return 'Kategorik';
            case 'datetime':
                return 'Tarih/Saat';
            default:
                return 'Metin';
        }
    };

    const getDtypeColor = (dtype: string) => {
        if (dtype.includes('int')) {
            return theme.colors.primary.cyan;
        }
        if (dtype.includes('float')) {
            return theme.colors.accent.purple;
        }
        if (dtype === 'object' || dtype === 'string') {
            return theme.colors.secondary.green;
        }
        if (dtype.includes('datetime') || dtype.includes('date')) {
            return '#F472B6';
        }
        if (dtype === 'bool' || dtype === 'boolean') {
            return '#FBBF24';
        }
        return theme.colors.text.secondary;
    };

    const columnsWithMissing = columnTypes.filter((col) => col.nullCount > 0).length;

    return (
        <div className="overflow-hidden rounded-xl border border-white/10">
            <div className="flex w-full items-center justify-between border-b border-white/10 bg-white/5 px-4 py-3">
                <div className="flex items-center gap-3">
                    <Database className="h-5 w-5 text-cyan-400" />
                    <div className="text-left">
                        <span className="font-medium text-white">Sutun Bilgileri</span>
                        <span className="ml-2 text-sm text-gray-400">
                            ({columnTypes.length} sutun{columnsWithMissing > 0 && `, ${columnsWithMissing} eksik degerli`})
                        </span>
                    </div>
                </div>
            </div>

            <div className="max-h-[352px] overflow-auto">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="sticky top-0 z-10 border-b border-white/10 bg-[rgba(17,24,39,0.96)] backdrop-blur-sm">
                            <th className="px-4 py-3 text-left font-medium text-gray-400">Sutun Adi</th>
                            <th className="px-4 py-3 text-left font-medium text-gray-400">Veri Tipi</th>
                            <th className="px-4 py-3 text-left font-medium text-gray-400">dtype</th>
                            <th className="px-4 py-3 text-left font-medium text-gray-400">Eksik</th>
                            <th className="px-4 py-3 text-left font-medium text-gray-400">Eksik %</th>
                        </tr>
                    </thead>
                    <tbody>
                        {columnTypes.map((col) => (
                            <tr
                                key={col.name}
                                className="border-b border-white/5 transition-colors hover:bg-white/5"
                            >
                                <td className="px-4 py-3 font-medium text-white">{col.name}</td>
                                <td className="px-4 py-3">
                                    <span
                                        className="rounded-md px-2 py-1 text-xs font-medium"
                                        style={{
                                            backgroundColor: `${getTypeColor(col.type)}20`,
                                            color: getTypeColor(col.type),
                                        }}
                                    >
                                        {getTypeLabel(col.type)}
                                    </span>
                                </td>
                                <td className="px-4 py-3">
                                    <span
                                        className="rounded-md px-2 py-1 text-xs font-mono"
                                        style={{
                                            backgroundColor: `${getDtypeColor(col.dtype)}15`,
                                            color: getDtypeColor(col.dtype),
                                        }}
                                    >
                                        {col.dtype}
                                    </span>
                                </td>
                                <td className="px-4 py-3">
                                    <span
                                        style={{
                                            color:
                                                col.nullCount > 0
                                                    ? theme.colors.status.warning
                                                    : theme.colors.text.secondary,
                                            fontWeight: col.nullCount > 0 ? 500 : 400,
                                        }}
                                    >
                                        {col.nullCount.toLocaleString('tr-TR')}
                                    </span>
                                </td>
                                <td className="px-4 py-3">
                                    <span
                                        style={{
                                            color:
                                                col.nullPercentage > 0
                                                    ? theme.colors.status.warning
                                                    : theme.colors.text.secondary,
                                            fontWeight: col.nullPercentage > 0 ? 500 : 400,
                                        }}
                                    >
                                        {col.nullPercentage.toFixed(1)}%
                                    </span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
