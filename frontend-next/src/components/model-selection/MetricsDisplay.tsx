'use client';

import { ModelMetrics, ProblemType } from '@/types/model-selection';
import { theme } from '@/styles/theme';

interface MetricsDisplayProps {
    metrics: ModelMetrics;
    problemType: ProblemType;
}

export function MetricsDisplay({ metrics, problemType }: MetricsDisplayProps) {
    const formatPercent = (value?: number) =>
        value !== undefined ? `${(value * 100).toFixed(1)}%` : '-';

    const formatNumber = (value?: number, decimals = 4) =>
        value !== undefined ? value.toFixed(decimals) : '-';

    const classificationMetrics = [
        { label: 'Accuracy', value: formatPercent(metrics.accuracy), color: theme.colors.primary.cyan },
        { label: 'Precision', value: formatPercent(metrics.precision), color: theme.colors.secondary.green },
        { label: 'Recall', value: formatPercent(metrics.recall), color: theme.colors.accent.purple },
        { label: 'F1 Score', value: formatPercent(metrics.f1Score), color: theme.colors.status.warning },
        { label: 'AUC', value: formatPercent(metrics.auc), color: theme.colors.status.info },
    ];

    const regressionMetrics = [
        { label: 'R² Score', value: formatNumber(metrics.r2, 4), color: theme.colors.primary.cyan },
        { label: 'MSE', value: formatNumber(metrics.mse, 2), color: theme.colors.secondary.green },
        { label: 'RMSE', value: formatNumber(metrics.rmse, 2), color: theme.colors.accent.purple },
        { label: 'MAE', value: formatNumber(metrics.mae, 2), color: theme.colors.status.warning },
    ];

    const displayMetrics = problemType === 'classification' ? classificationMetrics : regressionMetrics;

    return (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
            {displayMetrics.map((metric) => (
                <div
                    key={metric.label}
                    className="p-4 rounded-xl border border-white/10"
                    style={{
                        background: `linear-gradient(135deg, ${metric.color}10 0%, transparent 100%)`,
                    }}
                >
                    <p className="text-xs text-gray-400 mb-1">{metric.label}</p>
                    <p className="text-xl font-bold" style={{ color: metric.color }}>
                        {metric.value}
                    </p>
                </div>
            ))}
        </div>
    );
}
