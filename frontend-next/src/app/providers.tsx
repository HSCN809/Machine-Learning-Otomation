'use client';

import { ReactNode } from 'react';
import { AuthUserProvider } from '@/context/AuthUserContext';
import { DataUploadProvider } from '@/context/DataUploadContext';

interface ProvidersProps {
    children: ReactNode;
}

export function Providers({ children }: ProvidersProps) {
    return (
        <AuthUserProvider>
            <DataUploadProvider>
                {children}
            </DataUploadProvider>
        </AuthUserProvider>
    );
}
