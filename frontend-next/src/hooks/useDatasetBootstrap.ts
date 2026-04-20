'use client';

import { useEffect, useState, useSyncExternalStore } from 'react';
import { hasStoredSession, subscribeToStoredSession } from '@/lib/api';

export type DatasetBootstrapStatus = 'checking' | 'ready' | 'empty' | 'error';

interface UseDatasetBootstrapResult {
    status: DatasetBootstrapStatus;
    isChecking: boolean;
    isReady: boolean;
    isEmpty: boolean;
    isError: boolean;
}

export function useDatasetBootstrap(loader: () => Promise<unknown>): UseDatasetBootstrapResult {
    const hasSessionPointer = useSyncExternalStore<boolean | null>(
        subscribeToStoredSession,
        hasStoredSession,
        () => null
    );
    const [status, setStatus] = useState<DatasetBootstrapStatus>('checking');

    useEffect(() => {
        let cancelled = false;

        async function bootstrapDataset() {
            if (hasSessionPointer === null) {
                setStatus('checking');
                return;
            }

            if (!hasSessionPointer) {
                setStatus('empty');
                return;
            }

            setStatus('checking');

            try {
                await loader();
                if (!cancelled) {
                    setStatus(hasStoredSession() ? 'ready' : 'empty');
                }
            } catch {
                if (!cancelled) {
                    setStatus('error');
                }
            }
        }

        void bootstrapDataset();

        return () => {
            cancelled = true;
        };
    }, [hasSessionPointer, loader]);

    return {
        status,
        isChecking: status === 'checking',
        isReady: status === 'ready',
        isEmpty: status === 'empty',
        isError: status === 'error',
    };
}
