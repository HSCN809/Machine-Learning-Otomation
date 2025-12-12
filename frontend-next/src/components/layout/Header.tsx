'use client';

import { Bell, Search, User, Settings } from 'lucide-react';
import { theme } from '@/styles/theme';
import { cn } from '@/lib/utils';

interface HeaderProps {
    title?: string;
    showSearch?: boolean;
}

export function Header({ title = 'Dashboard', showSearch = true }: HeaderProps) {
    return (
        <header
            className="sticky top-0 z-30 flex items-center justify-between h-16 px-6 border-b border-white/10 backdrop-blur-xl"
            style={{
                background: `${theme.colors.background.primary}CC`,
            }}
        >
            {/* Left Section - Page Title */}
            <div className="flex items-center gap-4">
                <h1
                    className="text-xl font-bold bg-clip-text text-transparent"
                    style={{
                        backgroundImage: theme.gradients.primary,
                    }}
                >
                    {title}
                </h1>
            </div>

            {/* Center Section - Search Bar */}
            {showSearch && (
                <div className="flex-1 max-w-xl mx-8">
                    <div
                        className="relative flex items-center rounded-xl border border-white/10 transition-all duration-200 focus-within:border-cyan-500/50"
                        style={{
                            background: theme.colors.background.secondary,
                        }}
                    >
                        <Search
                            className="absolute left-3 w-5 h-5"
                            style={{ color: theme.colors.text.muted }}
                        />
                        <input
                            type="text"
                            placeholder="Ara..."
                            className={cn(
                                'w-full py-2.5 pl-10 pr-4 bg-transparent text-sm outline-none',
                                'placeholder:text-gray-500'
                            )}
                            style={{ color: theme.colors.text.primary }}
                        />
                        <kbd
                            className="hidden sm:flex items-center gap-1 px-2 py-1 mr-2 text-xs rounded border border-white/10"
                            style={{
                                color: theme.colors.text.muted,
                                background: theme.colors.background.tertiary,
                            }}
                        >
                            <span>⌘</span>
                            <span>K</span>
                        </kbd>
                    </div>
                </div>
            )}

            {/* Right Section - Actions */}
            <div className="flex items-center gap-2">
                {/* Notifications */}
                <button
                    className={cn(
                        'relative p-2.5 rounded-xl transition-all duration-200',
                        'hover:bg-white/5 group'
                    )}
                    style={{ color: theme.colors.text.secondary }}
                >
                    <Bell className="w-5 h-5 group-hover:text-cyan-400 transition-colors" />
                    {/* Notification badge */}
                    <span
                        className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full"
                        style={{
                            background: theme.colors.status.error,
                            boxShadow: `0 0 8px ${theme.colors.status.error}`,
                        }}
                    />
                </button>

                {/* Settings */}
                <button
                    className={cn(
                        'p-2.5 rounded-xl transition-all duration-200',
                        'hover:bg-white/5 group'
                    )}
                    style={{ color: theme.colors.text.secondary }}
                >
                    <Settings className="w-5 h-5 group-hover:text-cyan-400 transition-colors" />
                </button>

                {/* User Profile */}
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
