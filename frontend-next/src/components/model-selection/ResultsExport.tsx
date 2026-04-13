'use client';

import { useState } from 'react';
import { Download, FileJson, FileSpreadsheet, Package } from 'lucide-react';
import { TrainingResult } from '@/types/model-selection';
import { theme } from '@/styles/theme';
import * as api from '@/lib/api';

interface ResultsExportProps {
    results: TrainingResult[];
}

export function ResultsExport({ results }: ResultsExportProps) {
    const [downloadError, setDownloadError] = useState<string | null>(null);
    const [downloadingModelId, setDownloadingModelId] = useState<string | null>(null);

    const exportJSON = () => {
        const data = JSON.stringify(results, null, 2);
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = 'model_results.json';
        anchor.click();
        URL.revokeObjectURL(url);
    };

    const exportCSV = () => {
        const headers = ['Model', 'Accuracy', 'Precision', 'Recall', 'F1', 'AUC', 'R2', 'MSE', 'RMSE', 'MAE', 'Training Time'];
        const rows = results.map((result) => [
            result.modelName,
            result.metrics.accuracy ?? '',
            result.metrics.precision ?? '',
            result.metrics.recall ?? '',
            result.metrics.f1Score ?? '',
            result.metrics.auc ?? '',
            result.metrics.r2 ?? '',
            result.metrics.mse ?? '',
            result.metrics.rmse ?? '',
            result.metrics.mae ?? '',
            result.trainingTime,
        ]);

        const csv = [headers.join(','), ...rows.map((row) => row.join(','))].join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = 'model_results.csv';
        anchor.click();
        URL.revokeObjectURL(url);
    };

    const handleModelDownload = async (result: TrainingResult) => {
        try {
            setDownloadError(null);
            setDownloadingModelId(result.modelId);
            await api.downloadTrainedModel(result.modelId);
        } catch (err) {
            setDownloadError(err instanceof Error ? err.message : 'Model indirilemedi');
        } finally {
            setDownloadingModelId(null);
        }
    };

    const exportFormats = [
        { name: 'JSON', icon: FileJson, action: exportJSON, color: theme.colors.primary.cyan },
        { name: 'CSV', icon: FileSpreadsheet, action: exportCSV, color: theme.colors.secondary.green },
    ];

    return (
        <div className="rounded-xl border border-white/10 bg-white/5 p-6">
            <h4 className="mb-4 flex items-center gap-2 font-semibold text-white">
                <Download className="h-5 w-5" />
                Sonuclari Disa Aktar
            </h4>

            <div className="flex flex-wrap gap-3">
                {exportFormats.map((format) => {
                    const Icon = format.icon;
                    return (
                        <button
                            key={format.name}
                            onClick={format.action}
                            className="flex cursor-pointer items-center gap-2 rounded-xl border border-white/10 px-4 py-2 transition-colors hover:bg-white/10"
                        >
                            <Icon className="h-5 w-5" style={{ color: format.color }} />
                            <span className="text-white">{format.name}</span>
                        </button>
                    );
                })}
            </div>

            <div className="mt-6 space-y-3">
                <p className="text-sm font-medium text-gray-300">Egitilmis Modeller</p>
                <div className="grid gap-3 md:grid-cols-2">
                    {results.map((result) => (
                        <button
                            key={result.modelId}
                            onClick={() => void handleModelDownload(result)}
                            disabled={downloadingModelId !== null}
                            className="flex cursor-pointer items-center justify-between rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-left transition-colors hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            <div>
                                <p className="font-medium text-white">{result.modelName}</p>
                                <p className="text-xs text-gray-400">{result.modelId}.pkl</p>
                            </div>
                            <div className="flex items-center gap-2 text-cyan-300">
                                <Package className="h-4 w-4" />
                                <span className="text-sm">
                                    {downloadingModelId === result.modelId ? 'Indiriliyor...' : 'Modeli Indir'}
                                </span>
                            </div>
                        </button>
                    ))}
                </div>
            </div>

            {downloadError && <p className="mt-3 text-sm text-red-400">{downloadError}</p>}

            <p className="mt-3 text-xs text-gray-500">
                Sonuc raporlarini ve egitilmis modelleri farkli projelerde kullanmak icin indirebilirsiniz.
            </p>
        </div>
    );
}
