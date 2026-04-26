'use client';

import { ReactNode } from 'react';
import { Check, SkipForward } from 'lucide-react';
import { cn } from '@/lib/utils';
import { theme } from '@/styles/theme';

export type StepStatus = 'pending' | 'current' | 'completed' | 'skipped';

export interface ProgressStepItem {
    id: string | number;
    name: string;
    icon: ReactNode;
}

interface StepProgressProps {
    steps: ProgressStepItem[];
    currentStep: number;
    completedSteps?: number[];
    skippedSteps?: number[];
    onStepClick?: (step: number) => void;
    isStepClickable?: (index: number, status: StepStatus) => boolean;
    showActiveLine?: boolean;
}

export function StepProgress({
    steps,
    currentStep,
    completedSteps = [],
    skippedSteps = [],
    onStepClick,
    isStepClickable,
    showActiveLine = true,
}: StepProgressProps) {
    const getStepStatus = (index: number): StepStatus => {
        if (completedSteps.includes(index)) return 'completed';
        if (skippedSteps.includes(index)) return 'skipped';
        if (index === currentStep) return 'current';
        return 'pending';
    };

    return (
        <div className="w-full">
            <div className="hidden md:flex items-center justify-between relative">
                <div className="absolute top-6 left-0 right-0 h-0.5 bg-white/10" />
                {showActiveLine && (
                    <div
                        className="absolute top-6 left-0 h-0.5 transition-all duration-500"
                        style={{
                            width: `${(currentStep / (steps.length - 1)) * 100}%`,
                            background: theme.gradients.primary,
                            boxShadow: theme.glow.cyan,
                        }}
                    />
                )}

                {steps.map((step, index) => {
                    const status = getStepStatus(index);
                    const clickable = isStepClickable
                        ? isStepClickable(index, status)
                        : status === 'completed' || status === 'skipped' || index <= currentStep;

                    return (
                        <div
                            key={step.id}
                            className="relative z-10 flex flex-col items-center"
                            style={{ width: `${100 / steps.length}%` }}
                        >
                            <button
                                onClick={() => clickable && onStepClick?.(index)}
                                disabled={!clickable}
                                className={cn(
                                    'w-12 h-12 rounded-full flex items-center justify-center text-lg transition-all duration-300 border-2',
                                    status === 'completed' && 'border-green-500 bg-green-500/20',
                                    status === 'skipped' && 'border-amber-500 bg-amber-500/15',
                                    status === 'current' && 'border-cyan-500 bg-cyan-500/20',
                                    status === 'pending' && 'border-white/20 bg-white/5',
                                    clickable && 'cursor-pointer hover:scale-110',
                                    !clickable && 'cursor-not-allowed opacity-50'
                                )}
                                style={
                                    status === 'current'
                                        ? { boxShadow: theme.glow.cyan }
                                        : status === 'completed'
                                          ? { boxShadow: theme.glow.green }
                                          : status === 'skipped'
                                            ? { boxShadow: '0 0 20px rgba(245, 158, 11, 0.25)' }
                                          : undefined
                                }
                            >
                                {status === 'completed' ? (
                                    <Check className="w-6 h-6 text-green-400" />
                                ) : status === 'skipped' ? (
                                    <SkipForward className="w-5 h-5 text-amber-400" />
                                ) : (
                                    step.icon
                                )}
                            </button>

                            <span
                                className={cn(
                                    'mt-6 text-sm font-medium text-center',
                                    status === 'current' && 'text-cyan-400',
                                    status === 'completed' && 'text-green-400',
                                    status === 'skipped' && 'text-amber-400',
                                    status === 'pending' && 'text-gray-500'
                                )}
                            >
                                {step.name}
                            </span>
                        </div>
                    );
                })}
            </div>

            <div className="md:hidden">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-400">
                        Adım {currentStep + 1} / {steps.length}
                    </span>
                    <span className="text-sm font-medium text-cyan-400">
                        {steps[currentStep]?.icon} {steps[currentStep]?.name}
                    </span>
                </div>
                <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                    <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{
                            width: `${((currentStep + 1) / steps.length) * 100}%`,
                            background: theme.gradients.primary,
                        }}
                    />
                </div>
            </div>
        </div>
    );
}
