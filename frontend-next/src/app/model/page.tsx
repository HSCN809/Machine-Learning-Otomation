'use client';

import { useEffect, useState, useSyncExternalStore } from 'react';
import { Target, BrainCircuit, SlidersHorizontal, Rocket, BarChart3, ChevronLeft, ChevronRight, Play, SkipForward } from 'lucide-react';
import { Sidebar, Header } from '@/components/layout';
import {
    TargetSelector,
    ModelGrid,
    HyperparameterForm,
    TrainingProgress,
    MetricsDisplay,
    ConfusionMatrix,
    FeatureImportance,
    ModelComparison,
    ResultsExport,
} from '@/components/model-selection';
import { NoDataWarning, SessionPageSkeleton, StepProgress } from '@/components/common';
import { useModelSelection } from '@/hooks/useModelSelection';
import { hasStoredSession } from '@/lib/api';
import { theme } from '@/styles/theme';

const subscribeToSession = () => () => {};
const getSessionSnapshot = () => hasStoredSession();
const getServerSessionSnapshot = (): boolean | null => null;

const STEPS = [
    { id: 0, name: 'Target Secimi', icon: <Target className="h-5 w-5" /> },
    { id: 1, name: 'Model Secimi', icon: <BrainCircuit className="h-5 w-5" /> },
    { id: 2, name: 'Hiperparametreler', icon: <SlidersHorizontal className="h-5 w-5" /> },
    { id: 3, name: 'Egitim', icon: <Rocket className="h-5 w-5" /> },
    { id: 4, name: 'Sonuclar', icon: <BarChart3 className="h-5 w-5" /> },
];

export default function ModelSelectionPage() {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const hasSession = useSyncExternalStore(
        subscribeToSession,
        getSessionSnapshot,
        getServerSessionSnapshot
    );

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
        toggleModelSelection,
        updateModelParams,
        trainModels,
        stopTraining,
    } = useModelSelection();

    useEffect(() => {
        if (hasSession) {
            void loadColumns();
        }
    }, [hasSession, loadColumns]);

    const hasData = hasSession === true && columns.length > 0;
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
                                    {selectedModels.length} model egitime hazir
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
                                    Egitimi Baslat
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
                                    {trainingStatus === 'stopping' ? 'Durduruluyor...' : 'Egitimi Durdur'}
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
                                        En Iyi Model: {trainingResults[0]?.modelName}
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
                    title="Model Secimi"
                    subtitle="Verilerinize uygun modelleri secin, egitin ve karsilastirin."
                />

                <main className="space-y-6 p-6">
                    {hasSession === true && isLoading && !hasData && <SessionPageSkeleton variant="wizard" />}

                    {hasSession !== null && !isLoading && !hasData && (
                        <NoDataWarning
                            title="Veri Yuklenmedi"
                            description="Model secimi ve egitimi yapabilmek icin once veri yuklemeniz gerekmektedir."
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
                                                Ileri
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
                                                Egit
                                            </button>
                                        )}
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
