'use client';

import { type ReactNode, useEffect, useMemo, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';

import { getAuthStatus } from '@/lib/api';
import { buildLoginHref, DEFAULT_AUTHENTICATED_PATH } from '@/lib/routing';

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
                    return;
                }

                router.replace(buildLoginHref(nextPath));
            } catch (error) {
                if (cancelled) {
                    return;
                }

                setErrorMessage(getErrorMessage(error));
            }
        }

        void verifyAuth();

        return () => {
            cancelled = true;
        };
    }, [nextPath, router]);

    if (errorMessage) {
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
