'use client';

import dynamic from 'next/dynamic';
import { useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Sidebar, Header } from '@/components/layout';
import { ProtectedRouteBoundary } from '@/components/auth/ProtectedRouteBoundary';
import { FileDropzone, SavedDatasets, SampleDatasets, UploadProgress } from '@/components/data-upload';
import { SessionPageSkeleton } from '@/components/common';
import { TimelineDrawerLauncher } from '@/components/timeline';
import { useDataUpload } from '@/hooks/useDataUpload';
import { normalizeNextPath } from '@/lib/routing';
import * as api from '@/lib/api';

const DataEditor = dynamic(
    () => import('@/components/data-upload/DataEditor').then((module) => module.DataEditor),
    {
        loading: () => <SessionPageSkeleton variant="upload" />,
    }
);

export default function DataUploadPage() {
    const router = useRouter();
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [isBootstrapping, setIsBootstrapping] = useState(true);
    const [showDropzone, setShowDropzone] = useState(true);
    const [editorRefreshToken, setEditorRefreshToken] = useState(0);
    const fileDropzoneSectionRef = useRef<HTMLElement | null>(null);
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
        isInitializing,
        savedDatasets,
        activeDatasetId,
        isSavedDatasetsLoading,
        uploadFile,
        loadSampleDataset,
        loadSavedDataset,
        renameSavedDataset,
        deleteSavedDataset,
        hydrateSession,
        refreshSavedDatasets,
        reset,
    } = useDataUpload();

    useEffect(() => {
        let cancelled = false;

        const bootstrap = async () => {
            try {
                await refreshSavedDatasets();
                if (!cancelled) {
                    setShowDropzone(!api.hasStoredSession());
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
    }, [refreshSavedDatasets]);

    const handleNewUpload = () => {
        setShowDropzone(true);
        fileDropzoneSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    };

    const handleFileUpload = (file: File) => {
        setShowDropzone(false);
        api.clearStoredSession();
        uploadFile(file);
    };

    const handleSampleSelect = (datasetId: string) => {
        setShowDropzone(false);
        api.clearStoredSession();
        loadSampleDataset(datasetId);
    };

    const handleSavedDatasetLoad = async (datasetId: string) => {
        const isSwitchingDataset = Boolean(activeDatasetId && activeDatasetId !== datasetId);

        if (isSwitchingDataset) {
            const confirmed = window.confirm(
                'Aktif veri seti değiştirilecek. Mevcut veri setindeki değişiklikleri kaydettiğinizden emin misiniz? Kaydedilmemiş değişiklikler kaybolabilir. Devam etmek istiyor musunuz?'
            );

            if (!confirmed) {
                return;
            }
        }

        setShowDropzone(false);
        await loadSavedDataset(datasetId);
    };

    const handleSavedDatasetRename = async (datasetId: string, name: string) => {
        await renameSavedDataset(datasetId, name);
    };

    const handleSavedDatasetDelete = async (datasetId: string) => {
        const wasActiveDataset = activeDatasetId === datasetId;
        const confirmed = window.confirm(
            'Bu veri seti kalıcı olarak silinecek. Bu veri setine bağlı preprocessing geçmişi ve model kayıtları da kaldırılacak. Devam etmek istiyor musunuz?'
        );

        if (!confirmed) {
            return;
        }

        await deleteSavedDataset(datasetId);

        if (wasActiveDataset) {
            setShowDropzone(true);
        }
    };

    const isLoading = status === 'uploading' || status === 'validating';
    const hasActiveSession = Boolean(activeDatasetId);
    const showEditor = status === 'success' && Boolean(dataSummary);
    const showActiveEditor = !showDropzone && (showEditor || hasActiveSession);
    const showSessionSkeleton = isBootstrapping;

    const handleEditorSaved = async () => {
        await hydrateSession();
    };

    const handleTimelineUndo = async () => {
        await hydrateSession();
        setEditorRefreshToken((currentValue) => currentValue + 1);
    };

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

                        {!showSessionSkeleton && (
                            <section
                                className="rounded-2xl border border-white/10 p-6"
                                style={{
                                    background:
                                        'linear-gradient(135deg, rgba(17, 24, 39, 0.6) 0%, rgba(31, 41, 55, 0.4) 100%)',
                                }}
                            >
                                <SavedDatasets
                                    datasets={savedDatasets}
                                    activeDatasetId={showDropzone ? null : activeDatasetId}
                                    loading={isSavedDatasetsLoading}
                                    disabled={isLoading || isInitializing}
                                    onLoad={handleSavedDatasetLoad}
                                    onRename={handleSavedDatasetRename}
                                    onDelete={handleSavedDatasetDelete}
                                    onNewUpload={handleNewUpload}
                                />
                            </section>
                        )}

                        {!showSessionSkeleton && showDropzone && (
                            <>
                                <section
                                    ref={fileDropzoneSectionRef}
                                    className="rounded-2xl border border-white/10 p-6"
                                    style={{
                                        background:
                                            'linear-gradient(135deg, rgba(17, 24, 39, 0.6) 0%, rgba(31, 41, 55, 0.4) 100%)',
                                    }}
                                >
                                    <h2 className="mb-4 text-lg font-semibold text-white">Dosya Yükle</h2>
                                    <FileDropzone onFileSelect={handleFileUpload} disabled={isLoading} />
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
                                        onSelect={handleSampleSelect}
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

                        {!showSessionSkeleton && showActiveEditor && nextPath && (
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

                        {!showSessionSkeleton && showActiveEditor && (
                            <section
                                className="rounded-2xl border border-white/10 p-6"
                                style={{
                                    background:
                                        'linear-gradient(135deg, rgba(17, 24, 39, 0.6) 0%, rgba(31, 41, 55, 0.4) 100%)',
                                }}
                            >
                                <DataEditor
                                    key={`${activeDatasetId ?? 'no-session'}:${editorRefreshToken}`}
                                    onSaved={handleEditorSaved}
                                    onDelete={reset}
                                />
                            </section>
                        )}
                    </main>
                </div>
                <TimelineDrawerLauncher
                    visible={!showSessionSkeleton}
                    enabled={showActiveEditor}
                    onAfterUndo={handleTimelineUndo}
                />
            </div>
        </ProtectedRouteBoundary>
    );
}
