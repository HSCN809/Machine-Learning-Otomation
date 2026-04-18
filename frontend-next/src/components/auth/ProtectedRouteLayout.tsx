import type { ReactNode } from 'react';
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

import { HOMEPAGE_PATH } from '@/lib/routing';

const AUTH_COOKIE_NAME =
    process.env.AUTH_COOKIE_NAME ||
    process.env.NEXT_PUBLIC_AUTH_COOKIE_NAME ||
    'ml_auth_session';

interface ProtectedRouteLayoutProps {
    children: ReactNode;
    nextPath: string;
}

export async function ProtectedRouteLayout({
    children,
    nextPath,
}: ProtectedRouteLayoutProps) {
    void nextPath;

    const cookieStore = await cookies();
    const authCookie = cookieStore.get(AUTH_COOKIE_NAME)?.value;

    if (!authCookie) {
        redirect(HOMEPAGE_PATH);
    }

    return <>{children}</>;
}
