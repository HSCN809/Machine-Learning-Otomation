'use client';

import { ReactNode } from 'react';
import { Toaster } from 'sonner';
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
                <Toaster
                    closeButton
                    richColors
                    position="top-right"
                    theme="dark"
                    toastOptions={{
                        duration: 4500,
                    }}
                />
            </DataUploadProvider>
        </AuthUserProvider>
    );
}
