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

import {
    ApiRequestError,
    getAuthStatus,
    getBackendHealthStatus,
    isApiRequestError,
    type AuthUser,
} from '@/lib/api';
import { logger } from '@/lib/logger';
import { notify } from '@/lib/notify';
import { isProtectedPath } from '@/lib/routing';

type AuthResolutionStatus = 'idle' | 'loading' | 'authenticated' | 'unauthenticated' | 'error';

interface AuthUserContextValue {
    currentUser: AuthUser | null;
    status: AuthResolutionStatus;
    errorMessage: string;
    errorTitle: string;
    isLoading: boolean;
    refreshAuth: () => Promise<void>;
}

const AuthUserContext = createContext<AuthUserContextValue | undefined>(undefined);

function getErrorLogContext(error: unknown): Record<string, unknown> {
    if (error instanceof Error) {
        return {
            name: error.name,
            message: error.message,
        };
    }

    return { error };
}

function getAuthFailureContent(error: unknown): { title: string; description: string } {
    if (isApiRequestError(error)) {
        if (error.endpoint === '/api/auth/status' && (error.status === 404 || error.status === 503)) {
            return {
                title: 'Uygulama ara katmanı erişilemiyor',
                description: 'Auth kontrol isteği proxy katmanında cevap vermedi. Nginx veya yönlendirme ayarlarını kontrol edin.',
            };
        }

        if (error.kind === 'proxy_unavailable') {
            return {
                title: 'Uygulama ara katmanı erişilemiyor',
                description: 'API yönlendirmesi şu anda cevap vermiyor. Reverse proxy servisini kontrol edin.',
            };
        }

        if (error.kind === 'backend_unavailable' || error.kind === 'network_error') {
            return {
                title: 'Backend servisi kapalı',
                description: 'FastAPI servisine ulaşılamıyor. Backend container veya servis durumunu kontrol edin.',
            };
        }
    }

    if (error instanceof Error && error.message && error.message.trim().toLowerCase() !== 'unknown error') {
        return {
            title: 'Oturum kontrolü tamamlanamadı',
            description: error.message,
        };
    }

    return {
        title: 'Oturum kontrolü tamamlanamadı',
        description: 'Lütfen tekrar deneyin.',
    };
}

export function AuthUserProvider({ children }: { children: ReactNode }) {
    const pathname = usePathname();
    const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
    const [status, setStatus] = useState<AuthResolutionStatus>('idle');
    const [errorTitle, setErrorTitle] = useState('');
    const [errorMessage, setErrorMessage] = useState('');

    const refreshAuth = useCallback(async () => {
        setStatus('loading');
        setErrorTitle('');
        setErrorMessage('');

        for (let attempt = 0; attempt < 3; attempt++) {
            try {
                if (attempt === 0) {
                    const health = await getBackendHealthStatus();
                    if (!health.ok) {
                        throw new ApiRequestError(
                            health.kind === 'proxy_unavailable'
                                ? 'Health check proxy katmanında cevap vermedi.'
                                : 'Health check backend servisine ulaşamadı.',
                            {
                                endpoint: '/api/health',
                                kind:
                                    health.kind === 'proxy_unavailable'
                                        ? 'proxy_unavailable'
                                        : health.kind === 'backend_unavailable'
                                          ? 'backend_unavailable'
                                          : 'network_error',
                                status: health.status,
                            }
                        );
                    }
                }

                const response = await getAuthStatus();

                if (response.authenticated && response.user) {
                    setCurrentUser(response.user);
                    setStatus('authenticated');
                    setErrorTitle('');
                    setErrorMessage('');
                    return;
                }

                setCurrentUser(null);
                setStatus('unauthenticated');
                setErrorTitle('');
                setErrorMessage('');
                return;
            } catch (error) {
                if (isApiRequestError(error) && error.endpoint === '/api/auth/status' && error.status === 401) {
                    setCurrentUser(null);
                    setStatus('unauthenticated');
                    setErrorTitle('');
                    setErrorMessage('');
                    return;
                }

                logger.warn('Auth refresh failed', {
                    attempt: attempt + 1,
                    ...getErrorLogContext(error),
                });
                if (attempt < 2) {
                    await new Promise((r) => setTimeout(r, 1000 * Math.pow(2, attempt)));
                    continue;
                }
                const failure = getAuthFailureContent(error);
                setCurrentUser(null);
                setErrorTitle(failure.title);
                setErrorMessage(failure.description);
                setStatus('error');
                notify.error(new Error(failure.title), failure.title);
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
                setErrorTitle('');
                setErrorMessage('');
            }
        }

        function handleLogout() {
            setCurrentUser(null);
            setStatus('unauthenticated');
            setErrorTitle('');
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
            errorTitle,
            errorMessage,
            isLoading: status === 'loading',
            refreshAuth,
        }),
        [currentUser, errorMessage, errorTitle, refreshAuth, status]
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



