'use client';

import Link from 'next/link';
import { AlertTriangle, Upload } from 'lucide-react';
import { theme } from '@/styles/theme';

interface NoDataWarningProps {
    title?: string;
    description?: string;
}

export function NoDataWarning({
    title = 'Veri Yüklenmedi',
    description = 'Bu sayfayı kullanabilmek için önce veri yüklemeniz gerekmektedir.',
}: NoDataWarningProps) {
    return (
        <div className="flex flex-col items-center justify-center py-20 space-y-6">
            <div
                className="p-6 rounded-2xl border border-yellow-500/30"
                style={{
                    background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(245, 158, 11, 0.05) 100%)',
                }}
            >
                <AlertTriangle className="w-16 h-16 text-yellow-400 mx-auto" />
            </div>

            <div className="text-center space-y-2">
                <h2 className="text-2xl font-bold text-white">{title}</h2>
                <p className="text-gray-400 max-w-md">{description}</p>
            </div>

            <Link
                href="/data-upload"
                className="inline-flex items-center gap-3 px-8 py-4 rounded-xl font-medium text-white transition-all hover:scale-105"
                style={{
                    background: theme.gradients.primary,
                    boxShadow: theme.glow.cyan,
                }}
            >
                <Upload className="w-5 h-5" />
                Veri Yükle
            </Link>
        </div>
    );
}
