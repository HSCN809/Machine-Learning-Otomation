'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Sidebar, Header } from '@/components/layout';
import { ProtectedRouteBoundary } from '@/components/auth/ProtectedRouteBoundary';
import {
    DataEditor,
    FileDropzone,
    SampleDatasets,
    UploadProgress,
} from '@/components/data-upload';
import { SessionPageSkeleton } from '@/components/common';
import { useDataUpload } from '@/hooks/useDataUpload';
import * as api from '@/lib/api';
import { normalizeNextPath } from '@/lib/routing';

export default function DataUploadPage() {
    const router = useRouter();
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [isBootstrapping, setIsBootstrapping] = useState(true);
    const bootstrapStartedRef = useRef(false);
    const nextPath = useMemo(
        () =>
            normalizeNextPath(
                typeof window === 'undefined'
                    ? null
                    : new URLSearchParams(window.location.search).get('next'),
                ''
            ),
        []
    );

    const {
        status,
        progress,
        error,
        uploadedFile,
        dataSummary,
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
                const hasContextData = Boolean(dataSummary);
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
    }, [dataSummary, hydrateSession, status]);

    const isLoading = status === 'uploading' || status === 'validating';
    const showEditor = status === 'success' && dataSummary;
    const showSessionSkeleton = isBootstrapping;

    return (
        <ProtectedRouteBoundary>
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

                    <main className="space-y-8 p-6">
                        {showSessionSkeleton && <SessionPageSkeleton variant="upload" />}

                        {!showSessionSkeleton && (status === 'idle' || status === 'error') && (
                            <>
                                <section
                                    className="rounded-2xl border border-white/10 p-6"
                                    style={{
                                        background:
                                            'linear-gradient(135deg, rgba(17, 24, 39, 0.6) 0%, rgba(31, 41, 55, 0.4) 100%)',
                                    }}
                                >
                                    <h2 className="mb-4 text-lg font-semibold text-white">Dosya Yükle</h2>
                                    <FileDropzone onFileSelect={uploadFile} disabled={isLoading} />
                                </section>

                                <div className="flex items-center gap-4">
                                    <div className="h-px flex-1 bg-white/10" />
                                    <span className="text-sm text-gray-500">veya</span>
                                    <div className="h-px flex-1 bg-white/10" />
                                </div>

                                <section
                                    className="rounded-2xl border border-white/10 p-6"
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

                        {!showSessionSkeleton && showEditor && nextPath && (
                            <section className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 p-5">
                                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                                    <div>
                                        <h2 className="text-lg font-semibold text-white">Veri hazır</h2>
                                        <p className="mt-1 text-sm text-slate-300">
                                            İsterseniz veri düzenlemeye devam edin veya geldiğiniz adıma geri dönün.
                                        </p>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => router.push(nextPath)}
                                        className="inline-flex cursor-pointer items-center justify-center rounded-full bg-white px-5 py-2.5 text-sm font-semibold text-slate-950 transition-transform duration-300 hover:-translate-y-0.5"
                                    >
                                        Hedef adıma dön
                                    </button>
                                </div>
                            </section>
                        )}

                        {!showSessionSkeleton && showEditor && (
                            <section
                                className="rounded-2xl border border-white/10 p-6"
                                style={{
                                    background:
                                        'linear-gradient(135deg, rgba(17, 24, 39, 0.6) 0%, rgba(31, 41, 55, 0.4) 100%)',
                                }}
                            >
                                <DataEditor onSaved={hydrateSession} onDelete={reset} />
                            </section>
                        )}
                    </main>
                </div>
            </div>
        </ProtectedRouteBoundary>
    );
}
