'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, Database } from 'lucide-react';
import { ColumnType } from '@/types/eda';
import { theme } from '@/styles/theme';

interface DataTypesTableProps {
    columnTypes: ColumnType[];
}

export function DataTypesTable({ columnTypes }: DataTypesTableProps) {
    const [isExpanded, setIsExpanded] = useState(true);

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

    const getDtypeColor = (dtype: string) => {
        if (dtype.includes('int')) {
            return theme.colors.primary.cyan;
        } else if (dtype.includes('float')) {
            return theme.colors.accent.purple;
        } else if (dtype === 'object' || dtype === 'string') {
            return theme.colors.secondary.green;
        } else if (dtype.includes('datetime') || dtype.includes('date')) {
            return '#F472B6'; // pink
        } else if (dtype === 'bool' || dtype === 'boolean') {
            return '#FBBF24'; // amber
        }
        return theme.colors.text.secondary;
    };

    // Count columns with missing values
    const columnsWithMissing = columnTypes.filter(col => col.nullCount > 0).length;

    return (
        <div className="rounded-xl border border-white/10 overflow-hidden">
            {/* Collapsible Header */}
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full flex items-center justify-between px-4 py-3 bg-white/5 border-b border-white/10 hover:bg-white/10 transition-colors cursor-pointer"
            >
                <div className="flex items-center gap-3">
                    <Database className="w-5 h-5 text-cyan-400" />
                    <div className="text-left">
                        <span className="font-medium text-white">Sütun Bilgileri</span>
                        <span className="text-sm text-gray-400 ml-2">
                            ({columnTypes.length} sütun{columnsWithMissing > 0 && `, ${columnsWithMissing} eksik değerli`})
                        </span>
                    </div>
                </div>
                {isExpanded ? (
                    <ChevronUp className="w-5 h-5 text-gray-400" />
                ) : (
                    <ChevronDown className="w-5 h-5 text-gray-400" />
                )}
            </button>

            {/* Collapsible Content */}
            {isExpanded && (
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
                            {columnTypes.map((col) => (
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
                                    <td className="px-4 py-3">
                                        <span
                                            className="px-2 py-1 rounded-md text-xs font-mono"
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
                                                color: col.nullCount > 0 ? theme.colors.status.warning : theme.colors.text.secondary,
                                                fontWeight: col.nullCount > 0 ? 500 : 400,
                                            }}
                                        >
                                            {col.nullCount.toLocaleString('tr-TR')}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3">
                                        <span
                                            style={{
                                                color: col.nullPercentage > 0 ? theme.colors.status.warning : theme.colors.text.secondary,
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
            )}
        </div>
    );
}
