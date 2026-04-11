'use client';

import { useEffect, useRef, useState, useSyncExternalStore } from 'react';
import { Grip, History, X } from 'lucide-react';
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
import { ClickSpark, NoDataWarning, PixelTrail, SessionPageSkeleton } from '@/components/common';
import { usePreprocessing, PREPROCESSING_STEPS } from '@/hooks/usePreprocessing';
import { hasStoredSession } from '@/lib/api';
import { theme } from '@/styles/theme';

const subscribeToSession = () => () => {};
const getSessionSnapshot = () => hasStoredSession();
const getServerSessionSnapshot = (): boolean | null => null;

export default function PreprocessingPage() {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [isHistoryOpen, setIsHistoryOpen] = useState(false);
    const [historyButtonPosition, setHistoryButtonPosition] = useState(() => {
        if (typeof window === 'undefined') {
            return { x: 16, y: 16 };
        }

        return {
            x: window.innerWidth - 96,
            y: window.innerHeight - 120,
        };
    });
    const [historyTrailPointer, setHistoryTrailPointer] = useState<{ x: number; y: number } | null>(null);
    const [isHistoryButtonDragging, setIsHistoryButtonDragging] = useState(false);
    const hasSession = useSyncExternalStore(
        subscribeToSession,
        getSessionSnapshot,
        getServerSessionSnapshot
    );
    const dragOffsetRef = useRef({ x: 0, y: 0 });
    const dragStartRef = useRef({ x: 0, y: 0 });
    const didDragRef = useRef(false);

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
        loadInitialData,
        applyMissingValues,
        applyOutliers,
        applyEncoding,
        applyScaling,
        applyFeatureEngineering,
        undoLastAction,
        undoToHistoryItem,
        resetAll,
        numericColumns,
        categoricalColumns,
        columnsWithMissing,
    } = usePreprocessing();

    useEffect(() => {
        if (hasSession) {
            void loadInitialData();
        }
    }, [hasSession, loadInitialData]);

    const hasData = hasSession === true && columns.length > 0;
    const currentStepInfo = PREPROCESSING_STEPS[currentStep];
    const isLastStep = currentStep === PREPROCESSING_STEPS.length - 1;

    const handleHistoryButtonPointerDown = (event: React.PointerEvent<HTMLButtonElement>) => {
        const rect = event.currentTarget.getBoundingClientRect();
        dragStartRef.current = { x: event.clientX, y: event.clientY };
        didDragRef.current = false;
        setHistoryTrailPointer({ x: event.clientX, y: event.clientY });
        dragOffsetRef.current = {
            x: event.clientX - rect.left,
            y: event.clientY - rect.top,
        };

        const handlePointerMove = (moveEvent: PointerEvent) => {
            const buttonSize = 56;
            if (
                Math.abs(moveEvent.clientX - dragStartRef.current.x) > 4 ||
                Math.abs(moveEvent.clientY - dragStartRef.current.y) > 4
            ) {
                didDragRef.current = true;
                setIsHistoryButtonDragging(true);
            }

            setHistoryTrailPointer({ x: moveEvent.clientX, y: moveEvent.clientY });
            const nextX = Math.min(
                Math.max(16, moveEvent.clientX - dragOffsetRef.current.x),
                window.innerWidth - buttonSize - 16
            );
            const nextY = Math.min(
                Math.max(16, moveEvent.clientY - dragOffsetRef.current.y),
                window.innerHeight - buttonSize - 16
            );

            setHistoryButtonPosition({ x: nextX, y: nextY });
        };

        const handlePointerUp = () => {
            setIsHistoryButtonDragging(false);
            window.removeEventListener('pointermove', handlePointerMove);
            window.removeEventListener('pointerup', handlePointerUp);
        };

        window.addEventListener('pointermove', handlePointerMove);
        window.addEventListener('pointerup', handlePointerUp);
    };

    const handleHistoryButtonClick = () => {
        if (didDragRef.current) {
            didDragRef.current = false;
            return;
        }

        setIsHistoryOpen(true);
    };

    const renderStepContent = () => {
        switch (currentStepInfo?.key) {
            case 'missing_values':
                return (
                    <MissingValues
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
            case 'feature_engineering':
                return (
                    <FeatureEngineering
                        columns={columns}
                        numericColumns={numericColumns}
                        onApply={applyFeatureEngineering}
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

                <ClickSpark
                    className="relative"
                    sparkColor={theme.colors.primary.cyan}
                    sparkSize={12}
                    sparkRadius={20}
                    sparkCount={10}
                    duration={500}
                    extraScale={1.15}
                >
                    <main className="p-6 space-y-6">
                        {(hasSession === null || (hasSession === true && isLoading && !hasData)) && (
                            <SessionPageSkeleton variant="wizard" />
                        )}

                        {hasSession !== null && !isLoading && !hasData && (
                            <NoDataWarning
                                title="Veri Yüklenmedi"
                                description="Veri ön işleme yapabilmek için önce veri yüklemeniz gerekir."
                            />
                        )}

                        {hasData && (
                            <>
                                <StepProgress
                                    steps={PREPROCESSING_STEPS}
                                    currentStep={currentStep}
                                    completedSteps={completedSteps}
                                    onStepClick={goToStep}
                                    showActiveLine={false}
                                />

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
                            </>
                        )}
                    </main>
                </ClickSpark>
            </div>

            {hasData && (
                <>
                    <PixelTrail
                        active={isHistoryButtonDragging}
                        pointer={historyTrailPointer}
                        color={theme.colors.primary.cyan}
                        gridSize={22}
                        trailSize={0.55}
                        maxAge={320}
                        interpolate={10}
                    />
                    <button
                        type="button"
                        aria-label="İşlem geçmişini aç"
                        onPointerDown={handleHistoryButtonPointerDown}
                        onClick={handleHistoryButtonClick}
                        className="fixed z-40 flex h-14 w-14 cursor-grab items-center justify-center rounded-full border border-cyan-400/30 bg-slate-900/90 text-cyan-300 shadow-lg backdrop-blur transition-transform hover:scale-105 active:cursor-grabbing"
                        style={{
                            left: historyButtonPosition.x,
                            top: historyButtonPosition.y,
                            boxShadow: theme.glow.cyanStrong,
                        }}
                    >
                        <History className="h-5 w-5" />
                        <span className="pointer-events-none absolute -bottom-1 -right-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-cyan-500 px-1 text-[10px] font-semibold text-slate-950">
                            {history.length}
                        </span>
                        <span className="pointer-events-none absolute -top-1 -left-1 rounded-full border border-white/10 bg-slate-950/90 p-1 text-gray-400">
                            <Grip className="h-3 w-3" />
                        </span>
                    </button>

                    <div
                        className={`fixed inset-0 z-40 bg-slate-950/40 backdrop-blur-sm transition-opacity duration-300 ${isHistoryOpen ? 'pointer-events-auto opacity-100' : 'pointer-events-none opacity-0'}`}
                        onClick={() => setIsHistoryOpen(false)}
                    />

                    <aside
                        className={`fixed right-0 top-0 z-50 h-screen w-full max-w-md border-l border-white/10 bg-[#0D1528]/95 shadow-2xl backdrop-blur-xl transition-transform duration-300 ${isHistoryOpen ? 'translate-x-0' : 'translate-x-full'}`}
                    >
                        <div className="flex h-full flex-col">
                            <div className="flex items-start justify-between border-b border-white/10 px-5 py-5">
                                <div>
                                    <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-400/80">
                                        History
                                    </p>
                                    <h3 className="mt-1 text-xl font-semibold text-white">İşlem Timeline</h3>
                                    <p className="mt-1 text-sm text-gray-400">
                                        Preprocessing adımlarını yukarıdan aşağı kronolojik sırada görüntüleyin.
                                    </p>
                                </div>
                                <button
                                    type="button"
                                    onClick={() => setIsHistoryOpen(false)}
                                    className="flex h-10 w-10 cursor-pointer items-center justify-center rounded-full border border-white/10 bg-white/5 text-gray-300 transition-colors hover:bg-white/10 hover:text-white"
                                    aria-label="İşlem geçmişini kapat"
                                >
                                    <X className="h-5 w-5" />
                                </button>
                            </div>

                            <div className="flex-1 overflow-hidden p-5">
                                <HistoryLog
                                    history={history}
                                    onUndo={undoLastAction}
                                    onUndoItem={undoToHistoryItem}
                                    isLoading={isLoading}
                                    variant="timeline"
                                />
                            </div>
                        </div>
                    </aside>
                </>
            )}
        </div>
    );
}
