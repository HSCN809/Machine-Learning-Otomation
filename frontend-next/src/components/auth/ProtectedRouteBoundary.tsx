'use client';

import { type ReactNode, useEffect, useMemo } from 'react';
import { usePathname, useRouter } from 'next/navigation';

import { useAuthUserContext } from '@/context/AuthUserContext';
import { FullPageLoading } from '@/components/common';
import { buildLoginHref, DEFAULT_AUTHENTICATED_PATH } from '@/lib/routing';

interface ProtectedRouteBoundaryProps {
    children: ReactNode;
}

export function ProtectedRouteBoundary({ children }: ProtectedRouteBoundaryProps) {
    const router = useRouter();
    const pathname = usePathname();
    const { status, errorMessage, errorTitle } = useAuthUserContext();

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
            <FullPageLoading
                label={errorTitle || 'Bağlantı yenileniyor'}
                description={errorMessage}
            />
        );
    }

    if (status === 'unauthenticated') {
        return <FullPageLoading />;
    }

    return <>{children}</>;
}

