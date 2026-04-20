import type { ReactNode } from 'react';
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

import { buildLoginHref } from '@/lib/routing';
import { AUTH_COOKIE_NAME, hasValidAuthSession } from '@/lib/server-auth';

interface ProtectedRouteLayoutProps {
    children: ReactNode;
    nextPath: string;
}

export async function ProtectedRouteLayout({
    children,
    nextPath,
}: ProtectedRouteLayoutProps) {
    const cookieStore = await cookies();
    const authCookie = cookieStore.get(AUTH_COOKIE_NAME)?.value;
    const isAuthenticated = await hasValidAuthSession(authCookie);

    if (!isAuthenticated) {
        redirect(buildLoginHref(nextPath));
    }

    return <>{children}</>;
}
