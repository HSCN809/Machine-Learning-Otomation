'use client';

import { Medal, Trophy } from 'lucide-react';
import { TrainingResult, ProblemType } from '@/types/model-selection';
import { theme } from '@/styles/theme';

interface ModelComparisonProps {
    results: TrainingResult[];
    problemType: ProblemType;
}

export function ModelComparison({ results, problemType }: ModelComparisonProps) {
    if (results.length === 0) {
        return (
            <div className="rounded-xl border border-white/10 bg-white/5 p-6 text-center">
                <p className="text-gray-400">Henüz sonuç yok</p>
            </div>
        );
    }

    const primaryMetric = problemType === 'classification' ? 'accuracy' : 'r2';
    const sortedResults = [...results].sort((a, b) => {
        const aVal = (a.metrics as Record<string, number | undefined>)[primaryMetric] ?? 0;
        const bVal = (b.metrics as Record<string, number | undefined>)[primaryMetric] ?? 0;
        return bVal - aVal;
    });

    const formatValue = (value?: number, isPercent = true) => {
        if (value === undefined) return '-';
        return isPercent ? `${(value * 100).toFixed(1)}%` : value.toFixed(4);
    };

    const classificationHeaders = ['Model', 'Doğruluk', 'Kesinlik', 'Duyarlılık', 'F1', 'AUC', 'Süre'];
    const regressionHeaders = ['Model', 'R²', 'MSE', 'RMSE', 'MAE', 'Süre'];
    const headers = problemType === 'classification' ? classificationHeaders : regressionHeaders;

    return (
        <div className="overflow-hidden rounded-xl border border-white/10">
            <div className="border-b border-white/10 bg-white/5 px-4 py-3">
                <h3 className="flex items-center gap-2 font-semibold text-white">
                    <Trophy className="h-5 w-5 text-yellow-400" />
                    Model Karşılaştırması
                </h3>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b border-white/10 bg-white/5">
                            {headers.map((header) => (
                                <th key={header} className="px-4 py-3 text-left font-medium text-gray-400">
                                    {header}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {sortedResults.map((result, index) => (
                            <tr
                                key={result.modelId}
                                className="border-b border-white/5 transition-colors hover:bg-white/5"
                            >
                                <td className="px-4 py-3">
                                    <div className="flex items-center gap-2">
                                        {index === 0 && <Trophy className="h-4 w-4 text-yellow-400" />}
                                        {index === 1 && <Medal className="h-4 w-4 text-gray-300" />}
                                        {index === 2 && <Medal className="h-4 w-4 text-orange-400" />}
                                        <span className={index === 0 ? 'font-semibold text-cyan-400' : 'text-white'}>
                                            {result.modelName}
                                        </span>
                                    </div>
                                </td>

                                {problemType === 'classification' ? (
                                    <>
                                        <td className="px-4 py-3 font-medium text-white">
                                            {formatValue(result.metrics.accuracy)}
                                        </td>
                                        <td className="px-4 py-3 text-gray-300">
                                            {formatValue(result.metrics.precision)}
                                        </td>
                                        <td className="px-4 py-3 text-gray-300">
                                            {formatValue(result.metrics.recall)}
                                        </td>
                                        <td className="px-4 py-3 text-gray-300">
                                            {formatValue(result.metrics.f1Score)}
                                        </td>
                                        <td className="px-4 py-3 text-gray-300">
                                            {formatValue(result.metrics.auc)}
                                        </td>
                                    </>
                                ) : (
                                    <>
                                        <td className="px-4 py-3 font-medium text-white">
                                            {formatValue(result.metrics.r2, false)}
                                        </td>
                                        <td className="px-4 py-3 text-gray-300">
                                            {formatValue(result.metrics.mse, false)}
                                        </td>
                                        <td className="px-4 py-3 text-gray-300">
                                            {formatValue(result.metrics.rmse, false)}
                                        </td>
                                        <td className="px-4 py-3 text-gray-300">
                                            {formatValue(result.metrics.mae, false)}
                                        </td>
                                    </>
                                )}

                                <td className="px-4 py-3 text-gray-400">{result.trainingTime.toFixed(2)} sn</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {sortedResults.length > 0 && (
                <div
                    className="border-t p-4"
                    style={{
                        borderColor: `${theme.colors.secondary.green}30`,
                        background: `${theme.colors.secondary.green}10`,
                    }}
                >
                    <p className="flex items-center gap-2 text-green-400">
                        <Trophy className="h-5 w-5" />
                        <span className="font-semibold">{sortedResults[0].modelName}</span>
                        <span className="text-gray-400">
                            en yüksek {primaryMetric === 'accuracy' ? 'doğruluk' : 'R²'} ile birinci
                        </span>
                    </p>
                </div>
            )}
        </div>
    );
}
