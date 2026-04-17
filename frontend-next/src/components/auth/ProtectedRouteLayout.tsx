import type { ReactNode } from 'react';
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

import { buildLoginHref } from '@/lib/routing';

const AUTH_COOKIE_NAME = process.env.AUTH_COOKIE_NAME || 'ml_auth_session';

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

    if (!authCookie) {
        redirect(buildLoginHref(nextPath));
    }

    return <>{children}</>;
}
