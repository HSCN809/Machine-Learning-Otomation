'use client';

import { useState, useEffect } from 'react';
import { Sidebar, Header } from '@/components/layout';
import {
    StepProgress,
    StepNavigation,
    HistoryLog,
    FeatureEngineering,
    MissingValues,
    Outliers,
    Encoding,
    Scaling,
    Summary,
} from '@/components/preprocessing';
import { NoDataWarning } from '@/components/common';
import { usePreprocessing, PREPROCESSING_STEPS } from '@/hooks/usePreprocessing';
import { theme } from '@/styles/theme';
import { Loader2 } from 'lucide-react';

export default function PreprocessingPage() {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

    const {
        currentStep,
        completedSteps,
        history,
        columns,
        isLoading,
        error,
        goToStep,
        nextStep,
        prevStep,
        canGoNext,
        canGoPrev,
        loadColumns,
        applyMissingValues,
        applyOutliers,
        applyEncoding,
        applyScaling,
        applyFeatureEngineering,
        undoLastAction,
        resetAll,
        numericColumns,
        categoricalColumns,
        columnsWithMissing,
    } = usePreprocessing();

    // Load columns on mount
    useEffect(() => {
        loadColumns();
    }, [loadColumns]);

    const hasData = columns.length > 0;
    const currentStepInfo = PREPROCESSING_STEPS[currentStep];
    const isLastStep = currentStep === PREPROCESSING_STEPS.length - 1;

    // Render current step content
    const renderStepContent = () => {
        switch (currentStepInfo?.key) {
            case 'feature_engineering':
                return (
                    <FeatureEngineering
                        columns={columns}
                        numericColumns={numericColumns}
                        onApply={applyFeatureEngineering}
                        isLoading={isLoading}
                    />
                );
            case 'missing_values':
                return (
                    <MissingValues
                        columns={columns}
                        columnsWithMissing={columnsWithMissing}
                        onApply={applyMissingValues}
                        isLoading={isLoading}
                    />
                );
            case 'outliers':
                return (
                    <Outliers
                        numericColumns={numericColumns}
                        onApply={applyOutliers}
                        isLoading={isLoading}
                    />
                );
            case 'encoding':
                return (
                    <Encoding
                        categoricalColumns={categoricalColumns}
                        onApply={applyEncoding}
                        isLoading={isLoading}
                    />
                );
            case 'scaling':
                return (
                    <Scaling
                        numericColumns={numericColumns}
                        onApply={applyScaling}
                        isLoading={isLoading}
                    />
                );
            case 'summary':
                return (
                    <Summary
                        history={history}
                        columns={columns}
                        originalColumnCount={6}
                    />
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
                <Header title="Veri Ön İşleme" />

                <main className="p-6 space-y-6">
                    {/* Page Header */}
                    <div>
                        <h1 className="text-2xl font-bold text-white mb-2">🔧 Veri Ön İşleme</h1>
                        <p className="text-gray-400">
                            Adım adım verilerinizi model eğitimine hazırlayın.
                        </p>
                    </div>

                    {/* Step Progress */}
                    <StepProgress
                        steps={PREPROCESSING_STEPS}
                        currentStep={currentStep}
                        completedSteps={completedSteps}
                        onStepClick={goToStep}
                    />

                    {/* Error display */}
                    {error && (
                        <div className="p-4 rounded-xl border border-red-500/30 bg-red-500/10">
                            <p className="text-red-400">❌ {error}</p>
                        </div>
                    )}

                    {/* Main content area */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* Step content */}
                        <div className="lg:col-span-2">
                            <div
                                className="p-6 rounded-2xl border border-white/10"
                                style={{
                                    background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.6) 0%, rgba(31, 41, 55, 0.4) 100%)',
                                }}
                            >
                                {/* Step header */}
                                <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
                                    <span className="text-3xl">{currentStepInfo?.icon}</span>
                                    <div>
                                        <h2 className="text-xl font-bold text-white">{currentStepInfo?.name}</h2>
                                        <p className="text-sm text-gray-400">{currentStepInfo?.description}</p>
                                    </div>
                                </div>

                                {/* Step content */}
                                {renderStepContent()}

                                {/* Navigation */}
                                {!isLastStep && (
                                    <StepNavigation
                                        onPrev={prevStep}
                                        onNext={nextStep}
                                        onSkip={nextStep}
                                        onReset={resetAll}
                                        canGoPrev={canGoPrev}
                                        canGoNext={canGoNext}
                                        isLastStep={isLastStep}
                                        isLoading={isLoading}
                                    />
                                )}
                            </div>
                        </div>

                        {/* History sidebar */}
                        <div className="lg:col-span-1">
                            <HistoryLog
                                history={history}
                                onUndo={undoLastAction}
                                onClear={resetAll}
                            />
                        </div>
                    </div>
                </main>
            </div>
        </div>
    );
}
