import type { ReactNode } from 'react';

import { ProtectedRouteLayout } from '@/components/auth/ProtectedRouteLayout';

export default function EDALayout({ children }: { children: ReactNode }) {
    return <ProtectedRouteLayout nextPath="/eda">{children}</ProtectedRouteLayout>;
}
