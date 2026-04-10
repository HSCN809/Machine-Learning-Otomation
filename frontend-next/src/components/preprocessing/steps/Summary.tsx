'use client';

import { ProcessingHistory, ColumnInfo } from '@/types/preprocessing';
import { theme } from '@/styles/theme';
import { CheckCircle, Download, ArrowRight } from 'lucide-react';
import Link from 'next/link';

interface SummaryProps {
    history: ProcessingHistory[];
    columns: ColumnInfo[];
    originalColumnCount: number;
}

export function Summary({ history, columns, originalColumnCount }: SummaryProps) {
    const stepCounts = history.reduce((acc, item) => {
        acc[item.stepKey] = (acc[item.stepKey] || 0) + 1;
        return acc;
    }, {} as Record<string, number>);

    const stepLabels: Record<string, string> = {
        feature_engineering: 'Feature Engineering',
        missing_values: 'Eksik Değerler',
        outliers: 'Aykırı Değerler',
        encoding: 'Encoding',
        scaling: 'Scaling',
    };

    const newColumnsCount = columns.length - originalColumnCount;
    const totalAffectedRows = history.reduce((sum, h) => sum + (h.affectedRows || 0), 0);

    return (
        <div className="space-y-6">
            {/* Success message */}
            <div
                className="p-6 rounded-xl border text-center"
                style={{
                    borderColor: `${theme.colors.status.success}50`,
                    background: `${theme.colors.status.success}10`,
                }}
            >
                <CheckCircle
                    className="w-16 h-16 mx-auto mb-4"
                    style={{ color: theme.colors.status.success }}
                />
                <h2 className="text-2xl font-bold text-white mb-2">
                    Ön İşleme Tamamlandı!
                </h2>
                <p className="text-gray-400">
                    Verileriniz başarıyla işlendi ve model eğitimine hazır.
                </p>
            </div>

            {/* Stats grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard
                    label="Toplam İşlem"
                    value={history.length.toString()}
                    color={theme.colors.primary.cyan}
                />
                <StatCard
                    label="Etkilenen Satır"
                    value={totalAffectedRows.toLocaleString('tr-TR')}
                    color={theme.colors.secondary.green}
                />
                <StatCard
                    label="Mevcut Sütun"
                    value={columns.length.toString()}
                    color={theme.colors.accent.purple}
                />
                <StatCard
                    label="Yeni Sütun"
                    value={newColumnsCount > 0 ? `+${newColumnsCount}` : '0'}
                    color={theme.colors.status.warning}
                />
            </div>

            {/* Steps summary */}
            <div className="rounded-xl border border-white/10 overflow-hidden">
                <div className="px-4 py-3 bg-white/5 border-b border-white/10">
                    <h3 className="font-medium text-white">Uygulanan Adımlar</h3>
                </div>
                <div className="divide-y divide-white/5">
                    {Object.entries(stepCounts).map(([stepKey, count]) => (
                        <div
                            key={stepKey}
                            className="flex items-center justify-between px-4 py-3"
                        >
                            <span className="text-gray-300">{stepLabels[stepKey] || stepKey}</span>
                            <span className="px-2 py-1 rounded-full text-xs bg-cyan-500/20 text-cyan-400">
                                {count} işlem
                            </span>
                        </div>
                    ))}
                    {Object.keys(stepCounts).length === 0 && (
                        <div className="px-4 py-6 text-center text-gray-500">
                            Henüz işlem yapılmadı
                        </div>
                    )}
                </div>
            </div>

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-4">
                <button
                    className="cursor-pointer flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-xl border border-white/20 text-white hover:bg-white/5 transition-all"
                >
                    <Download className="w-5 h-5" />
                    İşlenmiş Veriyi İndir
                </button>
                <Link
                    href="/model"
                    className="flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-medium text-white transition-all hover:scale-105"
                    style={{
                        background: theme.gradients.primary,
                        boxShadow: theme.glow.cyan,
                    }}
                >
                    Model Eğitimine Geç
                    <ArrowRight className="w-5 h-5" />
                </Link>
            </div>
        </div>
    );
}

function StatCard({ label, value, color }: { label: string; value: string; color: string }) {
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
