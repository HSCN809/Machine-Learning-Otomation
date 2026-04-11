'use client';

import { useEffect, useMemo, useState } from 'react';
import { MethodSelector } from '../MethodSelector';
import { ColumnSelector } from '../ColumnSelector';
import { ColumnInfo, OutlierConfig, OutlierMethod } from '@/types/preprocessing';
import { Loader2 } from 'lucide-react';
import { theme } from '@/styles/theme';
import { analyzeOutliers, isSessionRequiredError } from '@/lib/api';

interface OutliersProps {
    numericColumns: ColumnInfo[];
    onApply: (config: OutlierConfig) => Promise<void>;
    isLoading: boolean;
}

const METHODS = [
    { value: 'iqr_cap', label: 'IQR - Sınırla', icon: '📦', description: 'IQR yöntemi ile aykırı değerleri sınırla' },
    { value: 'zscore_cap', label: 'Z-Score - Sınırla', icon: '📊', description: 'Z-Score ile aykırı değerleri sınırla' },
    { value: 'isolation_forest', label: 'Isolation Forest', icon: '🌲', description: 'ML tabanlı aykırı değer tespiti' },
    { value: 'lof', label: 'LOF', icon: '🎯', description: 'Local Outlier Factor algoritması' },
];

export function Outliers({ numericColumns, onApply, isLoading }: OutliersProps) {
    const [method, setMethod] = useState<OutlierMethod>('iqr_cap');
    const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
    const [threshold, setThreshold] = useState<string>('1.5');
    const [detectedColumns, setDetectedColumns] = useState<ColumnInfo[]>([]);
    const [analysisSummary, setAnalysisSummary] = useState<{
        totalRows: number;
        outlierRowCount: number;
        outlierRowPercentage: number;
    } | null>(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [analysisError, setAnalysisError] = useState<string | null>(null);

    const numericColumnsByName = useMemo(
        () => new Map(numericColumns.map((column) => [column.name, column])),
        [numericColumns]
    );

    useEffect(() => {
        const run = async () => {
            if (numericColumns.length === 0) {
                setDetectedColumns([]);
                setSelectedColumns([]);
                setAnalysisSummary(null);
                return;
            }

            try {
                setIsAnalyzing(true);
                setAnalysisError(null);

                const thresholdValue = method.startsWith('iqr') || method.startsWith('zscore')
                    ? parseFloat(threshold) || undefined
                    : undefined;

                const result = await analyzeOutliers(
                    method,
                    numericColumns.map((column) => column.name),
                    thresholdValue
                );
                setAnalysisSummary({
                    totalRows: result.total_rows,
                    outlierRowCount: result.outlier_row_count,
                    outlierRowPercentage: result.outlier_row_percentage,
                });

                const nextDetected: ColumnInfo[] = [];
                for (const item of result.columns) {
                    const baseColumn = numericColumnsByName.get(item.column);
                    if (!baseColumn) {
                        continue;
                    }

                    nextDetected.push({
                        ...baseColumn,
                        outlierCount: item.outlier_count,
                        outlierPercentage: item.outlier_percentage,
                    });
                }

                const detectedNames = new Set(nextDetected.map((column) => column.name));
                setDetectedColumns(nextDetected);
                setSelectedColumns((previous: string[]) => {
                    const stillValid = previous.filter((columnName) => detectedNames.has(columnName));
                    return stillValid;
                });
            } catch (err) {
                if (isSessionRequiredError(err)) {
                    setDetectedColumns([]);
                    setSelectedColumns([]);
                    setAnalysisSummary(null);
                    setAnalysisError(null);
                    return;
                }

                console.error('Outlier analysis error:', err);
                setDetectedColumns([]);
                setSelectedColumns([]);
                setAnalysisSummary(null);
                setAnalysisError(err instanceof Error ? err.message : 'Aykırı değer analizi sırasında hata oluştu');
            } finally {
                setIsAnalyzing(false);
            }
        };

        void run();
    }, [method, threshold, numericColumns, numericColumnsByName]);

    const isRowBasedMethod = method === 'isolation_forest' || method === 'lof';

    const handleApply = async () => {
        const columnsToApply = isRowBasedMethod
            ? numericColumns.map((column) => column.name)
            : selectedColumns;
        if (columnsToApply.length === 0) return;

        const parsedThreshold = method.startsWith('iqr') || method.startsWith('zscore')
            ? parseFloat(threshold) || undefined
            : undefined;

        await onApply({
            method,
            columns: columnsToApply,
            threshold: parsedThreshold,
        });

        setSelectedColumns([]);
    };

    const canApply = isRowBasedMethod
        ? detectedColumns.length > 0 && !isAnalyzing
        : selectedColumns.length > 0 && !isAnalyzing;
    const showThreshold = method.startsWith('iqr') || method.startsWith('zscore');
    const showNoOutlierCard = !analysisError && !isAnalyzing && detectedColumns.length === 0;

    const handleMethodChange = (value: string) => {
        const nextMethod = value as OutlierMethod;
        setSelectedColumns([]);
        setMethod(nextMethod);

        if (nextMethod.startsWith('iqr')) {
            setThreshold('1.5');
        } else if (nextMethod.startsWith('zscore')) {
            setThreshold('3');
        }
    };

    return (
        <div className="space-y-6">

            {/* Method selector */}
            <MethodSelector
                label="Aykırı Değer Yöntemi"
                options={METHODS}
                value={method}
                onChange={handleMethodChange}
                disabled={isLoading || isAnalyzing}
            />

            {/* Threshold input */}
            {showThreshold && (
                <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-300">
                        Eşik Değeri {method.startsWith('iqr') ? '(IQR çarpanı)' : '(σ sayısı)'}
                    </label>
                    <input
                        type="number"
                        value={threshold}
                        onChange={(e) => setThreshold(e.target.value)}
                        step="0.1"
                        min="0.5"
                        max="5"
                        disabled={isLoading || isAnalyzing}
                        className="w-full px-4 py-2 rounded-lg border border-white/10 bg-white/5 text-white placeholder:text-gray-500 outline-none focus:border-cyan-500/50"
                    />
                    <p className="text-xs text-gray-500">
                        {method.startsWith('iqr')
                            ? 'Varsayılan: 1.5 (standart IQR kuralı)'
                            : 'Varsayılan: 3 (3 sigma kuralı)'
                        }
                    </p>
                </div>
            )}

            {!isRowBasedMethod && !showNoOutlierCard && (
                <ColumnSelector
                    columns={detectedColumns}
                    selectedColumns={selectedColumns}
                    onChange={setSelectedColumns}
                    label="Uygulanacak Sayısal Sütunlar"
                    showMissing={false}
                    showOutliers
                    disabled={isLoading || isAnalyzing}
                />
            )}
            {!analysisError && !isAnalyzing && isRowBasedMethod && analysisSummary && !showNoOutlierCard && (
                <div
                    className="rounded-xl border p-4"
                    style={{
                        borderColor: 'rgba(34, 211, 238, 0.35)',
                        background: 'rgba(6, 182, 212, 0.08)',
                    }}
                >
                    <p className="text-sm font-medium text-cyan-300">Global anomalik satır oranı</p>
                    <p className="mt-1 text-base text-cyan-200">
                        %{analysisSummary.outlierRowPercentage.toFixed(2)} ({analysisSummary.outlierRowCount}/{analysisSummary.totalRows})
                    </p>
                </div>
            )}

            {analysisError && (
                <p className="text-xs text-red-400">{analysisError}</p>
            )}
            {!analysisError && isAnalyzing && (
                <p className="text-xs text-cyan-300">Yönteme göre aykırı sütunlar analiz ediliyor...</p>
            )}
            {!analysisError && !isAnalyzing && detectedColumns.length === 0 && false && (
                <p className="text-xs text-gray-400">Seçilen yöntemde aykırı değer tespit edilen sütun bulunamadı.</p>
            )}

            {showNoOutlierCard && (
                <div
                    className="rounded-xl border p-4"
                    style={{
                        borderColor: 'rgba(148, 163, 184, 0.35)',
                        background: 'rgba(148, 163, 184, 0.08)',
                    }}
                >
                    <p className="text-sm font-medium text-gray-200">Bilgi</p>
                    <p className="mt-1 text-sm text-gray-300">Secilen yontemde aykiri deger tespit edilmedi.</p>
                </div>
            )}

            {/* Apply button */}
            <button
                onClick={handleApply}
                disabled={!canApply || isLoading || isAnalyzing}
                className={`w-full flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-medium text-white transition-all duration-200 ${
                    !canApply || isLoading || isAnalyzing ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'
                }`}
                style={{
                    background: canApply && !isLoading && !isAnalyzing ? theme.gradients.primary : 'rgba(255,255,255,0.1)',
                    boxShadow: canApply && !isLoading && !isAnalyzing ? theme.glow.cyan : undefined,
                }}
            >
                {isLoading || isAnalyzing ? (
                    <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        İşleniyor...
                    </>
                ) : (
                    <>Uygula</>
                )}
            </button>
        </div>
    );
}
