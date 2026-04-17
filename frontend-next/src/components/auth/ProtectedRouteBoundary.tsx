'use client';

import { type ReactNode, useEffect, useMemo, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';

import { getAuthStatus } from '@/lib/api';
import { DEFAULT_AUTHENTICATED_PATH, HOMEPAGE_PATH } from '@/lib/routing';

type GuardState = 'bootstrap' | 'ready' | 'error';

interface ProtectedRouteBoundaryProps {
    children: ReactNode;
}

function getErrorMessage(error: unknown): string {
    if (error instanceof Error && error.message) {
        return error.message;
    }

    return 'Oturum kontrolü tamamlanamadı. Lütfen tekrar deneyin.';
}

export function ProtectedRouteBoundary({ children }: ProtectedRouteBoundaryProps) {
    const router = useRouter();
    const pathname = usePathname();

    const [guardState, setGuardState] = useState<GuardState>('bootstrap');
    const [errorMessage, setErrorMessage] = useState('');

    const nextPath = useMemo(() => {
        if (!pathname) {
            return DEFAULT_AUTHENTICATED_PATH;
        }

        if (typeof window === 'undefined' || !window.location.search) {
            return pathname;
        }

        return `${pathname}${window.location.search}`;
    }, [pathname]);

    useEffect(() => {
        let cancelled = false;

        async function verifyAuth() {
            try {
                const status = await getAuthStatus();
                if (cancelled) {
                    return;
                }

                if (status.authenticated && status.user) {
                    setGuardState('ready');
                    return;
                }

                router.replace(HOMEPAGE_PATH);
            } catch (error) {
                if (cancelled) {
                    return;
                }

                setGuardState('error');
                setErrorMessage(getErrorMessage(error));
            }
        }

        void verifyAuth();

        return () => {
            cancelled = true;
        };
    }, [nextPath, router]);

    if (guardState === 'bootstrap') {
        return (
            <div className="min-h-screen bg-[#07101f] p-6">
                <div className="mx-auto max-w-7xl space-y-4">
                    <div className="h-16 animate-pulse rounded-2xl bg-white/5" />
                    <div className="h-[420px] animate-pulse rounded-3xl bg-white/5" />
                </div>
            </div>
        );
    }

    if (guardState === 'error') {
        return (
            <div className="min-h-screen bg-[#07101f] p-6">
                <div className="mx-auto max-w-2xl rounded-3xl border border-red-400/20 bg-red-500/10 p-6 text-sm text-red-100">
                    {errorMessage}
                </div>
            </div>
        );
    }

    return <>{children}</>;
}
