import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

import { DEFAULT_AUTHENTICATED_PATH, HOMEPAGE_PATH } from '@/lib/routing';

const AUTH_COOKIE_NAME =
    process.env.AUTH_COOKIE_NAME ||
    process.env.NEXT_PUBLIC_AUTH_COOKIE_NAME ||
    'ml_auth_session';

export default async function RootPage() {
    const cookieStore = await cookies();
    const authCookie = cookieStore.get(AUTH_COOKIE_NAME)?.value;

    redirect(authCookie ? DEFAULT_AUTHENTICATED_PATH : HOMEPAGE_PATH);
}
