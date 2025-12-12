'use client';

import { cn } from '@/lib/utils';
import { theme } from '@/styles/theme';
import { PreprocessingStep, StepStatus } from '@/types/preprocessing';
import { Check } from 'lucide-react';

interface StepProgressProps {
    steps: PreprocessingStep[];
    currentStep: number;
    completedSteps: number[];
    onStepClick?: (step: number) => void;
}

export function StepProgress({ steps, currentStep, completedSteps, onStepClick }: StepProgressProps) {
    const getStepStatus = (index: number): StepStatus => {
        if (completedSteps.includes(index)) return 'completed';
        if (index === currentStep) return 'current';
        return 'pending';
    };

    return (
        <div className="w-full">
            {/* Desktop view */}
            <div className="hidden md:flex items-center justify-between relative">
                {/* Progress line */}
                <div className="absolute top-6 left-0 right-0 h-0.5 bg-white/10" />
                <div
                    className="absolute top-6 left-0 h-0.5 transition-all duration-500"
                    style={{
                        width: `${(currentStep / (steps.length - 1)) * 100}%`,
                        background: theme.gradients.primary,
                        boxShadow: theme.glow.cyan,
                    }}
                />

                {steps.map((step, index) => {
                    const status = getStepStatus(index);
                    const isClickable = status === 'completed' || index <= currentStep;

                    return (
                        <div
                            key={step.id}
                            className="relative z-10 flex flex-col items-center"
                            style={{ width: `${100 / steps.length}%` }}
                        >
                            <button
                                onClick={() => isClickable && onStepClick?.(index)}
                                disabled={!isClickable}
                                className={cn(
                                    'w-12 h-12 rounded-full flex items-center justify-center text-lg transition-all duration-300',
                                    'border-2',
                                    status === 'completed' && 'border-green-500 bg-green-500/20',
                                    status === 'current' && 'border-cyan-500 bg-cyan-500/20',
                                    status === 'pending' && 'border-white/20 bg-white/5',
                                    isClickable && 'cursor-pointer hover:scale-110',
                                    !isClickable && 'cursor-not-allowed opacity-50'
                                )}
                                style={
                                    status === 'current'
                                        ? { boxShadow: theme.glow.cyan }
                                        : status === 'completed'
                                            ? { boxShadow: theme.glow.green }
                                            : undefined
                                }
                            >
                                {status === 'completed' ? (
                                    <Check className="w-6 h-6 text-green-400" />
                                ) : (
                                    <span>{step.icon}</span>
                                )}
                            </button>

                            <span
                                className={cn(
                                    'mt-2 text-sm font-medium text-center',
                                    status === 'current' && 'text-cyan-400',
                                    status === 'completed' && 'text-green-400',
                                    status === 'pending' && 'text-gray-500'
                                )}
                            >
                                {step.name}
                            </span>
                        </div>
                    );
                })}
            </div>

            {/* Mobile view - compact */}
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
