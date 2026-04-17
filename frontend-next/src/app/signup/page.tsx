import SignupClient from './SignupClient';

interface SignupPageProps {
    searchParams?: Promise<Record<string, string | string[] | undefined>>;
}

function normalizeNextPath(value: string | string[] | undefined): string {
    const candidate = Array.isArray(value) ? value[0] : value;

    if (!candidate || !candidate.startsWith('/')) {
        return '/';
    }

    return candidate;
}

export default async function SignupPage({ searchParams }: SignupPageProps) {
    const resolvedSearchParams = searchParams ? await searchParams : undefined;
    const nextPath = normalizeNextPath(resolvedSearchParams?.next);

    return <SignupClient nextPath={nextPath} />;
}
