'use client';

import { ReactNode, useEffect, useMemo, useRef, useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { theme } from '@/styles/theme';

interface ChartSlide {
    id: string;
    label: string;
    content: ReactNode;
}

interface ChartCarouselProps {
    slides: ChartSlide[];
    className?: string;
}

const EXIT_DURATION_MS = 180;
const ENTER_DURATION_MS = 260;

export function ChartCarousel({ slides, className }: ChartCarouselProps) {
    const [activeIndex, setActiveIndex] = useState(0);
    const [phase, setPhase] = useState<'idle' | 'exit' | 'enter'>('idle');
    const [direction, setDirection] = useState<'forward' | 'backward'>('forward');
    const exitTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const enterTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    useEffect(() => {
        return () => {
            if (exitTimerRef.current) {
                clearTimeout(exitTimerRef.current);
            }
            if (enterTimerRef.current) {
                clearTimeout(enterTimerRef.current);
            }
        };
    }, []);

    useEffect(() => {
        if (slides.length === 0) {
            setActiveIndex(0);
            return;
        }

        if (activeIndex >= slides.length) {
            setActiveIndex(0);
        }
    }, [activeIndex, slides.length]);

    const currentSlide = slides[activeIndex];
    const isAnimating = phase !== 'idle';
    const showNavigation = slides.length > 1;

    const stageClassName = useMemo(
        () =>
            cn(
                'chart-carousel-stage',
                phase !== 'idle' && `is-${phase}`,
                direction === 'forward' ? 'is-forward' : 'is-backward'
            ),
        [direction, phase]
    );

    const goToSlide = (nextIndex: number, nextDirection: 'forward' | 'backward') => {
        if (slides.length <= 1 || isAnimating || nextIndex === activeIndex) {
            return;
        }

        setDirection(nextDirection);
        setPhase('exit');

        exitTimerRef.current = setTimeout(() => {
            setActiveIndex(nextIndex);
            setPhase('enter');

            enterTimerRef.current = setTimeout(() => {
                setPhase('idle');
            }, ENTER_DURATION_MS);
        }, EXIT_DURATION_MS);
    };

    const handlePrevious = () => {
        const nextIndex = (activeIndex - 1 + slides.length) % slides.length;
        goToSlide(nextIndex, 'backward');
    };

    const handleNext = () => {
        const nextIndex = (activeIndex + 1) % slides.length;
        goToSlide(nextIndex, 'forward');
    };

    if (!currentSlide) {
        return null;
    }

    return (
        <div className={cn('space-y-4', className)}>
            <div
                className="flex items-center justify-between gap-3 rounded-xl border border-white/10 px-4 py-3"
                style={{
                    background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.45) 0%, rgba(31, 41, 55, 0.25) 100%)',
                }}
            >
                <div>
                    <p className="text-xs uppercase tracking-[0.24em] text-cyan-300/70">Grafik Görünümü</p>
                    <p className="text-sm font-medium text-white">{currentSlide.label}</p>
                </div>

                <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-400">
                        {activeIndex + 1} / {slides.length}
                    </span>
                    <button
                        type="button"
                        onClick={handlePrevious}
                        disabled={!showNavigation || isAnimating}
                        className="flex h-10 w-10 cursor-pointer items-center justify-center rounded-xl border border-white/10 bg-white/5 text-gray-300 transition-all duration-200 hover:border-cyan-400/40 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
                        aria-label="Önceki grafik"
                    >
                        <ChevronLeft className="h-5 w-5" />
                    </button>
                    <button
                        type="button"
                        onClick={handleNext}
                        disabled={!showNavigation || isAnimating}
                        className="flex h-10 w-10 cursor-pointer items-center justify-center rounded-xl border border-white/10 bg-white/5 text-gray-300 transition-all duration-200 hover:border-cyan-400/40 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
                        aria-label="Sonraki grafik"
                    >
                        <ChevronRight className="h-5 w-5" />
                    </button>
                </div>
            </div>

            <div className="overflow-hidden">
                <div className={stageClassName}>
                    {currentSlide.content}
                </div>
            </div>

            <style jsx>{`
                .chart-carousel-stage {
                    will-change: transform, opacity;
                }

                .chart-carousel-stage.is-exit {
                    opacity: 0;
                    transition: opacity ${EXIT_DURATION_MS}ms ease, transform ${EXIT_DURATION_MS}ms ease;
                }

                .chart-carousel-stage.is-exit.is-forward {
                    transform: translateX(-56px);
                }

                .chart-carousel-stage.is-exit.is-backward {
                    transform: translateX(56px);
                }

                .chart-carousel-stage.is-enter.is-forward {
                    animation: slide-in-from-right ${ENTER_DURATION_MS}ms ease both;
                }

                .chart-carousel-stage.is-enter.is-backward {
                    animation: slide-in-from-left ${ENTER_DURATION_MS}ms ease both;
                }

                @keyframes slide-in-from-right {
                    from {
                        opacity: 0;
                        transform: translateX(72px);
                    }
                    to {
                        opacity: 1;
                        transform: translateX(0);
                    }
                }

                @keyframes slide-in-from-left {
                    from {
                        opacity: 0;
                        transform: translateX(-72px);
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
