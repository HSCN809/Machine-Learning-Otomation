'use client';

import { useEffect, useRef, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import {
    ChevronDown,
    LogOut,
    Settings,
    User,
    UserCog,
} from 'lucide-react';

import { cn } from '@/lib/utils';
import { getCurrentUser, logout, type AuthUser } from '@/lib/api';
import { theme } from '@/styles/theme';

interface HeaderProps {
    title?: string;
    subtitle?: string;
}

function getFallbackUser(): AuthUser {
    return {
        id: 'anonymous',
        email: '',
        full_name: 'Kullanıcı',
    };
}

export function Header({ title = 'Dashboard', subtitle }: HeaderProps) {
    const router = useRouter();
    const pathname = usePathname();
    const menuRef = useRef<HTMLDivElement | null>(null);

    const [menuOpen, setMenuOpen] = useState(false);
    const [isLoggingOut, setIsLoggingOut] = useState(false);
    const [currentUser, setCurrentUser] = useState<AuthUser>(getFallbackUser);

    useEffect(() => {
        let cancelled = false;

        async function loadUser() {
            try {
                const response = await getCurrentUser();
                if (!cancelled) {
                    setCurrentUser(response.user);
                }
            } catch {
                if (!cancelled) {
                    setCurrentUser(getFallbackUser());
                }
            }
        }

        loadUser();

        function handleUserUpdated(event: Event) {
            const customEvent = event as CustomEvent<AuthUser>;
            if (customEvent.detail) {
                setCurrentUser(customEvent.detail);
            }
        }

        function handlePointerDown(event: MouseEvent) {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                setMenuOpen(false);
            }
        }

        window.addEventListener('auth:user-updated', handleUserUpdated as EventListener);
        window.addEventListener('mousedown', handlePointerDown);

        return () => {
            cancelled = true;
            window.removeEventListener('auth:user-updated', handleUserUpdated as EventListener);
            window.removeEventListener('mousedown', handlePointerDown);
        };
    }, []);

    async function handleLogout() {
        setIsLoggingOut(true);
        try {
            await logout();
            setMenuOpen(false);
            router.replace('/login');
            router.refresh();
        } finally {
            setIsLoggingOut(false);
        }
    }

    function handleOpenProfile() {
        setMenuOpen(false);
        if (pathname !== '/settings') {
            router.push('/settings');
        }
    }

    return (
        <header
            className="sticky top-0 z-30 flex min-h-16 items-center justify-between border-b border-white/10 px-6 py-3 backdrop-blur-xl"
            style={{
                background: `${theme.colors.background.primary}CC`,
            }}
        >
            <div className="flex items-center gap-4">
                <div>
                    <h1
                        className="bg-clip-text text-xl font-bold text-transparent"
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
                    type="button"
                    onClick={handleOpenProfile}
                    className={cn(
                        'group cursor-pointer rounded-xl p-2.5 transition-all duration-200',
                        'hover:bg-white/5'
                    )}
                    style={{ color: theme.colors.text.secondary }}
                >
                    <Settings className="h-5 w-5 transition-colors group-hover:text-cyan-400" />
                </button>

                <div className="relative" ref={menuRef}>
                    <button
                        type="button"
                        onClick={() => setMenuOpen((current) => !current)}
                        className={cn(
                            'flex cursor-pointer items-center gap-3 rounded-xl border border-white/10 p-1.5 pr-3 transition-all duration-200',
                            'hover:bg-white/5'
                        )}
                    >
                        <div
                            className="flex h-8 w-8 items-center justify-center rounded-lg"
                            style={{
                                background: theme.gradients.secondary,
                            }}
                        >
                            <User className="h-4 w-4 text-white" />
                        </div>
                        <span
                            className="hidden text-sm font-medium sm:block"
                            style={{ color: theme.colors.text.primary }}
                        >
                            {currentUser.full_name}
                        </span>
                        <ChevronDown
                            className={cn(
                                'h-4 w-4 text-gray-400 transition-transform duration-200',
                                menuOpen && 'rotate-180'
                            )}
                        />
                    </button>

                    {menuOpen && (
                        <div
                            className="absolute right-0 top-full mt-3 w-56 overflow-hidden rounded-2xl border border-white/10 bg-[#101827] p-2 shadow-[0_24px_60px_rgba(3,7,18,0.45)]"
                        >
                            <div className="border-b border-white/10 px-3 py-2">
                                <p className="text-sm font-medium text-white">{currentUser.full_name}</p>
                                <p className="mt-1 text-xs text-slate-400">{currentUser.email || 'Aktif oturum'}</p>
                            </div>

                            <button
                                type="button"
                                onClick={handleOpenProfile}
                                className="mt-2 flex w-full cursor-pointer items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-slate-200 transition-colors hover:bg-white/5"
                            >
                                <UserCog className="h-4 w-4 text-cyan-300" />
                                Profil
                            </button>

                            <button
                                type="button"
                                onClick={handleLogout}
                                disabled={isLoggingOut}
                                className="flex w-full cursor-pointer items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-slate-200 transition-colors hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-60"
                            >
                                <LogOut className="h-4 w-4 text-rose-300" />
                                {isLoggingOut ? 'Çıkış yapılıyor...' : 'Çıkış yap'}
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </header>
    );
}
