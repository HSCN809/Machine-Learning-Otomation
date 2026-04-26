'use client';

import { ReactNode, useState } from 'react';
import { Toaster } from 'sonner';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthUserProvider } from '@/context/AuthUserContext';
import { DataUploadProvider } from '@/context/DataUploadContext';

interface ProvidersProps {
    children: ReactNode;
}

export function Providers({ children }: ProvidersProps) {
    const [queryClient] = useState(
        () =>
            new QueryClient({
                defaultOptions: {
                    queries: {
                        staleTime: 60 * 1000, // 1 minute
                        retry: 1,
                        refetchOnWindowFocus: false,
                    },
                },
            })
    );

    return (
        <QueryClientProvider client={queryClient}>
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
        </QueryClientProvider>
    );
}
