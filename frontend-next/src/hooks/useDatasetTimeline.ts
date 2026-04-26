'use client';

import { useCallback, useEffect, useState } from 'react';
import * as api from '@/lib/api';
import type { TimelineEvent } from '@/types/timeline';
import { logger } from '@/lib/logger';
import { getErrorMessage, notify } from '@/lib/notify';

interface UseDatasetTimelineReturn {
    events: TimelineEvent[];
    count: number;
    canUndoLast: boolean;
    lastEventId: string | null;
    isLoading: boolean;
    error: string | null;
    refresh: () => Promise<void>;
    undoLast: () => Promise<boolean>;
}

export function useDatasetTimeline(): UseDatasetTimelineReturn {
    const [events, setEvents] = useState<TimelineEvent[]>([]);
    const [canUndoLast, setCanUndoLast] = useState(false);
    const [lastEventId, setLastEventId] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const refresh = useCallback(async () => {
        if (!api.hasStoredSession()) {
            setEvents([]);
            setCanUndoLast(false);
            setLastEventId(null);
            setError(null);
            setIsLoading(false);
            return;
        }

        try {
            setIsLoading(true);
            setError(null);
            const response = await api.getTimeline();
            setEvents(response.events);
            setCanUndoLast(response.canUndoLast);
            setLastEventId(response.lastEventId ?? null);
        } catch (err) {
            if (api.isSessionRequiredError(err)) {
                setEvents([]);
                setCanUndoLast(false);
                setLastEventId(null);
                setError(null);
                return;
            }

            logger.error('Dataset timeline load failed', err);
            setError(getErrorMessage(err, 'Islem zaman akisi yuklenemedi'));
        } finally {
            setIsLoading(false);
        }
    }, []);

    const undoLast = useCallback(async () => {
        if (!canUndoLast) {
            return false;
        }

        try {
            setIsLoading(true);
            setError(null);
            await api.undoLastTimelineEvent();
            await refresh();
            notify.success('Son islem geri alindi');
            return true;
        } catch (err) {
            const message = getErrorMessage(err, 'Son islem geri alinamadi');
            logger.error('Dataset timeline undo failed', err);
            setError(message);
            notify.error(err, 'Son islem geri alinamadi');
            return false;
        } finally {
            setIsLoading(false);
        }
    }, [canUndoLast, refresh]);

    useEffect(() => {
        void refresh();
    }, [refresh]);

    useEffect(() => api.subscribeToStoredSession(() => {
        void refresh();
    }), [refresh]);

    return {
        events,
        count: events.length,
        canUndoLast,
        lastEventId,
        isLoading,
        error,
        refresh,
        undoLast,
    };
}
