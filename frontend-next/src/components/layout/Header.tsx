'use client';

import { Bell, User, Settings } from 'lucide-react';
import { theme } from '@/styles/theme';
import { cn } from '@/lib/utils';

interface HeaderProps {
    title?: string;
    subtitle?: string;
}

export function Header({ title = 'Dashboard', subtitle }: HeaderProps) {
    return (
        <header
            className="sticky top-0 z-30 flex items-center justify-between min-h-16 px-6 py-3 border-b border-white/10 backdrop-blur-xl"
            style={{
                background: `${theme.colors.background.primary}CC`,
            }}
        >
            <div className="flex items-center gap-4">
                <div>
                    <h1
                        className="text-xl font-bold bg-clip-text text-transparent"
                        style={{
                            backgroundImage: theme.gradients.primary,
                        }}
                    >
                        {title}
                    </h1>
                    {subtitle && (
                        <p className="mt-1 text-sm text-gray-400">
                            {subtitle}
                        </p>
                    )}
                </div>
            </div>

            <div className="flex items-center gap-2">
                <button
                    className={cn(
                        'relative p-2.5 rounded-xl transition-all duration-200',
                        'hover:bg-white/5 group'
                    )}
                    style={{ color: theme.colors.text.secondary }}
                >
                    <Bell className="w-5 h-5 group-hover:text-cyan-400 transition-colors" />
                    <span
                        className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full"
                        style={{
                            background: theme.colors.status.error,
                            boxShadow: `0 0 8px ${theme.colors.status.error}`,
                        }}
                    />
                </button>

                <button
                    className={cn(
                        'p-2.5 rounded-xl transition-all duration-200',
                        'hover:bg-white/5 group'
                    )}
                    style={{ color: theme.colors.text.secondary }}
                >
                    <Settings className="w-5 h-5 group-hover:text-cyan-400 transition-colors" />
                </button>

                <button
                    className={cn(
                        'flex items-center gap-3 p-1.5 pr-3 rounded-xl transition-all duration-200',
                        'hover:bg-white/5 border border-white/10'
                    )}
                >
                    <div
                        className="w-8 h-8 rounded-lg flex items-center justify-center"
                        style={{
                            background: theme.gradients.secondary,
                        }}
                    >
                        <User className="w-4 h-4 text-white" />
                    </div>
                    <span
                        className="text-sm font-medium hidden sm:block"
                        style={{ color: theme.colors.text.primary }}
                    >
                        Kullanıcı
                    </span>
                </button>
            </div>
        </header>
    );
}
