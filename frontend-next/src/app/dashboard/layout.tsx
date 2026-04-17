import type { ReactNode } from 'react';

import { ProtectedRouteLayout } from '@/components/auth/ProtectedRouteLayout';

export default function DashboardLayout({ children }: { children: ReactNode }) {
    return <ProtectedRouteLayout nextPath="/dashboard">{children}</ProtectedRouteLayout>;
}
