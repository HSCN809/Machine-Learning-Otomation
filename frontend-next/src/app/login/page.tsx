import LoginClient from './LoginClient';
import { normalizeNextPath } from '@/lib/routing';

interface LoginPageProps {
    searchParams?: Promise<Record<string, string | string[] | undefined>>;
}

export default async function LoginPage({ searchParams }: LoginPageProps) {
    const resolvedSearchParams = searchParams ? await searchParams : undefined;
    const nextPath = normalizeNextPath(resolvedSearchParams?.next);
    const registered = resolvedSearchParams?.registered === '1';

    return <LoginClient nextPath={nextPath} registered={registered} />;
}
