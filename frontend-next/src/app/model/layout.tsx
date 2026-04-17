import type { ReactNode } from 'react';

import { ProtectedRouteLayout } from '@/components/auth/ProtectedRouteLayout';

export default function ModelLayout({ children }: { children: ReactNode }) {
    return <ProtectedRouteLayout nextPath="/model">{children}</ProtectedRouteLayout>;
}
