'use client';

import dynamic from 'next/dynamic';
import { useState } from 'react';
import { usePathname } from 'next/navigation';
import { Target, BrainCircuit, SlidersHorizontal, Rocket, BarChart3, ChevronLeft, ChevronRight, Play, SkipForward } from 'lucide-react';
import { Sidebar, Header } from '@/components/layout';
import { ProtectedRouteBoundary } from '@/components/auth/ProtectedRouteBoundary';
import { NoDataWarning, SessionPageSkeleton, StepProgress } from '@/components/common';
import { TimelineDrawerLauncher } from '@/components/timeline';
import { HyperparameterForm } from '@/components/model-selection/HyperparameterForm';
import { MetricsDisplay } from '@/components/model-selection/MetricsDisplay';
import { ModelGrid } from '@/components/model-selection/ModelGrid';
import { TargetSelectorClean as TargetSelector } from '@/components/model-selection/TargetSelectorClean';
import { TrainingProgress } from '@/components/model-selection/TrainingProgress';
import { useModelSelection } from '@/hooks/useModelSelection';
import { useDatasetBootstrap } from '@/hooks/useDatasetBootstrap';
import { buildDataUploadHref } from '@/lib/routing';
import { theme } from '@/styles/theme';

const STEPS = [
    { id: 0, name: 'Target Seçimi', icon: <Target className="h-5 w-5" /> },
    { id: 1, name: 'Model Seçimi', icon: <BrainCircuit className="h-5 w-5" /> },
    { id: 2, name: 'Hiperparametreler', icon: <SlidersHorizontal className="h-5 w-5" /> },
    { id: 3, name: 'Eğitim', icon: <Rocket className="h-5 w-5" /> },
    { id: 4, name: 'Sonuçlar', icon: <BarChart3 className="h-5 w-5" /> },
];

function ResultsPanelFallback() {
    return (
        <div className="rounded-xl border border-white/10 bg-white/5 p-6">
            <div className="mb-4 h-6 w-40 animate-pulse rounded-lg bg-white/10" />
            <div className="h-72 animate-pulse rounded-2xl bg-white/8" />
        </div>
    );
}

const ConfusionMatrix = dynamic(
    () => import('@/components/model-selection/ConfusionMatrix').then((module) => module.ConfusionMatrix),
    {
        loading: () => <ResultsPanelFallback />,
        ssr: false,
    }
);

const FeatureImportance = dynamic(
    () => import('@/components/model-selection/FeatureImportance').then((module) => module.FeatureImportance),
    {
        loading: () => <ResultsPanelFallback />,
        ssr: false,
    }
);

const ModelComparison = dynamic(
    () => import('@/components/model-selection/ModelComparison').then((module) => module.ModelComparison),
    {
        loading: () => <ResultsPanelFallback />,
    }
);

const ResultsExport = dynamic(
    () => import('@/components/model-selection/ResultsExport').then((module) => module.ResultsExport),
    {
        loading: () => <ResultsPanelFallback />,
        ssr: false,
    }
);

