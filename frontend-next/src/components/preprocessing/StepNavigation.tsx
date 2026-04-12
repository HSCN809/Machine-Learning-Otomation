'use client';

import { ChevronLeft, ChevronRight, SkipForward } from 'lucide-react';
import { cn } from '@/lib/utils';
import { theme } from '@/styles/theme';

interface StepNavigationProps {
    onPrev: () => void;
    onNext: () => void;
    onSkip?: () => void;
    canGoPrev: boolean;
    canGoNext: boolean;
    isLastStep?: boolean;
    isLoading?: boolean;
}

export function StepNavigation({
    onPrev,
    onNext,
    onSkip,
    canGoPrev,
    canGoNext,
    isLastStep = false,
    isLoading = false,
}: StepNavigationProps) {
    return (
        <div className="flex items-center justify-between pt-6 border-t border-white/10">
            <div className="flex items-center gap-2">
                {/* Back button */}
                <button
                    onClick={onPrev}
                    disabled={!canGoPrev || isLoading}
                    className={cn(
                        'flex items-center gap-2 px-4 py-2 rounded-xl border border-white/10 transition-all duration-200',
                        canGoPrev && !isLoading
                            ? 'cursor-pointer text-white hover:bg-white/5'
                            : 'text-gray-500 cursor-not-allowed opacity-50'
                    )}
                >
                    <ChevronLeft className="w-4 h-4" />
                    <span>Geri</span>
                </button>

            </div>

            <div className="flex items-center gap-2">
                {/* Skip button */}
                {onSkip && !isLastStep && (
                    <button
                        onClick={onSkip}
                        disabled={isLoading}
                        className={`flex items-center gap-2 px-4 py-2 rounded-xl border border-white/10 text-gray-400 hover:text-white hover:bg-white/5 transition-all duration-200 ${isLoading ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}
                    >
                        <span>Atla</span>
                        <SkipForward className="w-4 h-4" />
                    </button>
                )}

                {/* Next/Finish button */}
                <button
                    onClick={onNext}
                    disabled={!canGoNext && !isLastStep || isLoading}
                    className={cn(
                        'flex items-center gap-2 px-6 py-2 rounded-xl font-medium transition-all duration-200',
                        (canGoNext || isLastStep) && !isLoading
                            ? 'cursor-pointer text-white hover:scale-105'
                            : 'text-gray-500 cursor-not-allowed opacity-50'
                    )}
                    style={
                        (canGoNext || isLastStep) && !isLoading
                            ? {
                                background: theme.gradients.primary,
                                boxShadow: theme.glow.cyan,
                            }
                            : {
                                background: 'rgba(255,255,255,0.1)',
                            }
                    }
                >
                    <span>{isLastStep ? 'Tamamla' : 'İleri'}</span>
                    {!isLastStep && <ChevronRight className="w-4 h-4" />}
                </button>
            </div>
        </div>
    );
}
