import type { ReactNode } from 'react';

import { ProtectedRouteLayout } from '@/components/auth/ProtectedRouteLayout';

export default function PreprocessingLayout({ children }: { children: ReactNode }) {
    return <ProtectedRouteLayout nextPath="/preprocessing">{children}</ProtectedRouteLayout>;
}
