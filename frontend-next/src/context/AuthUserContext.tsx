'use client';

import {
    createContext,
    type ReactNode,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useState,
} from 'react';
import { usePathname } from 'next/navigation';

import { checkBackendHealth, getAuthStatus, type AuthUser } from '@/lib/api';
import { logger } from '@/lib/logger';
import { notify } from '@/lib/notify';
import { isProtectedPath } from '@/lib/routing';

type AuthResolutionStatus = 'idle' | 'loading' | 'authenticated' | 'unauthenticated' | 'error';

interface AuthUserContextValue {
    currentUser: AuthUser | null;
    status: AuthResolutionStatus;
    errorMessage: string;
    isLoading: boolean;
    refreshAuth: () => Promise<void>;
}

const AuthUserContext = createContext<AuthUserContextValue | undefined>(undefined);

function getErrorMessage(error: unknown): string {
    if (error instanceof Error && error.message) {
        return error.message;
    }

    return 'Auth state could not be resolved. Please try again.';
}

export function AuthUserProvider({ children }: { children: ReactNode }) {
    const pathname = usePathname();
    const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
    const [status, setStatus] = useState<AuthResolutionStatus>('idle');
    const [errorMessage, setErrorMessage] = useState('');

    const refreshAuth = useCallback(async () => {
        setStatus('loading');
        setErrorMessage('');

        for (let attempt = 0; attempt < 3; attempt++) {
            try {
                if (attempt === 0 && !(await checkBackendHealth())) {
                    await new Promise((r) => setTimeout(r, 1000));
                    continue;
                }

                const response = await getAuthStatus();

                if (response.authenticated && response.user) {
                    setCurrentUser(response.user);
                    setStatus('authenticated');
                    return;
                }

                setCurrentUser(null);
                setStatus('unauthenticated');
                return;
            } catch (error) {
                logger.error('Auth refresh failed', error);
                if (attempt < 2) {
                    await new Promise((r) => setTimeout(r, 1000 * Math.pow(2, attempt)));
                    continue;
                }
                setCurrentUser(null);
                setErrorMessage(getErrorMessage(error));
                setStatus('error');
                notify.error(error, 'Oturum durumu kontrol edilemedi');
            }
        }
    }, []);

    useEffect(() => {
        if (!pathname || !isProtectedPath(pathname)) {
            return;
        }

        if (status === 'idle') {
            const timerId = window.setTimeout(() => {
                void refreshAuth();
            }, 0);

            return () => {
                window.clearTimeout(timerId);
            };
        }
    }, [pathname, refreshAuth, status]);

    useEffect(() => {
        function handleUserUpdated(event: Event) {
            const customEvent = event as CustomEvent<AuthUser>;
            if (customEvent.detail) {
                setCurrentUser(customEvent.detail);
                setStatus('authenticated');
                setErrorMessage('');
            }
        }

        function handleLogout() {
            setCurrentUser(null);
            setStatus('unauthenticated');
            setErrorMessage('');
        }

        window.addEventListener('auth:user-updated', handleUserUpdated as EventListener);
        window.addEventListener('auth:logged-out', handleLogout);

        return () => {
            window.removeEventListener('auth:user-updated', handleUserUpdated as EventListener);
            window.removeEventListener('auth:logged-out', handleLogout);
        };
    }, []);

    const value = useMemo<AuthUserContextValue>(
        () => ({
            currentUser,
            status,
            errorMessage,
            isLoading: status === 'loading',
            refreshAuth,
        }),
        [currentUser, errorMessage, refreshAuth, status]
    );

    return <AuthUserContext.Provider value={value}>{children}</AuthUserContext.Provider>;
}

export function useAuthUserContext(): AuthUserContextValue {
    const context = useContext(AuthUserContext);
    if (!context) {
        throw new Error('useAuthUserContext must be used within an AuthUserProvider');
    }
    return context;
}
