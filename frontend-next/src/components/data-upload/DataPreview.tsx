'use client';

import { Table, ChevronLeft, ChevronRight } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';
import { theme } from '@/styles/theme';
import { DataSummary } from '@/types/data-upload';

interface DataPreviewProps {
    summary: DataSummary;
}

export function DataPreview({ summary }: DataPreviewProps) {
    const [currentPage, setCurrentPage] = useState(0);
    const rowsPerPage = 10;
    const totalPages = Math.ceil(summary.preview.length / rowsPerPage);

    const { shape, missingValues, duplicateRows } = summary;

    return (
        <div className="space-y-6">
            {/* Stats cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard
                    label="Satır Sayısı"
                    value={shape.rows.toLocaleString('tr-TR')}
                    color={theme.colors.primary.cyan}
                />
                <StatCard
                    label="Sütun Sayısı"
                    value={shape.columns.toString()}
                    color={theme.colors.secondary.green}
                />
                <StatCard
                    label="Eksik Değer"
                    value={`${missingValues.percentage.toFixed(1)}%`}
                    color={missingValues.percentage > 5 ? theme.colors.status.warning : theme.colors.status.success}
                />
                <StatCard
                    label="Tekrar Satır"
                    value={duplicateRows.toString()}
                    color={duplicateRows > 0 ? theme.colors.status.warning : theme.colors.status.success}
                />
            </div>

            {/* Data table preview */}
            {summary.preview.length > 0 && (
                <div className="rounded-xl border border-white/10 overflow-hidden">
                    <div className="flex items-center justify-between px-4 py-3 bg-white/5 border-b border-white/10">
                        <div className="flex items-center gap-2">
                            <Table className="w-5 h-5 text-cyan-400" />
                            <span className="font-medium text-white">Veri Önizlemesi</span>
                        </div>
                        <span className="text-sm text-gray-400">
                            İlk {Math.min(rowsPerPage, summary.preview.length)} satır gösteriliyor
                        </span>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-white/10 bg-white/5">
                                    {Object.keys(summary.preview[0] || {}).map((column) => (
                                        <th
                                            key={column}
                                            className="px-4 py-3 text-left font-medium text-gray-400 whitespace-nowrap"
                                        >
                                            {column}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {summary.preview
                                    .slice(currentPage * rowsPerPage, (currentPage + 1) * rowsPerPage)
                                    .map((row, rowIndex) => (
                                        <tr
                                            key={rowIndex}
                                            className="border-b border-white/5 hover:bg-white/5 transition-colors"
                                        >
                                            {Object.values(row).map((value, colIndex) => (
                                                <td
                                                    key={colIndex}
                                                    className="px-4 py-2.5 text-white whitespace-nowrap"
                                                >
                                                    {value === null || value === undefined ? (
                                                        <span className="text-gray-500 italic">null</span>
                                                    ) : (
                                                        String(value)
                                                    )}
                                                </td>
                                            ))}
                                        </tr>
                                    ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination */}
                    {totalPages > 1 && (
                        <div className="flex items-center justify-between px-4 py-3 bg-white/5 border-t border-white/10">
                            <span className="text-sm text-gray-400">
                                Sayfa {currentPage + 1} / {totalPages}
                            </span>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={() => setCurrentPage((p) => Math.max(0, p - 1))}
                                    disabled={currentPage === 0}
                                    className="p-2 rounded-lg hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                >
                                    <ChevronLeft className="w-4 h-4 text-gray-400" />
                                </button>
                                <button
                                    onClick={() => setCurrentPage((p) => Math.min(totalPages - 1, p + 1))}
                                    disabled={currentPage === totalPages - 1}
                                    className="p-2 rounded-lg hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                >
                                    <ChevronRight className="w-4 h-4 text-gray-400" />
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

interface StatCardProps {
    label: string;
    value: string;
    color: string;
}

function StatCard({ label, value, color }: StatCardProps) {
    return (
        <div
            className="p-4 rounded-xl border border-white/10"
            style={{
                background: `linear-gradient(135deg, ${color}10 0%, transparent 100%)`,
            }}
        >
            <p className="text-sm text-gray-400 mb-1">{label}</p>
            <p className="text-2xl font-bold" style={{ color }}>
                {value}
            </p>
        </div>
    );
}
