'use client';

import { useEffect, useRef, useState } from 'react';
import { Grip, History, X } from 'lucide-react';
import { PixelTrail } from '@/components/common';
import { theme } from '@/styles/theme';
import { notify } from '@/lib/notify';
import { useDatasetTimeline } from '@/hooks/useDatasetTimeline';
import type { TimelineEvent, TimelineRollbackPlan } from '@/types/timeline';
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
    const [rollbackPlan, setRollbackPlan] = useState<TimelineRollbackPlan | null>(null);
    const [isRollbackPlanLoading, setIsRollbackPlanLoading] = useState(false);
    const [isRollbackApplying, setIsRollbackApplying] = useState(false);
    const dragOffsetRef = useRef({ x: 0, y: 0 });
    const dragStartRef = useRef({ x: 0, y: 0 });
    const didDragRef = useRef(false);
    const {
        events,
        canUndoLast,
        isLoading,
        undoLast,
        getRollbackPlan,
        rollbackEvent,
    } = useDatasetTimeline({ enabled });
    const visibleEvents = events.filter((event) => event.category !== 'model');

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

    const handleRollbackRequest = async (event: TimelineEvent) => {
        setIsRollbackPlanLoading(true);
        const plan = await getRollbackPlan(event.id);
        setIsRollbackPlanLoading(false);
        if (!plan) {
            return;
        }
        if (plan.unsupportedReplayEvents.length > 0) {
            notify.warning('Bu işlem geri alınamaz. Timeline içinde yeniden oynatılamayan eski formatlı kayıt var.');
        }
        setRollbackPlan(plan);
    };

    const handleConfirmRollback = async () => {
        if (!rollbackPlan || !rollbackPlan.canRollback) {
            return;
        }

        setIsRollbackApplying(true);
        const isRolledBack = await rollbackEvent(rollbackPlan.eventId);
        setIsRollbackApplying(false);
        if (!isRolledBack) {
            return;
        }

        setRollbackPlan(null);
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
                    {visibleEvents.length}
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
                                Veri yükleme, düzenleme ve ön işleme işlemlerini kronolojik görüntüleyin.
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
                            events={visibleEvents}
                            canUndoLast={canUndoLast}
                            isLoading={isLoading || isRollbackPlanLoading || isRollbackApplying}
                            onUndoLast={() => void handleUndoLast()}
                            onRollbackEvent={(event) => void handleRollbackRequest(event)}
                        />
                    </div>
                </div>
            </aside>

            {rollbackPlan && (
                <div className="fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/70 px-4 backdrop-blur-sm">
                    <div className="w-full max-w-lg rounded-2xl border border-white/10 bg-[#0D1528] p-5 shadow-2xl">
                        <div className="flex items-start justify-between gap-4">
                            <div>
                                <p className="text-sm font-medium uppercase tracking-[0.2em] text-cyan-400/80">
                                    Geri alma
                                </p>
                                <h3 className="mt-1 text-xl font-semibold text-white">İşlem geri alınacak</h3>
                                <p className="mt-2 text-sm text-gray-400">
                                    Seçilen işlem ve ona bağlı sonraki işlemler pasif hale getirilecek. Bağımsız işlemler korunacak.
                                </p>
                            </div>
                            <button
                                type="button"
                                onClick={() => setRollbackPlan(null)}
                                className="flex h-9 w-9 cursor-pointer items-center justify-center rounded-full border border-white/10 bg-white/5 text-gray-300 transition-colors hover:bg-white/10 hover:text-white"
                                aria-label="Geri alma penceresini kapat"
                            >
                                <X className="h-4 w-4" />
                            </button>
                        </div>

                        <div className="mt-5 space-y-3 text-sm">
                            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
                                <p className="text-xs uppercase tracking-[0.16em] text-gray-500">Seçilen işlem</p>
                                <p className="mt-1 font-medium text-white">
                                    {rollbackPlan.targetEvent.title || rollbackPlan.targetEvent.action || rollbackPlan.targetEvent.id}
                                </p>
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                                <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
                                    <p className="text-xs text-gray-500">Bağlı</p>
                                    <p className="mt-1 text-lg font-semibold text-amber-300">{rollbackPlan.dependentEvents.length}</p>
                                </div>
                                <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
                                    <p className="text-xs text-gray-500">Korunan</p>
                                    <p className="mt-1 text-lg font-semibold text-emerald-300">{rollbackPlan.preservedEvents.length}</p>
                                </div>
                            </div>
                            {rollbackPlan.dependentEvents.length > 0 && (
                                <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
                                    <p className="text-xs uppercase tracking-[0.16em] text-gray-500">Pasifleşecek bağlı işlemler</p>
                                    <div className="mt-2 max-h-32 space-y-1 overflow-y-auto">
                                        {rollbackPlan.dependentEvents.map((event) => (
                                            <p key={event.id} className="truncate text-gray-300">
                                                {event.title || event.action || event.id}
                                            </p>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="mt-5 flex justify-end gap-3">
                            <button
                                type="button"
                                onClick={() => setRollbackPlan(null)}
                                className="cursor-pointer rounded-lg border border-white/10 px-4 py-2 text-sm text-gray-300 transition-colors hover:bg-white/10 hover:text-white"
                            >
                                İptal
                            </button>
                            <button
                                type="button"
                                onClick={() => void handleConfirmRollback()}
                                disabled={!rollbackPlan.canRollback || isRollbackApplying}
                                className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                                    !rollbackPlan.canRollback || isRollbackApplying
                                        ? 'cursor-not-allowed bg-gray-700 text-gray-400'
                                        : 'cursor-pointer bg-cyan-400 text-slate-950 hover:bg-cyan-300'
                                }`}
                            >
                                {isRollbackApplying ? 'Uygulanıyor' : 'Geri al'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
