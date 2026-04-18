'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    LayoutDashboard,
    Upload,
    BarChart3,
    Settings2,
    BrainCircuit,
    ChevronLeft,
    ChevronRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { theme } from '@/styles/theme';

interface SidebarProps {
    isCollapsed?: boolean;
    onToggle?: () => void;
}

const navItems = [
    {
        id: 'dashboard',
        label: 'Dashboard',
        icon: LayoutDashboard,
        href: '/dashboard',
    },
    {
        id: 'data-upload',
        label: 'Veri Yükleme',
        icon: Upload,
        href: '/data-upload',
    },
    {
        id: 'eda',
        label: 'EDA',
        icon: BarChart3,
        href: '/eda',
    },
    {
        id: 'preprocessing',
        label: 'Ön İşleme',
        icon: Settings2,
        href: '/preprocessing',
    },
    {
        id: 'model',
        label: 'Model Seçimi',
        icon: BrainCircuit,
        href: '/model',
    },
];

export function Sidebar({ isCollapsed = false, onToggle }: SidebarProps) {
    const pathname = usePathname();

    return (
        <aside
            className={cn(
                'fixed left-0 top-0 z-40 h-screen transition-all duration-300 ease-in-out',
                'border-r border-white/10',
                isCollapsed ? 'w-20' : 'w-72'
            )}
            style={{
                background: theme.colors.background.primary,
            }}
        >
            <div className="flex min-h-16 items-center justify-between px-4 py-3 border-b border-white/10">
                <Link href="/dashboard" className="flex items-center gap-3">
                    <div
                        className="relative w-10 h-10 rounded-xl flex items-center justify-center"
                        style={{
                            background: theme.gradients.primary,
                            boxShadow: theme.glow.cyan,
                        }}
                    >
                        <BrainCircuit className="w-6 h-6 text-white" />
                        <div
                            className="absolute inset-0 rounded-xl animate-ping opacity-20"
                            style={{ background: theme.gradients.primary }}
                        />
                    </div>

                    {!isCollapsed && (
                        <div className="flex flex-col">
                            <span
                                className="font-bold text-xl leading-tight bg-clip-text text-transparent"
                                style={{
                                    backgroundImage: theme.gradients.primary,
                                }}
                            >
                                ML Automation
                            </span>
                            <span className="text-sm leading-tight" style={{ color: theme.colors.text.muted }}>
                                Data Science Copilot
                            </span>
                        </div>
                    )}
                </Link>

                <button
                    onClick={onToggle}
                    className={cn(
                        'p-2 rounded-lg transition-all duration-200',
                        'hover:bg-white/5',
                        isCollapsed && 'absolute -right-3 top-6 bg-gray-800 border border-white/10 rounded-full'
                    )}
                    style={{ color: theme.colors.text.secondary }}
                >
                    {isCollapsed ? (
                        <ChevronRight className="w-4 h-4" />
                    ) : (
                        <ChevronLeft className="w-4 h-4" />
                    )}
                </button>
            </div>

            <nav className="flex-1 px-3 py-4 space-y-1">
                {navItems.map((item) => {
                    const isActive = pathname === item.href;
                    const Icon = item.icon;

                    return (
                        <Link
                            key={item.id}
                            href={item.href}
                            className={cn(
                                'group flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200',
                                'relative overflow-hidden',
                                isActive
                                    ? 'text-white'
                                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                            )}
                            style={
                                isActive
                                    ? {
                                          background: `linear-gradient(135deg, ${theme.colors.primary.cyan}20 0%, ${theme.colors.secondary.green}10 100%)`,
                                          boxShadow: theme.glow.cyan,
                                      }
                                    : undefined
                            }
                        >
                            {isActive && (
                                <div
                                    className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 rounded-r-full"
                                    style={{
                                        background: theme.gradients.primary,
                                    }}
                                />
                            )}

                            <Icon
                                className={cn(
                                    'w-5 h-5 transition-all duration-200',
                                    isActive && 'drop-shadow-[0_0_8px_rgba(0,217,255,0.5)]'
                                )}
                                style={
                                    isActive
                                        ? { color: theme.colors.primary.cyan }
                                        : undefined
                                }
                            />

                            {!isCollapsed && <span className="font-medium">{item.label}</span>}

                            <div
                                className={cn(
                                    'absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300',
                                    'bg-gradient-to-r from-cyan-500/5 to-transparent'
                                )}
                            />
                        </Link>
                    );
                })}
            </nav>
        </aside>
    );
}

