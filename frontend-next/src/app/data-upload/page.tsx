'use client';

import { useState } from 'react';
import { Sidebar, Header } from '@/components/layout';
import {
    FileDropzone,
    SampleDatasets,
    UploadProgress,
    ValidationReport,
    DataPreview,
} from '@/components/data-upload';
import { useDataUpload } from '@/hooks/useDataUpload';
import { RefreshCw } from 'lucide-react';
import { theme } from '@/styles/theme';

export default function DataUploadPage() {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

    const {
        status,
        progress,
        error,
        uploadedFile,
        dataSummary,
        validationReport,
        uploadFile,
        loadSampleDataset,
        reset,
    } = useDataUpload();

    const isLoading = status === 'uploading' || status === 'validating';
    const showResults = status === 'success' && dataSummary && validationReport;

    return (
        <div className="min-h-screen">
            {/* Sidebar */}
            <Sidebar
                isCollapsed={sidebarCollapsed}
                onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
            />

            {/* Main Content */}
            <div
                className="transition-all duration-300"
                style={{
                    marginLeft: sidebarCollapsed ? '80px' : '288px',
                }}
            >
                <Header title="Veri Yükleme" />

                <main className="p-6 space-y-8">
                    {/* Page description */}
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-2xl font-bold text-white mb-2">📊 Veri Yükleme</h1>
                            <p className="text-gray-400">
                                CSV veya Excel dosyalarınızı yükleyin ve otomatik doğrulama alın.
                            </p>
                        </div>

                        {/* Reset button - always visible */}
                        <button
                            onClick={reset}
                            className="flex items-center gap-2 px-4 py-2 rounded-xl border border-white/10 text-gray-400 hover:text-white hover:bg-white/5 transition-all cursor-pointer"
                        >
                            <RefreshCw className="w-4 h-4" />
                            <span>Sıfırla</span>
                        </button>
                    </div>

                    {/* Upload section - only show when idle or on error */}
                    {(status === 'idle' || status === 'error') && (
                        <>
                            {/* File dropzone */}
                            <section
                                className="p-6 rounded-2xl border border-white/10"
                                style={{
                                    background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.6) 0%, rgba(31, 41, 55, 0.4) 100%)',
                                }}
                            >
                                <h2 className="text-lg font-semibold text-white mb-4">📁 Dosya Yükle</h2>
                                <FileDropzone
                                    onFileSelect={uploadFile}
                                    disabled={isLoading}
                                />
                            </section>

                            {/* Divider */}
                            <div className="flex items-center gap-4">
                                <div className="flex-1 h-px bg-white/10" />
                                <span className="text-gray-500 text-sm">veya</span>
                                <div className="flex-1 h-px bg-white/10" />
                            </div>

                            {/* Sample datasets */}
                            <section
                                className="p-6 rounded-2xl border border-white/10"
                                style={{
                                    background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.6) 0%, rgba(31, 41, 55, 0.4) 100%)',
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

                    {/* Upload progress */}
                    {(status === 'uploading' || status === 'validating') && (
                        <UploadProgress
                            status={status}
                            progress={progress}
                            file={uploadedFile}
                            error={error}
                        />
                    )}

                    {/* Results section */}
                    {showResults && (
                        <>
                            {/* Success indicator */}
                            <div
                                className="p-4 rounded-xl border"
                                style={{
                                    borderColor: `${theme.colors.status.success}50`,
                                    background: `${theme.colors.status.success}10`,
                                }}
                            >
                                <p className="text-green-400 font-medium">
                                    ✅ Veri başarıyla yüklendi: {uploadedFile?.name || 'Hazır veri seti'}
                                </p>
                            </div>

                            {/* Data preview */}
                            <section
                                className="p-6 rounded-2xl border border-white/10"
                                style={{
                                    background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.6) 0%, rgba(31, 41, 55, 0.4) 100%)',
                                }}
                            >
                                <DataPreview summary={dataSummary} />
                            </section>

                            {/* Validation report */}
                            <section
                                className="p-6 rounded-2xl border border-white/10"
                                style={{
                                    background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.6) 0%, rgba(31, 41, 55, 0.4) 100%)',
                                }}
                            >
                                <ValidationReport report={validationReport} />
                            </section>

                            {/* Next step CTA */}
                            <div
                                className="p-6 rounded-xl border border-cyan-500/20"
                                style={{
                                    background: 'linear-gradient(135deg, rgba(0, 217, 255, 0.05) 0%, rgba(0, 255, 136, 0.05) 100%)',
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
                                            🔍 EDA
                                        </a>
                                        <a
                                            href="/preprocessing"
                                            className="px-4 py-2 rounded-xl font-medium text-white transition-all hover:scale-105"
                                            style={{
                                                background: theme.gradients.primary,
                                                boxShadow: theme.glow.cyan,
                                            }}
                                        >
                                            🔧 Ön İşleme
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
