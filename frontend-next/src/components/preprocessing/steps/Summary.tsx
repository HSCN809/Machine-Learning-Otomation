'use client';

import { useState } from 'react';
import Link from 'next/link';
import { CheckCircle, Download, ArrowRight } from 'lucide-react';
import { ProcessingHistory, ColumnInfo } from '@/types/preprocessing';
import { theme } from '@/styles/theme';
import * as api from '@/lib/api';

interface SummaryProps {
    history: ProcessingHistory[];
    columns: ColumnInfo[];
    originalColumnCount: number;
}

export function Summary({ history, columns, originalColumnCount }: SummaryProps) {
    const [isDownloading, setIsDownloading] = useState(false);
    const [downloadError, setDownloadError] = useState<string | null>(null);

    const stepCounts = history.reduce((acc, item) => {
        acc[item.stepKey] = (acc[item.stepKey] || 0) + 1;
        return acc;
    }, {} as Record<string, number>);

    const stepLabels: Record<string, string> = {
        missing_values: 'Missing Values',
        outliers: 'Outliers',
        feature_engineering: 'Feature Engineering',
        encoding: 'Encoding',
        scaling: 'Scaling',
    };
    const orderedStepKeys = ['missing_values', 'outliers', 'feature_engineering', 'encoding', 'scaling'];
    const appliedStepKeys = orderedStepKeys.filter((stepKey) => stepCounts[stepKey]);

    const newColumnsCount = columns.length - originalColumnCount;
    const totalAffectedRows = history.reduce((sum, h) => sum + (h.affectedRows || 0), 0);

    const handleDownload = async () => {
        try {
            setIsDownloading(true);
            setDownloadError(null);
            await api.downloadProcessedData();
        } catch (err) {
            setDownloadError(err instanceof Error ? err.message : 'Islenmis veri indirilemedi');
        } finally {
            setIsDownloading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div
                className="rounded-xl border p-6 text-center"
                style={{
                    borderColor: `${theme.colors.status.success}50`,
                    background: `${theme.colors.status.success}10`,
                }}
            >
                <CheckCircle
                    className="mx-auto mb-4 h-16 w-16"
                    style={{ color: theme.colors.status.success }}
                />
                <h2 className="mb-2 text-2xl font-bold text-white">On Isleme Tamamlandi</h2>
                <p className="text-gray-400">Verileriniz basariyla islendi ve model egitimine hazir.</p>
            </div>

            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                <StatCard
                    label="Toplam Islem"
                    value={history.length.toString()}
                    color={theme.colors.primary.cyan}
                />
                <StatCard
                    label="Etkilenen Satir"
                    value={totalAffectedRows.toLocaleString('tr-TR')}
                    color={theme.colors.secondary.green}
                />
                <StatCard
                    label="Mevcut Sutun"
                    value={columns.length.toString()}
                    color={theme.colors.accent.purple}
                />
                <StatCard
                    label="Yeni Sutun"
                    value={newColumnsCount > 0 ? `+${newColumnsCount}` : '0'}
                    color={theme.colors.status.warning}
                />
            </div>

            <div className="overflow-hidden rounded-xl border border-white/10">
                <div className="border-b border-white/10 bg-white/5 px-4 py-3">
                    <h3 className="font-medium text-white">Uygulanan Adimlar</h3>
                </div>
                <div className="divide-y divide-white/5">
                    {appliedStepKeys.map((stepKey) => (
                        <div key={stepKey} className="flex items-center justify-between px-4 py-3">
                            <span className="text-gray-300">{stepLabels[stepKey] || stepKey}</span>
                            <span className="rounded-full bg-cyan-500/20 px-2 py-1 text-xs text-cyan-400">
                                {stepCounts[stepKey]} islem
                            </span>
                        </div>
                    ))}
                    {appliedStepKeys.length === 0 && (
                        <div className="px-4 py-6 text-center text-gray-500">Henuz islem yapilmadi</div>
                    )}
                </div>
            </div>

            <div className="flex flex-col gap-4 sm:flex-row">
                <button
                    onClick={() => void handleDownload()}
                    disabled={isDownloading}
                    className="flex flex-1 cursor-pointer items-center justify-center gap-2 rounded-xl border border-white/20 px-6 py-3 text-white transition-all hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-50"
                >
                    <Download className="h-5 w-5" />
                    {isDownloading ? 'Indiriliyor...' : 'Islenmis Veriyi Indir'}
                </button>
                <Link
                    href="/model"
                    className="flex flex-1 items-center justify-center gap-2 rounded-xl px-6 py-3 font-medium text-white transition-all hover:scale-105"
                    style={{
                        background: theme.gradients.primary,
                        boxShadow: theme.glow.cyan,
                    }}
                >
                    Model Egitimine Gec
                    <ArrowRight className="h-5 w-5" />
                </Link>
            </div>

            {downloadError && <p className="text-sm text-red-400">{downloadError}</p>}
        </div>
    );
}

function StatCard({ label, value, color }: { label: string; value: string; color: string }) {
    return (
        <div
            className="rounded-xl border border-white/10 p-4"
            style={{
                background: `linear-gradient(135deg, ${color}10 0%, transparent 100%)`,
            }}
        >
            <p className="mb-1 text-sm text-gray-400">{label}</p>
            <p className="text-2xl font-bold" style={{ color }}>
                {value}
            </p>
        </div>
    );
}
