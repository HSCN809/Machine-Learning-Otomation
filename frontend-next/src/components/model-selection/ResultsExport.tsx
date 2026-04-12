'use client';

import { Download, FileJson, FileSpreadsheet } from 'lucide-react';
import { TrainingResult } from '@/types/model-selection';
import { theme } from '@/styles/theme';

interface ResultsExportProps {
    results: TrainingResult[];
}

export function ResultsExport({ results }: ResultsExportProps) {
    const exportJSON = () => {
        const data = JSON.stringify(results, null, 2);
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'model_results.json';
        a.click();
        URL.revokeObjectURL(url);
    };

    const exportCSV = () => {
        const headers = ['Model', 'Accuracy', 'Precision', 'Recall', 'F1', 'AUC', 'R2', 'MSE', 'RMSE', 'MAE', 'Training Time'];
        const rows = results.map(r => [
            r.modelName,
            r.metrics.accuracy ?? '',
            r.metrics.precision ?? '',
            r.metrics.recall ?? '',
            r.metrics.f1Score ?? '',
            r.metrics.auc ?? '',
            r.metrics.r2 ?? '',
            r.metrics.mse ?? '',
            r.metrics.rmse ?? '',
            r.metrics.mae ?? '',
            r.trainingTime,
        ]);

        const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'model_results.csv';
        a.click();
        URL.revokeObjectURL(url);
    };

    const exportFormats = [
        { name: 'JSON', icon: FileJson, action: exportJSON, color: theme.colors.primary.cyan },
        { name: 'CSV', icon: FileSpreadsheet, action: exportCSV, color: theme.colors.secondary.green },
    ];

    return (
        <div className="p-6 rounded-xl border border-white/10 bg-white/5">
            <h4 className="font-semibold text-white mb-4 flex items-center gap-2">
                <Download className="w-5 h-5" />
                Sonuçları Dışa Aktar
            </h4>

            <div className="flex flex-wrap gap-3">
                {exportFormats.map((format) => {
                    const Icon = format.icon;
                    return (
                        <button
                            key={format.name}
                            onClick={format.action}
                            className="flex cursor-pointer items-center gap-2 px-4 py-2 rounded-xl border border-white/10 hover:bg-white/10 transition-colors"
                        >
                            <Icon className="w-5 h-5" style={{ color: format.color }} />
                            <span className="text-white">{format.name}</span>
                        </button>
                    );
                })}
            </div>

            <p className="text-xs text-gray-500 mt-3">
                💡 Sonuçları farklı formatlarda indirerek raporlarda kullanabilirsiniz.
            </p>
        </div>
    );
}
