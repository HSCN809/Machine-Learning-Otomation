export const DEFAULT_AUTHENTICATED_PATH = '/dashboard';
export const HOMEPAGE_PATH = '/homepage';
export const LOGIN_PATH = '/login';
export const SIGNUP_PATH = '/signup';

export const PROTECTED_PATH_PREFIXES = [
    '/dashboard',
    '/data-upload',
    '/eda',
    '/preprocessing',
    '/model',
    '/settings',
] as const;

export function normalizeNextPath(
    value: string | string[] | null | undefined,
    fallback: string = DEFAULT_AUTHENTICATED_PATH
): string {
    const candidate = Array.isArray(value) ? value[0] : value;

    if (!candidate) {
        return fallback;
    }

    if (!candidate.startsWith('/') || candidate.startsWith('//') || candidate.startsWith('/\\')) {
        return fallback;
    }

    return candidate;
}

export function buildLoginHref(nextPath: string): string {
    return `${LOGIN_PATH}?next=${encodeURIComponent(nextPath)}`;
}

export function buildSignupHref(nextPath: string): string {
    return `${SIGNUP_PATH}?next=${encodeURIComponent(nextPath)}`;
}

export function buildDataUploadHref(nextPath: string): string {
    return `/data-upload?next=${encodeURIComponent(nextPath)}`;
}

export function isProtectedPath(pathname: string): boolean {
    return PROTECTED_PATH_PREFIXES.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
}
