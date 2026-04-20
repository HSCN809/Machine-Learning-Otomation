import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

import { DEFAULT_AUTHENTICATED_PATH, HOMEPAGE_PATH } from '@/lib/routing';
import { AUTH_COOKIE_NAME, hasValidAuthSession } from '@/lib/server-auth';

export default async function RootPage() {
    const cookieStore = await cookies();
    const authCookie = cookieStore.get(AUTH_COOKIE_NAME)?.value;
    const isAuthenticated = await hasValidAuthSession(authCookie);

    redirect(isAuthenticated ? DEFAULT_AUTHENTICATED_PATH : HOMEPAGE_PATH);
}
