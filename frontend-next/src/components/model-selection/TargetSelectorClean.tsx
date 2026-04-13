'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { ProblemType } from '@/types/model-selection';
import { cn } from '@/lib/utils';
import { theme } from '@/styles/theme';

interface TargetSelectorProps {
    columns: { name: string; type: string; uniqueValues: number }[];
    selectedColumn: string | null;
    problemType: ProblemType | null;
    onSelect: (column: string) => void;
    onProblemTypeChange: (problemType: ProblemType) => void;
    disabled?: boolean;
}

const EXIT_DURATION_MS = 150;
const ENTER_DURATION_MS = 220;

export function TargetSelectorClean({
    columns,
    selectedColumn,
    problemType,
    onSelect,
    onProblemTypeChange,
    disabled = false,
}: TargetSelectorProps) {
    const hasColumns = columns.length > 0;
    const selectedIndex = columns.findIndex((column) => column.name === selectedColumn);
    const currentIndex = hasColumns && selectedIndex >= 0 ? selectedIndex : 0;
    const [animatedIndex, setAnimatedIndex] = useState(currentIndex);
    const [phase, setPhase] = useState<'idle' | 'exit' | 'enter'>('idle');
    const [direction, setDirection] = useState<'forward' | 'backward'>('forward');
    const exitTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const enterTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const isAnimating = phase !== 'idle';
    const visibleIndex = isAnimating ? animatedIndex : currentIndex;

    const clearAnimationTimers = useCallback(() => {
        if (exitTimerRef.current) {
            clearTimeout(exitTimerRef.current);
            exitTimerRef.current = null;
        }

        if (enterTimerRef.current) {
            clearTimeout(enterTimerRef.current);
            enterTimerRef.current = null;
        }
    }, []);

    const handleSelectColumn = useCallback(
        (index: number, nextDirection: 'forward' | 'backward') => {
            if (disabled || columns.length === 0 || isAnimating) {
                return;
            }

            const wrappedIndex = (index + columns.length) % columns.length;
            const nextColumn = columns[wrappedIndex];

            if (!nextColumn || wrappedIndex === visibleIndex) {
                return;
            }

            clearAnimationTimers();
            setDirection(nextDirection);
            setPhase('exit');

            exitTimerRef.current = setTimeout(() => {
                setAnimatedIndex(wrappedIndex);
                onSelect(nextColumn.name);
                setPhase('enter');

                enterTimerRef.current = setTimeout(() => {
                    setPhase('idle');
                }, ENTER_DURATION_MS);
            }, EXIT_DURATION_MS);
        },
        [clearAnimationTimers, columns, disabled, isAnimating, onSelect, visibleIndex]
    );

    const handlePrevious = useCallback(() => {
        handleSelectColumn(visibleIndex - 1, 'backward');
    }, [handleSelectColumn, visibleIndex]);

    const handleNext = useCallback(() => {
        handleSelectColumn(visibleIndex + 1, 'forward');
    }, [handleSelectColumn, visibleIndex]);

    const stageClassName = cn(
        'target-selector-stage',
        phase !== 'idle' && `is-${phase}`,
        `is-${direction}`
    );

    useEffect(() => {
        if (!hasColumns || disabled) {
            return;
        }

        const handleWindowKeyDown = (event: KeyboardEvent) => {
            const target = event.target as HTMLElement | null;
            const isEditableTarget =
                target instanceof HTMLInputElement ||
                target instanceof HTMLTextAreaElement ||
                target instanceof HTMLSelectElement ||
                target?.isContentEditable;

            if (isEditableTarget) {
                return;
            }

            if (isAnimating || event.altKey || event.ctrlKey || event.metaKey) {
                return;
            }

            if (event.key === 'ArrowLeft') {
                event.preventDefault();
                handlePrevious();
            }

            if (event.key === 'ArrowRight') {
                event.preventDefault();
                handleNext();
            }
        };

        window.addEventListener('keydown', handleWindowKeyDown);

        return () => {
            window.removeEventListener('keydown', handleWindowKeyDown);
        };
    }, [disabled, handleNext, handlePrevious, hasColumns, isAnimating]);

    useEffect(() => {
        return () => {
            clearAnimationTimers();
        };
    }, [clearAnimationTimers]);

    if (!hasColumns) {
        return (
            <div className="space-y-6">
                <div className="space-y-3">
                    <div className="rounded-2xl border border-white/10 bg-white/5 px-6 py-10 text-center text-gray-400">
                        Kullanilabilir sutun bulunamadi.
                    </div>
                </div>
            </div>
        );
    }

    const currentColumn = columns[visibleIndex]!;
    const isCurrentSelected = phase !== 'idle' || selectedColumn === currentColumn.name;
    const isNumeric = currentColumn.type === 'numeric';

    return (
        <div className="space-y-6">
            <div className="space-y-3">
                <div>
                    <h3 className="text-xl font-semibold text-white">Hedef Degisken Secimi</h3>
                    <p className="mt-1 text-sm text-gray-400">Model egitimi icin hedef kolonu belirleyin.</p>
                </div>
                <div className="mx-auto flex max-w-5xl items-center gap-3">
                    <button
                        type="button"
                        onClick={handlePrevious}
                        disabled={disabled || isAnimating}
                        aria-label="Onceki hedef degiskene gec"
                        className={cn(
                            'flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-gray-300 transition-all duration-200',
                            !disabled && 'cursor-pointer hover:border-cyan-500/30 hover:bg-white/10 hover:text-white',
                            (disabled || isAnimating) && 'cursor-not-allowed opacity-50'
                        )}
                    >
                        <ChevronLeft className="h-5 w-5" />
                    </button>

                    <div className="flex-1 overflow-hidden">
                        <button
                            key={currentColumn.name}
                            type="button"
                            disabled={disabled}
                            className={cn(
                                'w-full rounded-xl border-2 p-4 text-left transition-all duration-200 md:p-5',
                                isCurrentSelected
                                    ? 'border-cyan-500 bg-cyan-500/10'
                                    : 'border-white/10 bg-white/5 hover:border-cyan-500/30 hover:bg-white/10',
                                !disabled && 'cursor-pointer',
                                disabled && 'cursor-not-allowed opacity-50',
                                stageClassName
                            )}
                            style={isCurrentSelected ? { boxShadow: theme.glow.cyan } : undefined}
                        >
                            <div className="flex items-start justify-between gap-4">
                                <div>
                                    <p
                                        className={cn(
                                            'text-2xl font-semibold tracking-tight md:text-[2rem]',
                                            isCurrentSelected ? 'text-cyan-400' : 'text-white'
                                        )}
                                    >
                                        {currentColumn.name}
                                    </p>
                                    <div className="mt-3 flex flex-wrap items-center gap-2.5 text-sm">
                                        <span
                                            className={cn(
                                                'rounded-full px-3 py-1',
                                                isNumeric ? 'bg-blue-500/20 text-blue-400' : 'bg-green-500/20 text-green-400'
                                            )}
                                        >
                                            {isNumeric ? 'Sayisal' : 'Kategorik'}
                                        </span>
                                        <span className="text-gray-400">{currentColumn.uniqueValues} unique</span>
                                        <span className="text-gray-500">
                                            {visibleIndex + 1} / {columns.length}
                                        </span>
                                    </div>
                                </div>

                                {isCurrentSelected && <span className="text-xl text-cyan-400">✓</span>}
                            </div>
                        </button>
                    </div>

                    <button
                        type="button"
                        onClick={handleNext}
                        disabled={disabled || isAnimating}
                        aria-label="Sonraki hedef degiskene gec"
                        className={cn(
                            'flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-gray-300 transition-all duration-200',
                            !disabled && 'cursor-pointer hover:border-cyan-500/30 hover:bg-white/10 hover:text-white',
                            (disabled || isAnimating) && 'cursor-not-allowed opacity-50'
                        )}
                    >
                        <ChevronRight className="h-5 w-5" />
                    </button>
                </div>
            </div>

            {selectedColumn && (
                <div className="mx-auto max-w-5xl">
                    <div className="space-y-3 rounded-xl border border-white/10 bg-white/5 p-6 animate-fadeIn">
                        <div>
                            <h3 className="text-xl font-semibold text-white">Problem Secimi</h3>
                            <p className="mt-1 text-sm text-gray-400">Bu hedef kolon icin problem turunu manuel olarak secin.</p>
                        </div>
                        <div className="grid gap-4 md:grid-cols-2">
                            <button
                                type="button"
                                onClick={() => onProblemTypeChange('classification')}
                                disabled={disabled}
                                className={cn(
                                    'rounded-xl border p-5 text-left transition-all duration-200',
                                    problemType === 'classification'
                                        ? 'border-emerald-400 bg-emerald-500/10'
                                        : 'border-white/10 bg-transparent hover:border-emerald-400/40 hover:bg-white/5',
                                    disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'
                                )}
                            >
                                <div className="mb-3 flex items-center justify-between gap-3">
                                    <div>
                                        <p className="text-lg font-semibold text-white">Siniflandirma</p>
                                        <p className="mt-1 text-sm text-gray-400">
                                            Ayrik siniflar veya kategoriler icin classifier modelleri kullanir.
                                        </p>
                                    </div>
                                    <span
                                        className={cn(
                                            'flex h-6 w-6 items-center justify-center rounded border text-sm',
                                            problemType === 'classification'
                                                ? 'border-emerald-400 bg-emerald-400 text-slate-950'
                                                : 'border-white/20 text-transparent'
                                        )}
                                    >
                                        ✓
                                    </span>
                                </div>
                            </button>

                            <button
                                type="button"
                                onClick={() => onProblemTypeChange('regression')}
                                disabled={disabled}
                                className={cn(
                                    'rounded-xl border p-5 text-left transition-all duration-200',
                                    problemType === 'regression'
                                        ? 'border-cyan-400 bg-cyan-500/10'
                                        : 'border-white/10 bg-transparent hover:border-cyan-400/40 hover:bg-white/5',
                                    disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'
                                )}
                            >
                                <div className="mb-3 flex items-center justify-between gap-3">
                                    <div>
                                        <p className="text-lg font-semibold text-white">Regresyon</p>
                                        <p className="mt-1 text-sm text-gray-400">
                                            Sayisal hedefler icin regression modelleri kullanir.
                                        </p>
                                    </div>
                                    <span
                                        className={cn(
                                            'flex h-6 w-6 items-center justify-center rounded border text-sm',
                                            problemType === 'regression'
                                                ? 'border-cyan-400 bg-cyan-400 text-slate-950'
                                                : 'border-white/20 text-transparent'
                                        )}
                                    >
                                        ✓
                                    </span>
                                </div>
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <style jsx>{`
                .target-selector-stage {
                    will-change: transform, opacity;
                }

                .target-selector-stage.is-exit {
                    opacity: 0;
                    transition: opacity ${EXIT_DURATION_MS}ms ease, transform ${EXIT_DURATION_MS}ms ease;
                }

                .target-selector-stage.is-exit.is-forward {
                    transform: translateX(-48px);
                }

                .target-selector-stage.is-exit.is-backward {
                    transform: translateX(48px);
                }

                .target-selector-stage.is-enter.is-forward {
                    animation: target-slide-in-from-right ${ENTER_DURATION_MS}ms ease both;
                }

                .target-selector-stage.is-enter.is-backward {
                    animation: target-slide-in-from-left ${ENTER_DURATION_MS}ms ease both;
                }

                @keyframes target-slide-in-from-right {
                    from {
                        opacity: 0;
                        transform: translateX(64px);
                    }
                    to {
                        opacity: 1;
                        transform: translateX(0);
                    }
                }

                @keyframes target-slide-in-from-left {
                    from {
                        opacity: 0;
                        transform: translateX(-64px);
                    }
                    to {
                        opacity: 1;
                        transform: translateX(0);
                    }
                }
            `}</style>
        </div>
    );
}
