'use client';

import { useEffect, useMemo, useState } from 'react';
import { MethodSelector } from '../MethodSelector';
import { ColumnSelector } from '../ColumnSelector';
import { ColumnInfo, OutlierConfig, OutlierMethod } from '@/types/preprocessing';
import { Info, Loader2, X } from 'lucide-react';
import { theme } from '@/styles/theme';
import { analyzeOutliers, isSessionRequiredError } from '@/lib/api';

interface OutliersProps {
    numericColumns: ColumnInfo[];
    onApply: (config: OutlierConfig) => Promise<void>;
    isLoading: boolean;
}

const METHODS = [
    { value: 'iqr_cap', label: 'IQR - Cap', icon: '📦', description: 'IQR sınırlarının dışındaki değerleri doğrudan IQR sınırına çek' },
    { value: 'iqr_winsorize', label: 'IQR - Winsorize', icon: '📉', description: 'IQR ile aykırıyı tespit et, seçilen yüzdelik sınıra çek' },
];

const METHOD_DETAILS_MARKDOWN: Record<OutlierMethod, string> = {
    iqr_cap:
        '**Ne yapar?** IQR sınırlarının dışındaki değerleri doğrudan alt/üst IQR sınırına çeker.\n\n**Ne zaman uygundur?** Uç değerleri silmeden hızlı ve stabil biçimde sınırlamak istediğinizde tercih edilir.',
    iqr_winsorize:
        '**Ne yapar?** IQR ile aykırıları belirler, ardından seçilen kuyruk yüzdesine karşılık gelen quantile sınırlarına çeker.\n\n**Ne zaman uygundur?** Aykırı tespiti ile sıkıştırma seviyesini ayrı kontrol etmek istediğinizde daha esnek sonuç verir.',
};

type InfoKey = 'threshold' | 'winsorize';

const INFO_CONTENT: Record<InfoKey, { title: string; details: string }> = {
    threshold: {
        title: 'Eşik Değeri (IQR çarpanı)',
        details:
            '**Ne yapar?** IQR çarpanı, aykırı sınırlarını `Q1 - k×IQR` ve `Q3 + k×IQR` formülüyle belirler.\n\n**Nasıl etkiler?** Çarpan arttıkça sınırlar genişler ve daha az kayıt aykırı kabul edilir.',
    },
    winsorize: {
        title: 'Winsorize Yüzdesi',
        details:
            '**Ne yapar?** Bu yüzde, alt ve üst kuyrukta ayrı ayrı kaç verinin winsorize sınırına çekileceğini belirler.\n\n**Örnek:** `%5` seçildiğinde alt `%5` ve üst `%5` değerler sınır quantile değerlerine çekilir.',
    },
};

function renderInlineMarkdown(text: string) {
    const parts = text.split(/(\*\*.*?\*\*)/g);

    return parts.map((part, index) => {
        if (part.startsWith('**') && part.endsWith('**')) {
            return (
                <strong key={`${part}-${index}`} className="font-semibold text-white">
                    {part.slice(2, -2)}
                </strong>
            );
        }

        return <span key={`${part}-${index}`}>{part}</span>;
    });
}

function renderMarkdown(content: string) {
    return content.split(/\n\s*\n/).map((paragraph, index) => (
        <p key={`${paragraph}-${index}`} className="text-sm leading-6 text-gray-300">
            {renderInlineMarkdown(paragraph)}
        </p>
    ));
}

