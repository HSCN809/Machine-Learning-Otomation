'use client';

import { useEffect, useRef, useState } from 'react';
import { Grip, History, X } from 'lucide-react';
import { PixelTrail } from '@/components/common';
import { theme } from '@/styles/theme';
import { useDatasetTimeline } from '@/hooks/useDatasetTimeline';
import { TimelineLog } from './TimelineLog';

interface TimelineDrawerLauncherProps {
    visible?: boolean;
    enabled?: boolean;
    onAfterUndo?: () => Promise<void> | void;
}

export function TimelineDrawerLauncher({
    visible = true,
    enabled = true,
    onAfterUndo,
}: TimelineDrawerLauncherProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [buttonPosition, setButtonPosition] = useState(() => {
        if (typeof window === 'undefined') {
            return { x: 16, y: 16 };
        }

        return {
            x: window.innerWidth - 96,
            y: window.innerHeight - 120,
        };
    });
    const [trailPointer, setTrailPointer] = useState<{ x: number; y: number } | null>(null);
    const [isDragging, setIsDragging] = useState(false);
    const dragOffsetRef = useRef({ x: 0, y: 0 });
    const dragStartRef = useRef({ x: 0, y: 0 });
    const didDragRef = useRef(false);
    const { events, count, canUndoLast, isLoading, undoLast } = useDatasetTimeline({ enabled });

    useEffect(() => {
        if (!isOpen) {
            return;
        }

        const previousBodyOverflow = document.body.style.overflow;
        const previousHtmlOverflow = document.documentElement.style.overflow;

        document.body.style.overflow = 'hidden';
        document.documentElement.style.overflow = 'hidden';

        return () => {
            document.body.style.overflow = previousBodyOverflow;
            document.documentElement.style.overflow = previousHtmlOverflow;
        };
    }, [isOpen]);

    if (!visible) {
        return null;
    }

    const handlePointerDown = (event: React.PointerEvent<HTMLButtonElement>) => {
        const rect = event.currentTarget.getBoundingClientRect();
        dragStartRef.current = { x: event.clientX, y: event.clientY };
        didDragRef.current = false;
        setTrailPointer({ x: event.clientX, y: event.clientY });
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
                setIsDragging(true);
            }

            setTrailPointer({ x: moveEvent.clientX, y: moveEvent.clientY });
            const nextX = Math.min(
                Math.max(16, moveEvent.clientX - dragOffsetRef.current.x),
                window.innerWidth - buttonSize - 16
            );
            const nextY = Math.min(
                Math.max(16, moveEvent.clientY - dragOffsetRef.current.y),
                window.innerHeight - buttonSize - 16
            );

            setButtonPosition({ x: nextX, y: nextY });
        };

        const handlePointerUp = () => {
            setIsDragging(false);
            window.removeEventListener('pointermove', handlePointerMove);
            window.removeEventListener('pointerup', handlePointerUp);
        };

        window.addEventListener('pointermove', handlePointerMove);
        window.addEventListener('pointerup', handlePointerUp);
    };

    const handleButtonClick = () => {
        if (didDragRef.current) {
            didDragRef.current = false;
            return;
        }

        setIsOpen(true);
    };

    const handleUndoLast = async () => {
        const isUndone = await undoLast();
        if (!isUndone) {
            return;
        }

        await onAfterUndo?.();
    };

    return (
        <>
            <PixelTrail
                active={isDragging}
                pointer={trailPointer}
                color={theme.colors.primary.cyan}
                gridSize={22}
                trailSize={0.55}
                maxAge={320}
                interpolate={10}
            />
            <button
                type="button"
                aria-label="İşlem zaman akışını aç"
                onPointerDown={handlePointerDown}
                onClick={handleButtonClick}
                className="fixed z-40 flex h-14 w-14 cursor-grab items-center justify-center rounded-full border border-cyan-400/30 bg-slate-900/90 text-cyan-300 shadow-lg backdrop-blur transition-transform hover:scale-105 active:cursor-grabbing"
                style={{
                    left: buttonPosition.x,
                    top: buttonPosition.y,
                    boxShadow: theme.glow.cyanStrong,
                }}
            >
                <History className="h-5 w-5" />
                <span className="pointer-events-none absolute -bottom-1 -right-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-cyan-500 px-1 text-[10px] font-semibold text-slate-950">
                    {count}
                </span>
                <span className="pointer-events-none absolute -top-1 -left-1 rounded-full border border-white/10 bg-slate-950/90 p-1 text-gray-400">
                    <Grip className="h-3 w-3" />
                </span>
            </button>

            <div
                className={`fixed inset-0 z-40 bg-slate-950/40 backdrop-blur-sm transition-opacity duration-300 ${isOpen ? 'pointer-events-auto opacity-100' : 'pointer-events-none opacity-0'}`}
                onClick={() => setIsOpen(false)}
            />

            <aside
                className={`fixed right-0 top-0 z-50 h-screen w-full max-w-md border-l border-white/10 bg-[#0D1528]/95 shadow-2xl backdrop-blur-xl transition-transform duration-300 ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}
            >
                <div className="flex h-full flex-col overflow-y-auto">
                    <div className="flex items-start justify-between border-b border-white/10 px-5 py-5">
                        <div>
                            <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-400/80">
                                Geçmiş
                            </p>
                            <h3 className="mt-1 text-xl font-semibold text-white">İşlem Timeline</h3>
                            <p className="mt-1 text-sm text-gray-400">
                                Veri yükleme, düzenleme, ön işleme ve model seçimi işlemlerini kronolojik görüntüleyin.
                            </p>
                        </div>
                        <button
                            type="button"
                            onClick={() => setIsOpen(false)}
                            className="flex h-10 w-10 cursor-pointer items-center justify-center rounded-full border border-white/10 bg-white/5 text-gray-300 transition-colors hover:bg-white/10 hover:text-white"
                            aria-label="İşlem zaman akışını kapat"
                        >
                            <X className="h-5 w-5" />
                        </button>
                    </div>

                    <div className="p-5">
                        <TimelineLog
                            events={events}
                            canUndoLast={canUndoLast}
                            isLoading={isLoading}
                            onUndoLast={() => void handleUndoLast()}
                        />
                    </div>
                </div>
            </aside>
        </>
    );
}
