'use client';

import { ReactNode } from 'react';
import { DataUploadProvider } from '@/context/DataUploadContext';

interface ProvidersProps {
    children: ReactNode;
}

export function Providers({ children }: ProvidersProps) {
    return (
        <DataUploadProvider>
            {children}
        </DataUploadProvider>
    );
}
