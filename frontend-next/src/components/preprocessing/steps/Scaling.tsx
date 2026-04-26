'use client';

import { useEffect, useState } from 'react';
import { MethodSelector } from '../MethodSelector';
import { ColumnSelector } from '../ColumnSelector';
import { ColumnInfo, ScalingConfig, ScalingMethod } from '@/types/preprocessing';
import { Loader2 } from 'lucide-react';
import { theme } from '@/styles/theme';
import { analyzeOutliers, getNumericStats, isSessionRequiredError, NumericStat } from '@/lib/api';
import { logger } from '@/lib/logger';

interface ScalingProps {
    numericColumns: ColumnInfo[];
    onApply: (config: ScalingConfig) => Promise<void>;
    isLoading: boolean;
}

const METHODS = [
    { value: 'standard', label: 'Standard Scaler', icon: '📐', description: 'Ortalama 0, std 1 olacak şekilde' },
    { value: 'minmax', label: 'MinMax Scaler', icon: '📏', description: '0-1 aralığına dönüştür' },
    { value: 'robust', label: 'Robust Scaler', icon: '🛡️', description: 'Aykırı değerlere dayanıklı' },
    { value: 'maxabs', label: 'MaxAbs Scaler', icon: '📊', description: '-1 ile 1 arasına ölçekle' },
    { value: 'normalizer', label: 'Normalizer', icon: '🔄', description: 'Birim norm\'a normalize et' },
];

const METHOD_DETAILS_MARKDOWN: Record<ScalingMethod, string> = {
    standard:
        '**Ne yapar?** Her sütunu ortalaması 0 ve standart sapması 1 olacak şekilde dönüştürür.\n\n**Ne zaman uygundur?** Özellikle uzaklık/gradient tabanlı modellerde ölçek farkını azaltmak için kullanılır.',
    minmax:
        '**Ne yapar?** Değerleri belirlenen aralığa (genelde 0-1) lineer olarak taşır.\n\n**Ne zaman uygundur?** Özelliklerin aynı bantta olmasının önemli olduğu modellerde pratik bir tercihtir.',
    robust:
        '**Ne yapar?** Medyan ve IQR kullanarak ölçekler, uç değerlere daha az duyarlıdır.\n\n**Ne zaman uygundur?** Aykırı değerlerin yoğun olduğu veri setlerinde daha stabil sonuç verir.',
    maxabs:
        '**Ne yapar?** Her sütunu mutlak maksimum değerine bölerek aralığı yaklaşık -1 ile 1’e getirir.\n\n**Ne zaman uygundur?** Seyrek veri yapısını bozmadan ölçekleme gerektiğinde tercih edilir.',
    normalizer:
        '**Ne yapar?** Her satırı seçilen norma göre birim vektöre dönüştürür.\n\n**Ne zaman uygundur?** Yön bilgisinin büyüklükten daha önemli olduğu metin/vektör benzerliği problemlerinde faydalıdır.',
};

import React from 'react';

function formatPercentage(value: number): string {
    const normalized = Math.max(0, value);
    return normalized % 1 === 0 ? normalized.toFixed(0) : normalized.toFixed(1);
}

function buildDistributionSummary(stat: NumericStat, outlierPercentage: number): string {
    const absoluteSkewness = Math.abs(stat.skewness);
    const iqr = Math.max(0, stat.q75 - stat.q25);
    const range = Math.max(0, stat.max - stat.min);
    const relativeSpread = range > 0 ? iqr / range : 0;

    if (range === 0 || iqr === 0 || stat.std === 0) {
        return 'Dar aralık, düşük varyasyon';
    }

    if (outlierPercentage >= 10) {
        return 'Geniş aralık, aykırı baskın';
    }

    if (relativeSpread <= 0.18) {
        return 'Dar aralık, düşük varyasyon';
    }

    if (absoluteSkewness >= 1) {
        return `${stat.skewness > 0 ? 'Sağa' : 'Sola'} çarpık, %${formatPercentage(outlierPercentage)} aykırı`;
    }

    if (absoluteSkewness >= 0.5) {
        return `${stat.skewness > 0 ? 'Hafif sağa' : 'Hafif sola'} çarpık, %${formatPercentage(outlierPercentage)} aykırı`;
    }

    if (outlierPercentage >= 3) {
        return `Dengeli dağılım, %${formatPercentage(outlierPercentage)} aykırı`;
    }

    return 'Dengeli dağılım, düşük aykırı';
}

