'use client';

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
                return 'Sayısal';
            case 'categorical':
                return 'Kategorik';
            case 'datetime':
                return 'Tarih/Saat';
            default:
                return 'Metin';
        }
    };

    return (
        <div className="rounded-xl border border-white/10 overflow-hidden">
            <div className="overflow-x-auto">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b border-white/10 bg-white/5">
                            <th className="px-4 py-3 text-left font-medium text-gray-400">Sütun Adı</th>
                            <th className="px-4 py-3 text-left font-medium text-gray-400">Veri Tipi</th>
                            <th className="px-4 py-3 text-left font-medium text-gray-400">dtype</th>
                            <th className="px-4 py-3 text-left font-medium text-gray-400">Eksik</th>
                            <th className="px-4 py-3 text-left font-medium text-gray-400">Eksik %</th>
                        </tr>
                    </thead>
                    <tbody>
                        {columnTypes.map((col, index) => (
                            <tr
                                key={col.name}
                                className="border-b border-white/5 hover:bg-white/5 transition-colors"
                            >
                                <td className="px-4 py-3 font-medium text-white">{col.name}</td>
                                <td className="px-4 py-3">
                                    <span
                                        className="px-2 py-1 rounded-md text-xs font-medium"
                                        style={{
                                            backgroundColor: `${getTypeColor(col.type)}20`,
                                            color: getTypeColor(col.type),
                                        }}
                                    >
                                        {getTypeLabel(col.type)}
                                    </span>
                                </td>
                                <td className="px-4 py-3 text-gray-400 font-mono text-xs">{col.dtype}</td>
                                <td className="px-4 py-3 text-gray-400">{col.nullCount.toLocaleString('tr-TR')}</td>
                                <td className="px-4 py-3">
                                    <span
                                        style={{
                                            color: col.nullPercentage > 5 ? theme.colors.status.warning : theme.colors.text.secondary,
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
