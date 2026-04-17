import SignupClient from './SignupClient';
import { normalizeNextPath } from '@/lib/routing';

interface SignupPageProps {
    searchParams?: Promise<Record<string, string | string[] | undefined>>;
}

export default async function SignupPage({ searchParams }: SignupPageProps) {
    const resolvedSearchParams = searchParams ? await searchParams : undefined;
    const nextPath = normalizeNextPath(resolvedSearchParams?.next);

    return <SignupClient nextPath={nextPath} />;
}
