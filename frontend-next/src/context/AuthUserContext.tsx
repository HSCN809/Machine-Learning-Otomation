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

import { getCurrentUser, type AuthUser } from '@/lib/api';
import { isProtectedPath } from '@/lib/routing';

interface AuthUserContextValue {
    currentUser: AuthUser | null;
    isLoading: boolean;
    refreshCurrentUser: () => Promise<void>;
}

const AuthUserContext = createContext<AuthUserContextValue | undefined>(undefined);

export function AuthUserProvider({ children }: { children: ReactNode }) {
    const pathname = usePathname();
    const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [hasLoadedProtectedUser, setHasLoadedProtectedUser] = useState(false);

    const refreshCurrentUser = useCallback(async () => {
        try {
            setIsLoading(true);
            const response = await getCurrentUser();
            setCurrentUser(response.user);
        } catch {
            setCurrentUser(null);
        } finally {
            setHasLoadedProtectedUser(true);
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        if (!pathname || !isProtectedPath(pathname)) {
            return;
        }

        if (!hasLoadedProtectedUser || currentUser === null) {
            void refreshCurrentUser();
        }
    }, [currentUser, hasLoadedProtectedUser, pathname, refreshCurrentUser]);

    useEffect(() => {
        function handleUserUpdated(event: Event) {
            const customEvent = event as CustomEvent<AuthUser>;
            if (customEvent.detail) {
                setCurrentUser(customEvent.detail);
                setHasLoadedProtectedUser(true);
            }
        }

        function handleLogout() {
            setCurrentUser(null);
            setHasLoadedProtectedUser(false);
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
            isLoading,
            refreshCurrentUser,
        }),
        [currentUser, isLoading, refreshCurrentUser]
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
