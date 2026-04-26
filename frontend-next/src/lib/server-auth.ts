import { logger } from '@/lib/logger';

export const AUTH_COOKIE_NAME =
    process.env.AUTH_COOKIE_NAME ||
    process.env.NEXT_PUBLIC_AUTH_COOKIE_NAME ||
    'ml_auth_session';

const BACKEND_BASE_URL = process.env.BACKEND_API_URL || 'http://localhost:8000';

export async function hasValidAuthSession(authCookie: string | undefined): Promise<boolean> {
    if (!authCookie) {
        return false;
    }

    try {
        const response = await fetch(`${BACKEND_BASE_URL}/api/auth/status`, {
            headers: {
                cookie: `${AUTH_COOKIE_NAME}=${authCookie}`,
            },
            cache: 'no-store',
        });

        if (!response.ok) {
            logger.warn('Server auth status returned non-ok response', {
                status: response.status,
            });
            return false;
        }

        const status = (await response.json()) as {
            authenticated?: boolean;
            user?: unknown;
        };

        const isValid = Boolean(status.authenticated && status.user);
        return isValid;
    } catch (error) {
        logger.error('Server auth status request failed', error);
        return false;
    }
}