export function Outliers({ numericColumns, onApply, isLoading }: OutliersProps) {
    const [method, setMethod] = useState<OutlierMethod>('iqr_cap');
    const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
    const [threshold, setThreshold] = useState<string>('1.5');
    const [winsorizePercent, setWinsorizePercent] = useState<string>('5');
    const [detectedColumns, setDetectedColumns] = useState<ColumnInfo[]>([]);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [analysisError, setAnalysisError] = useState<string | null>(null);
    const [activeInfo, setActiveInfo] = useState<InfoKey | null>(null);

    const numericColumnsByName = useMemo(
        () => new Map(numericColumns.map((column) => [column.name, column])),
        [numericColumns]
    );

    useEffect(() => {
        const run = async () => {
            if (numericColumns.length === 0) {
                setDetectedColumns([]);
                setSelectedColumns([]);
                return;
            }

            try {
                setIsAnalyzing(true);
                setAnalysisError(null);

                const thresholdValue = parseFloat(threshold) || undefined;

                const winsorizePercentValue =
                    method === 'iqr_winsorize' ? parseFloat(winsorizePercent) || undefined : undefined;

                const result = await analyzeOutliers(method, numericColumns.map((column) => column.name), thresholdValue, winsorizePercentValue);

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
                    setAnalysisError(null);
                    return;
                }

                console.error('Outlier analysis error:', err);
                setDetectedColumns([]);
                setSelectedColumns([]);
                setAnalysisError(err instanceof Error ? err.message : 'Aykırı değer analizi sırasında hata oluştu');
            } finally {
                setIsAnalyzing(false);
            }
        };

        void run();
    }, [method, threshold, winsorizePercent, numericColumns, numericColumnsByName]);

    const handleApply = async () => {
        const columnsToApply = selectedColumns;
        if (columnsToApply.length === 0) return;

        const parsedThreshold = parseFloat(threshold) || undefined;
        const parsedWinsorizePercent =
            method === 'iqr_winsorize' ? parseFloat(winsorizePercent) || undefined : undefined;

        await onApply({
            method,
            columns: columnsToApply,
            threshold: parsedThreshold,
            winsorizePercent: parsedWinsorizePercent,
        });

        setSelectedColumns([]);
    };

    const canApply = selectedColumns.length > 0 && !isAnalyzing;
    const showThreshold = method.startsWith('iqr');
    const showWinsorizePercent = method === 'iqr_winsorize';
    const showNoOutlierCard = !analysisError && !isAnalyzing && detectedColumns.length === 0;

    const handleMethodChange = (value: string) => {
        const nextMethod = value as OutlierMethod;
        setSelectedColumns([]);
        setMethod(nextMethod);

        if (nextMethod.startsWith('iqr')) {
            setThreshold('1.5');
        }
        if (nextMethod === 'iqr_winsorize') {
            setWinsorizePercent('5');
        }
    };

    return (
        <div className="space-y-6">

            {/* Method selector */}
            <MethodSelector
                label="Aykırı Değer Yöntemi"
                options={METHODS.map((option) => ({
                    ...option,
                    details: METHOD_DETAILS_MARKDOWN[option.value as OutlierMethod],
                }))}
                value={method}
                onChange={handleMethodChange}
                disabled={isLoading || isAnalyzing}
            />

            {/* Threshold input */}
            {showThreshold && (
                <div className="space-y-4">
                    <label className="text-sm font-medium text-gray-300">
                        <span className="flex items-center gap-2">
                            Eşik Değeri (IQR çarpanı)
                            <div className="group relative flex items-center">
                                <button
                                    type="button"
                                    aria-label="Eşik değeri hakkında bilgi"
                                    onClick={() => setActiveInfo('threshold')}
                                    className="flex h-5 w-5 cursor-pointer items-center justify-center rounded-full border border-cyan-400/20 bg-cyan-400/10 text-cyan-300 transition-all duration-200 hover:border-cyan-400/40 hover:bg-cyan-400/15 hover:text-cyan-200"
                                >
                                    <Info className="h-3 w-3" />
                                </button>
                                <span className="pointer-events-none absolute bottom-full left-1/2 z-10 mb-2 -translate-x-1/2 whitespace-nowrap rounded-full border border-cyan-400/20 bg-slate-950/95 px-3 py-1 text-[11px] font-medium text-cyan-200 opacity-0 shadow-lg shadow-cyan-500/10 transition-all duration-200 group-hover:opacity-100">
                                    Bilgi almak için tıklayın
                                </span>
                            </div>
                        </span>
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
                </div>
            )}

            {showWinsorizePercent && (
                <div className="space-y-4">
                    <label className="text-sm font-medium text-gray-300">
                        <span className="flex items-center gap-2">
                            Winsorize Yüzdesi (iki kuyruk, %)
                            <div className="group relative flex items-center">
                                <button
                                    type="button"
                                    aria-label="Winsorize yüzdesi hakkında bilgi"
                                    onClick={() => setActiveInfo('winsorize')}
                                    className="flex h-5 w-5 cursor-pointer items-center justify-center rounded-full border border-cyan-400/20 bg-cyan-400/10 text-cyan-300 transition-all duration-200 hover:border-cyan-400/40 hover:bg-cyan-400/15 hover:text-cyan-200"
                                >
                                    <Info className="h-3 w-3" />
                                </button>
                                <span className="pointer-events-none absolute bottom-full left-1/2 z-10 mb-2 -translate-x-1/2 whitespace-nowrap rounded-full border border-cyan-400/20 bg-slate-950/95 px-3 py-1 text-[11px] font-medium text-cyan-200 opacity-0 shadow-lg shadow-cyan-500/10 transition-all duration-200 group-hover:opacity-100">
                                    Bilgi almak için tıklayın
                                </span>
                            </div>
                        </span>
                    </label>
                    <input
                        type="range"
                        min="1"
                        max="20"
                        step="1"
                        value={winsorizePercent}
                        onChange={(e) => setWinsorizePercent(e.target.value)}
                        disabled={isLoading || isAnalyzing}
                        className="h-2 w-full cursor-pointer accent-cyan-400"
                    />
                    <p className="text-sm font-medium text-cyan-300">
                        %{winsorizePercent} / kuyruk
                    </p>
                </div>
            )}

            {!showNoOutlierCard && (
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
                    <p className="mt-1 text-sm text-gray-300">Seçilen yöntemde aykırı değer tespit edilmedi.</p>
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

            {activeInfo && (
                <div
                    className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 px-4 backdrop-blur-sm"
                    onClick={() => setActiveInfo(null)}
                >
                    <div
                        className="w-full max-w-md rounded-2xl border border-cyan-400/20 bg-[#0D1528]/95 p-6 shadow-2xl"
                        style={{ boxShadow: theme.glow.cyanStrong }}
                        onClick={(event) => event.stopPropagation()}
                    >
                        <div className="flex items-start justify-between gap-4">
                            <div className="flex items-start gap-3">
                                <div className="mt-0.5 flex h-10 w-10 items-center justify-center rounded-xl border border-cyan-400/20 bg-cyan-400/10 text-cyan-300">
                                    <Info className="h-5 w-5" />
                                </div>
                                <div>
                                    <p className="text-xs font-medium uppercase tracking-[0.2em] text-cyan-400/80">
                                        Alan Bilgisi
                                    </p>
                                    <h3 className="mt-1 text-lg font-semibold text-white">
                                        {INFO_CONTENT[activeInfo].title}
                                    </h3>
                                </div>
                            </div>
                            <button
                                type="button"
                                onClick={() => setActiveInfo(null)}
                                className="flex h-9 w-9 cursor-pointer items-center justify-center rounded-full border border-white/10 bg-white/5 text-gray-300 transition-colors hover:bg-white/10 hover:text-white"
                                aria-label="Bilgi penceresini kapat"
                            >
                                <X className="h-4 w-4" />
                            </button>
                        </div>

                        <div className="mt-5 space-y-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                            {renderMarkdown(INFO_CONTENT[activeInfo].details)}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