export const Scaling = React.memo(function Scaling({ numericColumns, onApply, isLoading }: ScalingProps) {
    const [method, setMethod] = useState<ScalingMethod>('standard');
    const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
    const [enrichedColumns, setEnrichedColumns] = useState<ColumnInfo[]>(numericColumns);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [analysisError, setAnalysisError] = useState<string | null>(null);

    useEffect(() => {
        let isCancelled = false;

        const run = async () => {
            setSelectedColumns((previous) =>
                previous.filter((columnName) => numericColumns.some((column) => column.name === columnName))
            );

            if (numericColumns.length === 0) {
                setEnrichedColumns([]);
                setAnalysisError(null);
                return;
            }

            setEnrichedColumns(numericColumns);

            try {
                setIsAnalyzing(true);
                setAnalysisError(null);

                const [numericStatsResponse, outlierAnalysisResponse] = await Promise.all([
                    getNumericStats(),
                    analyzeOutliers('iqr_cap', numericColumns.map((column) => column.name), 1.5),
                ]);

                if (isCancelled) {
                    return;
                }

                const statsByColumn = new Map(
                    numericStatsResponse.stats.map((stat) => [stat.column, stat] as const)
                );
                const outliersByColumn = new Map(
                    outlierAnalysisResponse.columns.map((item) => [item.column, item] as const)
                );

                setEnrichedColumns(
                    numericColumns.map((column) => {
                        const stat = statsByColumn.get(column.name);
                        const outlier = outliersByColumn.get(column.name);

                        if (!stat) {
                            return column;
                        }

                        return {
                            ...column,
                            outlierCount: outlier?.outlier_count ?? column.outlierCount,
                            outlierPercentage: outlier?.outlier_percentage ?? column.outlierPercentage,
                            distributionSummary: buildDistributionSummary(
                                stat,
                                outlier?.outlier_percentage ?? 0
                            ),
                        };
                    })
                );
            } catch (err) {
                if (isCancelled) {
                    return;
                }

                if (isSessionRequiredError(err)) {
                    setEnrichedColumns([]);
                    setSelectedColumns([]);
                    setAnalysisError(null);
                    return;
                }

                logger.error('Scaling distribution analysis failed', err);
                setEnrichedColumns(numericColumns);
                setAnalysisError('Dağılım özeti alınamadı, sütunlar yine seçilebilir.');
            } finally {
                if (!isCancelled) {
                    setIsAnalyzing(false);
                }
            }
        };

        void run();

        return () => {
            isCancelled = true;
        };
    }, [numericColumns]);

    const handleApply = async () => {
        if (selectedColumns.length === 0) return;

        await onApply({
            method,
            columns: selectedColumns,
        });

        setSelectedColumns([]);
    };

    const canApply = selectedColumns.length > 0;

    return (
        <div className="space-y-6">

            {/* Method selector */}
            <MethodSelector
                label="Ölçeklendirme Yöntemi"
                options={METHODS.map((option) => ({
                    ...option,
                    details: METHOD_DETAILS_MARKDOWN[option.value as ScalingMethod],
                }))}
                value={method}
                onChange={(v) => setMethod(v as ScalingMethod)}
                disabled={isLoading}
            />

            {/* Column selector */}
            <ColumnSelector
                columns={enrichedColumns}
                selectedColumns={selectedColumns}
                onChange={setSelectedColumns}
                label="Uygulanacak Sayısal Sütunlar"
                showMissing={false}
                showSummary
                disabled={isLoading}
            />

            {analysisError && (
                <p className="text-xs text-red-400">{analysisError}</p>
            )}
            {!analysisError && isAnalyzing && (
                <p className="text-xs text-cyan-300">Sütun dağılımları analiz ediliyor...</p>
            )}

            {/* Apply button */}
            <button
                onClick={handleApply}
                disabled={!canApply || isLoading}
                className={`w-full flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-medium text-white transition-all duration-200 ${
                    !canApply || isLoading ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'
                }`}
                style={{
                    background: canApply && !isLoading ? theme.gradients.primary : 'rgba(255,255,255,0.1)',
                    boxShadow: canApply && !isLoading ? theme.glow.cyan : undefined,
                }}
            >
                {isLoading ? (
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
});
