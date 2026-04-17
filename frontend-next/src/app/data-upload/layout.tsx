import type { ReactNode } from 'react';

import { ProtectedRouteLayout } from '@/components/auth/ProtectedRouteLayout';

export default function DataUploadLayout({ children }: { children: ReactNode }) {
    return <ProtectedRouteLayout nextPath="/data-upload">{children}</ProtectedRouteLayout>;
}
