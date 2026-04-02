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
import { hasStoredSession } from '@/lib/api';

export default function PreprocessingPage() {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [hasSession, setHasSession] = useState<boolean | null>(null);

    const {
        currentStep,
        completedSteps,
        history,
        columns,
        isLoading,
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

    useEffect(() => {
        const sessionExists = hasStoredSession();
        setHasSession(sessionExists);
        if (sessionExists) {
            loadColumns();
        }
    }, [loadColumns]);

    const hasData = hasSession === true && columns.length > 0;
    const currentStepInfo = PREPROCESSING_STEPS[currentStep];
    const isLastStep = currentStep === PREPROCESSING_STEPS.length - 1;

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
                return <Summary history={history} columns={columns} originalColumnCount={6} />;
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
                    title="Veri Ön İşleme"
                    subtitle="Adım adım verilerinizi model eğitimine hazırlayın."
                />

                <main className="p-6 space-y-6">
                    {!isLoading && hasSession !== null && !hasData && (
                        <NoDataWarning
                            title="Veri Yüklenmedi"
                            description="Veri ön işleme yapabilmek için önce veri yüklemeniz gerekmektedir."
                        />
                    )}

                    {hasData && (
                        <>
                            <StepProgress
                                steps={PREPROCESSING_STEPS}
                                currentStep={currentStep}
                                completedSteps={completedSteps}
                                onStepClick={goToStep}
                            />

                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                                <div className="lg:col-span-2">
                                    <div
                                        className="p-6 rounded-2xl border border-white/10"
                                        style={{
                                            background:
                                                'linear-gradient(135deg, rgba(17, 24, 39, 0.6) 0%, rgba(31, 41, 55, 0.4) 100%)',
                                        }}
                                    >
                                        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
                                            <span className="text-3xl">{currentStepInfo?.icon}</span>
                                            <div>
                                                <h2 className="text-xl font-bold text-white">{currentStepInfo?.name}</h2>
                                                <p className="text-sm text-gray-400">{currentStepInfo?.description}</p>
                                            </div>
                                        </div>

                                        {renderStepContent()}

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

                                <div className="lg:col-span-1">
                                    <HistoryLog history={history} onUndo={undoLastAction} onClear={resetAll} />
                                </div>
                            </div>
                        </>
                    )}
                </main>
            </div>
        </div>
    );
}