export default function ModelSelectionPage() {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const pathname = usePathname();

    const {
        currentStep,
        completedSteps,
        skippedSteps,
        targetColumn,
        problemType,
        selectedModels,
        modelParams,
        trainingResults,
        isLoading,
        isTraining,
        trainingStatus,
        currentTrainingModel,
        completedTrainingModels,
        totalTrainingModels,
        error,
        columns,
        availableModels,
        goToStep,
        nextStep,
        skipStep,
        prevStep,
        canGoNext,
        canGoPrev,
        loadColumns,
        setTargetColumn,
        setProblemType,
        toggleModelSelection,
        updateModelParams,
        trainModels,
        stopTraining,
    } = useModelSelection();
    const datasetBootstrap = useDatasetBootstrap(loadColumns);

    const hasData = datasetBootstrap.isReady && columns.length > 0;
    const hasBootstrapError = !hasData && (datasetBootstrap.isError || Boolean(error));
    const bootstrapErrorMessage = error ?? 'Model verileri yüklenirken hata oluştu.';
    const currentStepInfo = STEPS[currentStep];
    const canSkip = currentStep < STEPS.length - 1;
    const currentTrainingModelName =
        availableModels.find((model) => model.id === currentTrainingModel)?.name ??
        currentTrainingModel ??
        undefined;

    const renderStepContent = () => {
        switch (currentStep) {
            case 0:
                return (
                    <TargetSelector
                        columns={columns}
                        selectedColumn={targetColumn}
                        problemType={problemType}
                        onSelect={setTargetColumn}
                        onProblemTypeChange={setProblemType}
                    />
                );
            case 1:
                return (
                    <ModelGrid
                        models={availableModels}
                        selectedModels={selectedModels}
                        onToggle={toggleModelSelection}
                    />
                );
            case 2:
                return (
                    <HyperparameterForm
                        models={availableModels}
                        selectedModels={selectedModels}
                        params={modelParams}
                        onUpdateParams={updateModelParams}
                    />
                );
            case 3:
                return (
                    <div className="space-y-6">
                        <TrainingProgress
                            isTraining={isTraining}
                            status={trainingStatus}
                            currentModel={currentTrainingModelName}
                            totalModels={totalTrainingModels || selectedModels.length}
                            completedModels={completedTrainingModels}
                        />

                        {!isTraining && trainingResults.length === 0 && (
                            <div className="py-8 text-center">
                                <p className="mb-4 text-gray-400">
                                    {selectedModels.length} model eğitime hazır
                                </p>
                                <button
                                    onClick={trainModels}
                                    className="inline-flex cursor-pointer items-center gap-2 rounded-xl px-8 py-3 font-medium text-white transition-all hover:scale-105"
                                    style={{
                                        background: theme.gradients.primary,
                                        boxShadow: theme.glow.cyan,
                                    }}
                                >
                                    <Play className="h-5 w-5" />
                                    Eğitimi Başlat
                                </button>
                            </div>
                        )}

                        {isTraining && (
                            <div className="flex justify-center">
                                <button
                                    onClick={stopTraining}
                                    disabled={trainingStatus === 'stopping'}
                                    className="inline-flex items-center gap-2 rounded-xl border border-red-500/30 bg-red-500/10 px-6 py-3 font-medium text-red-300 transition-all hover:bg-red-500/20 disabled:cursor-not-allowed disabled:opacity-50"
                                >
                                    {trainingStatus === 'stopping' ? 'Durduruluyor...' : 'Eğitimi Durdur'}
                                </button>
                            </div>
                        )}
                    </div>
                );
            case 4:
                return (
                    <div className="space-y-6">
                        {trainingResults.length > 0 && problemType && (
                            <>
                                <div>
                                    <h3 className="mb-3 text-lg font-semibold text-white">
                                        En İyi Model: {trainingResults[0]?.modelName}
                                    </h3>
                                    <MetricsDisplay
                                        metrics={trainingResults[0].metrics}
                                        problemType={problemType}
                                    />
                                </div>

                                {problemType === 'classification' && trainingResults[0]?.confusionMatrix && (
                                    <ConfusionMatrix
                                        matrix={trainingResults[0].confusionMatrix}
                                        labels={trainingResults[0].confusionLabels}
                                    />
                                )}

                                {trainingResults[0]?.featureImportance && (
                                    <FeatureImportance data={trainingResults[0].featureImportance} />
                                )}

                                <ModelComparison results={trainingResults} problemType={problemType} />
                                <ResultsExport results={trainingResults} />
                            </>
                        )}
                    </div>
                );
            default:
                return null;
        }
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
                        title="Model Seçimi"
                        subtitle="Verilerinize uygun modelleri seçin, eğitin ve karşılaştırın."
                    />

                    <main className="space-y-6 p-6">
                        {(datasetBootstrap.isChecking || (isLoading && !hasData)) && (
                            <SessionPageSkeleton variant="wizard" />
                        )}

                        {!datasetBootstrap.isChecking && !isLoading && hasBootstrapError && (
                            <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
                                <h2 className="text-lg font-semibold text-red-100">Model verileri yüklenemedi</h2>
                                <p className="mt-2 text-sm text-red-200/80">{bootstrapErrorMessage}</p>
                            </div>
                        )}

                        {!datasetBootstrap.isChecking && !isLoading && !hasBootstrapError && !hasData && (
                            <NoDataWarning
                                title="Veri Yüklenmedi"
                                description="Model seçimi ve eğitimi yapabilmek için önce veri yüklemeniz gerekmektedir."
                                href={buildDataUploadHref(pathname)}
                                actionLabel="Veri yüklemeye geç"
                            />
                        )}

                        {hasData && !isLoading && (
                            <>
                                <StepProgress
                                    steps={STEPS}
                                    currentStep={currentStep}
                                    completedSteps={completedSteps}
                                    skippedSteps={skippedSteps}
                                    onStepClick={goToStep}
                                    isStepClickable={(index) => index <= currentStep}
                                    showActiveLine={false}
                                />

                                {error && (
                                    <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4">
                                        <p className="text-red-400">{error}</p>
                                    </div>
                                )}

                                <div
                                    className="rounded-2xl border border-white/10 p-6"
                                    style={{
                                        background:
                                            'linear-gradient(135deg, rgba(17, 24, 39, 0.6) 0%, rgba(31, 41, 55, 0.4) 100%)',
                                    }}
                                >
                                    <div className="mb-6 flex items-center gap-3 border-b border-white/10 pb-4">
                                        <div className="text-cyan-400">{currentStepInfo?.icon}</div>
                                        <h2 className="text-xl font-bold text-white">{currentStepInfo?.name}</h2>
                                    </div>

                                    {renderStepContent()}

                                    <div className="mt-6 flex items-center justify-between border-t border-white/10 pt-6">
                                        <div className="flex items-center gap-2">
                                            <button
                                                onClick={prevStep}
                                                disabled={!canGoPrev || isTraining}
                                                className="flex cursor-pointer items-center gap-2 rounded-xl border border-white/10 px-4 py-2 text-white transition-all hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-50"
                                            >
                                                <ChevronLeft className="h-4 w-4" />
                                                Geri
                                            </button>
                                        </div>

                                        <div className="flex items-center gap-2">
                                            {canSkip && (
                                                <button
                                                    onClick={skipStep}
                                                    disabled={isTraining}
                                                    className="flex cursor-pointer items-center gap-2 rounded-xl border border-white/10 px-4 py-2 text-gray-400 transition-all hover:bg-white/5 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
                                                >
                                                    Atla
                                                    <SkipForward className="h-4 w-4" />
                                                </button>
                                            )}

                                            {currentStep < 3 && (
                                                <button
                                                    onClick={nextStep}
                                                    disabled={!canGoNext || isTraining}
                                                    className="flex cursor-pointer items-center gap-2 rounded-xl px-6 py-2 font-medium text-white transition-all hover:scale-105 disabled:cursor-not-allowed disabled:opacity-50"
                                                    style={{
                                                        background:
                                                            canGoNext && !isTraining
                                                                ? theme.gradients.primary
                                                                : 'rgba(255,255,255,0.1)',
                                                        boxShadow:
                                                            canGoNext && !isTraining ? theme.glow.cyan : undefined,
                                                    }}
                                                >
                                                    İleri
                                                    <ChevronRight className="h-4 w-4" />
                                                </button>
                                            )}

                                            {currentStep === 3 && !isTraining && trainingResults.length === 0 && (
                                                <button
                                                    onClick={trainModels}
                                                    className="flex cursor-pointer items-center gap-2 rounded-xl px-6 py-2 font-medium text-white transition-all hover:scale-105"
                                                    style={{
                                                        background: theme.gradients.primary,
                                                        boxShadow: theme.glow.cyan,
                                                    }}
                                                >
                                                    <Play className="h-4 w-4" />
                                                    Eğit
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </>
                        )}
                    </main>
                </div>

                <TimelineDrawerLauncher
                    visible={hasData}
                    onAfterUndo={loadColumns}
                />
            </div>
        </ProtectedRouteBoundary>
    );
}
