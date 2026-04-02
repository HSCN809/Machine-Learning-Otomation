'use client';

import { useState, useEffect } from 'react';
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
import { NoDataWarning } from '@/components/common';
import { useModelSelection } from '@/hooks/useModelSelection';
import { hasStoredSession } from '@/lib/api';
import { theme } from '@/styles/theme';
import { ChevronLeft, ChevronRight, Loader2, Play, RotateCcw } from 'lucide-react';

const STEPS = [
    { id: 0, name: 'Target Seçimi', icon: '🎯' },
    { id: 1, name: 'Model Seçimi', icon: '🧠' },
    { id: 2, name: 'Hiperparametreler', icon: '⚙️' },
    { id: 3, name: 'Eğitim', icon: '🚀' },
    { id: 4, name: 'Sonuçlar', icon: '📊' },
];

export default function ModelSelectionPage() {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [hasSession, setHasSession] = useState<boolean | null>(null);

    const {
        currentStep,
        targetColumn,
        problemType,
        selectedModels,
        modelParams,
        trainingResults,
        isTraining,
        error,
        columns,
        availableModels,
        goToStep,
        nextStep,
        prevStep,
        canGoNext,
        canGoPrev,
        loadColumns,
        setTargetColumn,
        toggleModelSelection,
        updateModelParams,
        trainModels,
        resetAll,
    } = useModelSelection();

    // Load columns on mount
    useEffect(() => {
        const sessionExists = hasStoredSession();
        setHasSession(sessionExists);
        if (sessionExists) {
            loadColumns();
        }
    }, [loadColumns]);

    const hasData = hasSession === true && columns.length > 0;
    const currentStepInfo = STEPS[currentStep];

    // Render current step content
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
                            totalModels={selectedModels.length}
                            completedModels={trainingResults.length}
                        />

                        {!isTraining && trainingResults.length === 0 && (
                            <div className="text-center py-8">
                                <p className="text-gray-400 mb-4">
                                    {selectedModels.length} model eğitime hazır
                                </p>
                                <button
                                    onClick={trainModels}
                                    className="inline-flex items-center gap-2 px-8 py-3 rounded-xl font-medium text-white transition-all hover:scale-105"
                                    style={{
                                        background: theme.gradients.primary,
                                        boxShadow: theme.glow.cyan,
                                    }}
                                >
                                    <Play className="w-5 h-5" />
                                    Eğitimi Başlat
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
                                {/* Best model metrics */}
                                <div>
                                    <h3 className="text-lg font-semibold text-white mb-3">
                                        🏆 En İyi Model: {trainingResults[0]?.modelName}
                                    </h3>
                                    <MetricsDisplay
                                        metrics={trainingResults[0].metrics}
                                        problemType={problemType}
                                    />
                                </div>

                                {/* Confusion matrix for classification */}
                                {problemType === 'classification' && trainingResults[0]?.confusionMatrix && (
                                    <ConfusionMatrix matrix={trainingResults[0].confusionMatrix} />
                                )}

                                {/* Feature importance */}
                                {trainingResults[0]?.featureImportance && (
                                    <FeatureImportance data={trainingResults[0].featureImportance} />
                                )}

                                {/* Model comparison */}
                                <ModelComparison results={trainingResults} problemType={problemType} />

                                {/* Export */}
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
                <Header title="Model Seçimi" />

                <main className="p-6 space-y-6">
                    {/* Page Header */}
                    <div>
                        <h1 className="text-2xl font-bold text-white mb-2">🤖 Model Seçimi ve Eğitimi</h1>
                        <p className="text-gray-400">
                            Verilerinize uygun modelleri seçin, eğitin ve karşılaştırın.
                        </p>
                    </div>

                    {/* No Data Warning */}
                    {hasSession !== null && !hasData && (
                        <NoDataWarning
                            title="Veri Yüklenmedi"
                            description="Model seçimi ve eğitimi yapabilmek için önce veri yüklemeniz gerekmektedir."
                        />
                    )}

                    {/* Content - only show when data is loaded */}
                    {hasData && (
                        <>
                            {/* Step Progress */}
                            <div className="flex items-center gap-2">
                                {STEPS.map((step, index) => (
                                    <div key={step.id} className="flex items-center">
                                        <button
                                            onClick={() => index <= currentStep && goToStep(index)}
                                            disabled={index > currentStep}
                                            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${index === currentStep
                                                ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50'
                                                : index < currentStep
                                                    ? 'bg-green-500/10 text-green-400 cursor-pointer hover:bg-green-500/20'
                                                    : 'bg-white/5 text-gray-500 cursor-not-allowed'
                                                }`}
                                        >
                                            <span>{step.icon}</span>
                                            <span className="hidden sm:inline">{step.name}</span>
                                        </button>
                                        {index < STEPS.length - 1 && (
                                            <ChevronRight className="w-5 h-5 text-gray-600 mx-1" />
                                        )}
                                    </div>
                                ))}
                            </div>

                            {/* Error display */}
                            {error && (
                                <div className="p-4 rounded-xl border border-red-500/30 bg-red-500/10">
                                    <p className="text-red-400">❌ {error}</p>
                                </div>
                            )}

                            {/* Step content */}
                            <div
                                className="p-6 rounded-2xl border border-white/10"
                                style={{
                                    background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.6) 0%, rgba(31, 41, 55, 0.4) 100%)',
                                }}
                            >
                                {/* Step header */}
                                <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
                                    <span className="text-3xl">{currentStepInfo?.icon}</span>
                                    <h2 className="text-xl font-bold text-white">{currentStepInfo?.name}</h2>
                                </div>

                                {/* Content */}
                                {renderStepContent()}

                                {/* Navigation */}
                                <div className="flex items-center justify-between pt-6 mt-6 border-t border-white/10">
                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={prevStep}
                                            disabled={!canGoPrev || isTraining}
                                            className="flex items-center gap-2 px-4 py-2 rounded-xl border border-white/10 text-white hover:bg-white/5 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                                        >
                                            <ChevronLeft className="w-4 h-4" />
                                            Geri
                                        </button>
                                        <button
                                            onClick={resetAll}
                                            disabled={isTraining}
                                            className="flex items-center gap-2 px-4 py-2 rounded-xl border border-white/10 text-gray-400 hover:text-white hover:bg-white/5 transition-all"
                                        >
                                            <RotateCcw className="w-4 h-4" />
                                        </button>
                                    </div>

                                    {currentStep < 3 && (
                                        <button
                                            onClick={nextStep}
                                            disabled={!canGoNext || isTraining}
                                            className="flex items-center gap-2 px-6 py-2 rounded-xl font-medium text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105"
                                            style={{
                                                background: canGoNext && !isTraining ? theme.gradients.primary : 'rgba(255,255,255,0.1)',
                                                boxShadow: canGoNext && !isTraining ? theme.glow.cyan : undefined,
                                            }}
                                        >
                                            İleri
                                            <ChevronRight className="w-4 h-4" />
                                        </button>
                                    )}

                                    {currentStep === 3 && !isTraining && trainingResults.length === 0 && (
                                        <button
                                            onClick={trainModels}
                                            className="flex items-center gap-2 px-6 py-2 rounded-xl font-medium text-white transition-all hover:scale-105"
                                            style={{
                                                background: theme.gradients.primary,
                                                boxShadow: theme.glow.cyan,
                                            }}
                                        >
                                            <Play className="w-4 h-4" />
                                            Eğit
                                        </button>
                                    )}
                                </div>
                            </div>
                        </>
                    )}
                </main>
            </div>
        </div>
    );
}
