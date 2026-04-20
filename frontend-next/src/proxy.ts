import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

import { buildLoginHref, HOMEPAGE_PATH } from '@/lib/routing';

const AUTH_COOKIE_NAME =
    process.env.AUTH_COOKIE_NAME ||
    process.env.NEXT_PUBLIC_AUTH_COOKIE_NAME ||
    'ml_auth_session';

function isProtectedPath(pathname: string): boolean {
    return (
        pathname.startsWith('/dashboard') ||
        pathname.startsWith('/settings') ||
        pathname.startsWith('/data-upload') ||
        pathname.startsWith('/eda') ||
        pathname.startsWith('/preprocessing') ||
        pathname.startsWith('/model')
    );
}

export function proxy(request: NextRequest) {
    const { pathname, search } = request.nextUrl;
    const hasAuthCookie = Boolean(request.cookies.get(AUTH_COOKIE_NAME)?.value);

    if (pathname === '/' && !hasAuthCookie) {
        return NextResponse.redirect(new URL(HOMEPAGE_PATH, request.url));
    }

    if (isProtectedPath(pathname) && !hasAuthCookie) {
        return NextResponse.redirect(new URL(buildLoginHref(`${pathname}${search}`), request.url));
    }

    return NextResponse.next();
}

export const config = {
    matcher: [
        '/',
        '/login',
        '/signup',
        '/dashboard/:path*',
        '/settings/:path*',
        '/data-upload/:path*',
        '/eda/:path*',
        '/preprocessing/:path*',
        '/model/:path*',
    ],
};
