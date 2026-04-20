'use client';

import { type ReactNode, useEffect, useMemo } from 'react';
import { usePathname, useRouter } from 'next/navigation';

import { useAuthUserContext } from '@/context/AuthUserContext';
import { buildLoginHref, DEFAULT_AUTHENTICATED_PATH } from '@/lib/routing';

interface ProtectedRouteBoundaryProps {
    children: ReactNode;
}

export function ProtectedRouteBoundary({ children }: ProtectedRouteBoundaryProps) {
    const router = useRouter();
    const pathname = usePathname();
    const { status, errorMessage } = useAuthUserContext();

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
        if (status === 'unauthenticated') {
            router.replace(buildLoginHref(nextPath));
        }
    }, [nextPath, router, status]);

    if (errorMessage) {
        return (
            <div className="min-h-screen bg-[#07101f] p-6">
                <div className="mx-auto max-w-2xl rounded-3xl border border-red-400/20 bg-red-500/10 p-6 text-sm text-red-100">
                    {errorMessage}
                </div>
            </div>
        );
    }

    if (status === 'idle' || status === 'loading' || status === 'unauthenticated') {
        return null;
    }

    return <>{children}</>;
}
