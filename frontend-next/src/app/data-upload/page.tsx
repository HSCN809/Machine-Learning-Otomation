'use client';

import { useState, useCallback } from 'react';
import { Sidebar, Header } from '@/components/layout';
import {
    FileDropzone,
    SampleDatasets,
    UploadProgress,
    ValidationReport,
    DataPreview,
} from '@/components/data-upload';
import { useDataUpload } from '@/hooks/useDataUpload';
import * as api from '@/lib/api';
import { RefreshCw } from 'lucide-react';
import { theme } from '@/styles/theme';
import { ValidationReport as ValidationReportType, ValidationIssue } from '@/types/data-upload';

export default function DataUploadPage() {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [isEnhancing, setIsEnhancing] = useState(false);
    const [hasLLMSuggestions, setHasLLMSuggestions] = useState(false);

    const {
        status,
        progress,
        error,
        uploadedFile,
        dataSummary,
        validationReport,
        setValidationReport,
        uploadFile,
        loadSampleDataset,
        reset,
    } = useDataUpload();

    const handleEnhanceWithLLM = useCallback(async () => {
        try {
            setIsEnhancing(true);
            const enhanced = await api.enhanceWithLLM();

            if (enhanced && enhanced.issues) {
                const issues: ValidationReportType['issuesBySeverity'] = {
                    critical: [],
                    warning: [],
                    info: [],
                };

                enhanced.issues.forEach((issue: api.ValidationIssue) => {
                    const validationIssue: ValidationIssue = {
                        id: issue.id,
                        severity: issue.severity,
                        type: issue.type as ValidationIssue['type'],
                        column: issue.column,
                        description: issue.description,
                        suggestion: issue.suggestion,
                        llmSuggestion: issue.llmSuggestion,
                        priority: issue.priority as ValidationIssue['priority'],
                    };

                    if (issue.severity === 'critical') {
                        issues.critical.push(validationIssue);
                    } else if (issue.severity === 'warning') {
                        issues.warning.push(validationIssue);
                    } else {
                        issues.info.push(validationIssue);
                    }
                });

                setValidationReport({
                    isValid: enhanced.is_valid,
                    totalIssues: enhanced.issues.length,
                    issuesBySeverity: issues,
                });
                setHasLLMSuggestions(true);
            }
        } catch (err) {
            console.error('LLM enhancement error:', err);
        } finally {
            setIsEnhancing(false);
        }
    }, [setValidationReport]);

    const handleReset = useCallback(async () => {
        await reset();
        setHasLLMSuggestions(false);
    }, [reset]);

    const handleResetLLMSuggestions = useCallback(() => {
        if (validationReport) {
            const resetIssues = (issues: ValidationIssue[]) =>
                issues.map((issue) => ({
                    ...issue,
                    llmSuggestion: undefined,
                    priority: undefined,
                }));

            setValidationReport({
                ...validationReport,
                issuesBySeverity: {
                    critical: resetIssues(validationReport.issuesBySeverity.critical),
                    warning: resetIssues(validationReport.issuesBySeverity.warning),
                    info: resetIssues(validationReport.issuesBySeverity.info),
                },
            });
        }

        setHasLLMSuggestions(false);
    }, [validationReport, setValidationReport]);

    const isLoading = status === 'uploading' || status === 'validating';
    const showResults = status === 'success' && dataSummary && validationReport;

    return (
        <div className="min-h-screen">
            <Sidebar
                isCollapsed={sidebarCollapsed}
                onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
            />

            <div
                className="transition-all duration-300"
                style={{
                    marginLeft: sidebarCollapsed ? '80px' : '288px',
                }}
            >
                <Header
                    title="Veri Yükleme"
                    subtitle="CSV veya Excel dosyalarınızı yükleyin ve otomatik doğrulama alın."
                />

                <main className="p-6 space-y-8">
                    <div className="flex justify-end">
                        <button
                            onClick={handleReset}
                            className="flex items-center gap-2 px-4 py-2 rounded-xl border border-white/10 text-gray-400 hover:text-white hover:bg-white/5 transition-all cursor-pointer"
                        >
                            <RefreshCw className="w-4 h-4" />
                            <span>Sıfırla</span>
                        </button>
                    </div>

                    {(status === 'idle' || status === 'error') && (
                        <>
                            <section
                                className="p-6 rounded-2xl border border-white/10"
                                style={{
                                    background:
                                        'linear-gradient(135deg, rgba(17, 24, 39, 0.6) 0%, rgba(31, 41, 55, 0.4) 100%)',
                                }}
                            >
                                <h2 className="text-lg font-semibold text-white mb-4">Dosya Yükle</h2>
                                <FileDropzone onFileSelect={uploadFile} disabled={isLoading} />
                            </section>

                            <div className="flex items-center gap-4">
                                <div className="flex-1 h-px bg-white/10" />
                                <span className="text-gray-500 text-sm">veya</span>
                                <div className="flex-1 h-px bg-white/10" />
                            </div>

                            <section
                                className="p-6 rounded-2xl border border-white/10"
                                style={{
                                    background:
                                        'linear-gradient(135deg, rgba(17, 24, 39, 0.6) 0%, rgba(31, 41, 55, 0.4) 100%)',
                                }}
                            >
                                <SampleDatasets
                                    onSelect={loadSampleDataset}
                                    disabled={isLoading}
                                    loading={isLoading}
                                />
                            </section>
                        </>
                    )}

                    {(status === 'uploading' || status === 'validating') && (
                        <UploadProgress
                            status={status}
                            progress={progress}
                            file={uploadedFile}
                            error={error}
                        />
                    )}

                    {showResults && (
                        <>
                            <div
                                className="p-4 rounded-xl border"
                                style={{
                                    borderColor: `${theme.colors.status.success}50`,
                                    background: `${theme.colors.status.success}10`,
                                }}
                            >
                                <p className="text-green-400 font-medium">
                                    Veri başarıyla yüklendi: {uploadedFile?.name || 'Hazır veri seti'}
                                </p>
                            </div>

                            <section
                                className="p-6 rounded-2xl border border-white/10"
                                style={{
                                    background:
                                        'linear-gradient(135deg, rgba(17, 24, 39, 0.6) 0%, rgba(31, 41, 55, 0.4) 100%)',
                                }}
                            >
                                <DataPreview summary={dataSummary} />
                            </section>

                            <section
                                className="p-6 rounded-2xl border border-white/10"
                                style={{
                                    background:
                                        'linear-gradient(135deg, rgba(17, 24, 39, 0.6) 0%, rgba(31, 41, 55, 0.4) 100%)',
                                }}
                            >
                                <ValidationReport
                                    report={validationReport}
                                    onEnhanceWithLLM={handleEnhanceWithLLM}
                                    onResetLLMSuggestions={handleResetLLMSuggestions}
                                    isEnhancing={isEnhancing}
                                    hasLLMSuggestions={hasLLMSuggestions}
                                />
                            </section>

                            <div
                                className="p-6 rounded-xl border border-cyan-500/20"
                                style={{
                                    background:
                                        'linear-gradient(135deg, rgba(0, 217, 255, 0.05) 0%, rgba(0, 255, 136, 0.05) 100%)',
                                }}
                            >
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h3 className="font-semibold text-white mb-1">Sonraki Adım</h3>
                                        <p className="text-sm text-gray-400">
                                            Verilerinizi analiz etmek için EDA modülüne geçin veya ön işleme yapın.
                                        </p>
                                    </div>
                                    <div className="flex gap-3">
                                        <a
                                            href="/eda"
                                            className="px-4 py-2 rounded-xl border border-white/20 text-white hover:bg-white/5 transition-all"
                                        >
                                            EDA
                                        </a>
                                        <a
                                            href="/preprocessing"
                                            className="px-4 py-2 rounded-xl font-medium text-white transition-all hover:scale-105"
                                            style={{
                                                background: theme.gradients.primary,
                                                boxShadow: theme.glow.cyan,
                                            }}
                                        >
                                            Ön İşleme
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </>
                    )}
                </main>
            </div>
        </div>
    );
}
