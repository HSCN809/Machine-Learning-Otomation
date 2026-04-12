'use client';

import { useState, useEffect, useRef } from 'react';
import { Sidebar, Header } from '@/components/layout';
import {
    FileDropzone,
    SampleDatasets,
    UploadProgress,
    ValidationReport,
    DataPreview,
} from '@/components/data-upload';
import { SessionPageSkeleton } from '@/components/common';
import { useDataUpload } from '@/hooks/useDataUpload';
import * as api from '@/lib/api';

export default function DataUploadPage() {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [isBootstrapping, setIsBootstrapping] = useState(true);
    const bootstrapStartedRef = useRef(false);

    const {
        status,
        progress,
        error,
        uploadedFile,
        dataSummary,
        validationReport,
        uploadFile,
        loadSampleDataset,
        hydrateSession,
        reset,
    } = useDataUpload();

    useEffect(() => {
        if (bootstrapStartedRef.current) {
            return;
        }

        bootstrapStartedRef.current = true;
        let cancelled = false;

        const bootstrap = async () => {
            try {
                const hasContextData = Boolean(dataSummary && validationReport);
                const hasStoredSession = api.hasStoredSession();

                if (!hasContextData && hasStoredSession && status === 'idle') {
                    await hydrateSession();
                }
            } finally {
                if (!cancelled) {
                    setIsBootstrapping(false);
                }
            }
        };

        bootstrap();

        return () => {
            cancelled = true;
        };
    }, [dataSummary, hydrateSession, status, validationReport]);

    const isLoading = status === 'uploading' || status === 'validating';
    const showResults = status === 'success' && dataSummary && validationReport;
    const showSessionSkeleton = isBootstrapping;

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
                    {showSessionSkeleton && <SessionPageSkeleton variant="upload" />}

                    {!showSessionSkeleton && (status === 'idle' || status === 'error') && (
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

                    {!showSessionSkeleton && (status === 'uploading' || status === 'validating') && (
                        <UploadProgress
                            status={status}
                            progress={progress}
                            file={uploadedFile}
                            error={error}
                        />
                    )}

                    {!showSessionSkeleton && showResults && (
                        <>
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
                                    onDelete={reset}
                                />
                            </section>
                        </>
                    )}
                </main>
            </div>
        </div>
    );
}
