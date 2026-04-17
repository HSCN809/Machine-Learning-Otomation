import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const AUTH_COOKIE_NAME = process.env.NEXT_PUBLIC_AUTH_COOKIE_NAME || 'ml_auth_session';
const HOMEPAGE_PATH = '/homepage';

function isProtectedPath(pathname: string): boolean {
    return (
        pathname === '/' ||
        pathname.startsWith('/settings') ||
        pathname.startsWith('/data-upload') ||
        pathname.startsWith('/eda') ||
        pathname.startsWith('/preprocessing') ||
        pathname.startsWith('/model')
    );
}

export function proxy(request: NextRequest) {
    const { pathname } = request.nextUrl;
    const hasAuthCookie = Boolean(request.cookies.get(AUTH_COOKIE_NAME)?.value);

    if ((pathname === '/login' || pathname === '/signup') && hasAuthCookie) {
        return NextResponse.redirect(new URL('/', request.url));
    }

    if (isProtectedPath(pathname) && !hasAuthCookie) {
        return NextResponse.redirect(new URL(HOMEPAGE_PATH, request.url));
    }

    return NextResponse.next();
}

export const config = {
    matcher: ['/', '/login', '/signup', '/settings/:path*', '/data-upload/:path*', '/eda/:path*', '/preprocessing/:path*', '/model/:path*'],
};
