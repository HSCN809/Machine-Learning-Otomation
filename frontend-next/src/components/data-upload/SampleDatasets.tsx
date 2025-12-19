'use client';

import { Database } from 'lucide-react';
import { cn } from '@/lib/utils';
import { theme } from '@/styles/theme';
import { SAMPLE_DATASETS } from '@/hooks/useDataUpload';

interface SampleDatasetsProps {
    onSelect: (datasetId: string) => void;
    disabled?: boolean;
    loading?: boolean;
}

export function SampleDatasets({ onSelect, disabled = false, loading = false }: SampleDatasetsProps) {
    return (
        <div className="space-y-4 max-w-4xl mx-auto">
            <div className="flex items-center justify-center gap-2">
                <Database className="w-5 h-5 text-cyan-400" />
                <h3 className="text-lg font-semibold text-white">Hazır Veri Setleri</h3>
            </div>

            <p className="text-sm text-gray-400 text-center">
                Hızlı test için hazır veri setlerinden birini seçebilirsiniz:
            </p>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {SAMPLE_DATASETS.map((dataset) => (
                    <button
                        key={dataset.id}
                        onClick={() => onSelect(dataset.id)}
                        disabled={disabled || loading}
                        className={cn(
                            'group relative p-4 rounded-xl border border-white/10 transition-all duration-300',
                            'hover:border-cyan-500/50 hover:bg-white/5',
                            'disabled:opacity-50 disabled:cursor-not-allowed',
                            'flex flex-col items-center text-center'
                        )}
                    >
                        {/* Hover glow */}
                        <div
                            className="absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
                            style={{
                                background: `radial-gradient(circle at center, ${theme.colors.primary.cyan}15 0%, transparent 70%)`,
                            }}
                        />

                        <span className="text-3xl mb-2">{dataset.emoji}</span>
                        <span className="font-medium text-white text-sm">{dataset.name}</span>
                        <span className="text-xs text-gray-500 mt-1">
                            {dataset.rows.toLocaleString('tr-TR')} satır
                        </span>
                    </button>
                ))}
            </div>
        </div>
    );
}
