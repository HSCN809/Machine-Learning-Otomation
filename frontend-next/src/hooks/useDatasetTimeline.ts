'use client';

import { useCallback, useEffect, useSyncExternalStore } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import * as api from '@/lib/api';
import type { TimelineEvent, TimelineRollbackPlan } from '@/types/timeline';
import { logger } from '@/lib/logger';
import { getErrorMessage, notify } from '@/lib/notify';
import { clearDatasetQueries, datasetQueryKeys, invalidateDatasetQueries } from '@/lib/query-cache';

interface UseDatasetTimelineReturn {
    events: TimelineEvent[];
    count: number;
    canUndoLast: boolean;
    lastEventId: string | null;
    isLoading: boolean;
    error: string | null;
    refresh: () => Promise<void>;
    undoLast: () => Promise<boolean>;
    getRollbackPlan: (eventId: string) => Promise<TimelineRollbackPlan | null>;
    rollbackEvent: (eventId: string) => Promise<boolean>;
}

interface UseDatasetTimelineOptions {
    enabled?: boolean;
}

export function useDatasetTimeline({
    enabled = true,
}: UseDatasetTimelineOptions = {}): UseDatasetTimelineReturn {
    const queryClient = useQueryClient();
    const sessionId = useSyncExternalStore(api.subscribeToStoredSession, api.getStoredSessionId, () => null);

    const {
        data,
        isLoading,
        error: queryError,
        refetch,
    } = useQuery({
        queryKey: datasetQueryKeys.timeline(sessionId),
        queryFn: async () => {
            if (!sessionId) {
                return { events: [] as TimelineEvent[], canUndoLast: false, lastEventId: null as string | null };
            }
            return await api.getTimeline();
        },
        enabled: enabled && Boolean(sessionId),
        staleTime: 2 * 60 * 1000, // 2 minutes
        retry: false,
    });

    const events = data?.events ?? [];
    const canUndoLast = data?.canUndoLast ?? false;
    const lastEventId = data?.lastEventId ?? null;

    const refresh = useCallback(async () => {
        if (!sessionId) {
            return;
        }
        await refetch();
    }, [refetch, sessionId]);

    const undoLast = useCallback(async () => {
        if (!canUndoLast) {
            return false;
        }

        try {
            await api.undoLastTimelineEvent();
            await invalidateDatasetQueries(queryClient);
            notify.success('Son islem geri alindi');
            return true;
        } catch (err) {
            logger.error('Dataset timeline undo failed', err);
            notify.error(err, 'Son islem geri alinamadi');
            return false;
        }
    }, [canUndoLast, queryClient]);

    const getRollbackPlan = useCallback(async (eventId: string) => {
        try {
            return await api.getTimelineRollbackPlan(eventId);
        } catch (err) {
            logger.error('Dataset timeline rollback plan failed', err);
            notify.error(err, 'Geri alma planı hazırlanamadı');
            return null;
        }
    }, []);

    const rollbackEvent = useCallback(async (eventId: string) => {
        try {
            await api.rollbackTimelineEvent(eventId);
            await invalidateDatasetQueries(queryClient);
            notify.success('Seçili işlem geri alındı');
            return true;
        } catch (err) {
            logger.error('Dataset timeline selective rollback failed', err);
            notify.error(err, 'Seçili işlem geri alınamadı');
            return false;
        }
    }, [queryClient]);

    useEffect(() => {
        return api.subscribeToStoredSession(() => {
            if (api.getStoredSessionId()) {
                void invalidateDatasetQueries(queryClient);
                return;
            }
            clearDatasetQueries(queryClient);
        });
    }, [queryClient]);

    const errorMessage = queryError && !api.isSessionRequiredError(queryError)
        ? getErrorMessage(queryError, 'Islem zaman akisi yuklenemedi')
        : null;

    return {
        events,
        count: events.length,
        canUndoLast,
        lastEventId,
        isLoading,
        error: errorMessage,
        refresh,
        undoLast,
        getRollbackPlan,
        rollbackEvent,
    };
}
