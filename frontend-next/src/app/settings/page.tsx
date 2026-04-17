'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
    KeyRound,
    ShieldAlert,
    UserCircle2,
} from 'lucide-react';

import { Header, Sidebar } from '@/components/layout';
import {
    changePassword,
    deleteAccount,
    getCurrentUser,
    updateProfile,
    type AuthUser,
} from '@/lib/api';

type PageState = 'bootstrap' | 'ready' | 'error';

function getErrorMessage(error: unknown): string {
    if (error instanceof Error && error.message) {
        return error.message;
    }

    return 'İşlem tamamlanamadı. Lütfen tekrar deneyin.';
}

export default function SettingsPage() {
    const router = useRouter();

    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [pageState, setPageState] = useState<PageState>('bootstrap');
    const [pageError, setPageError] = useState('');
    const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);

    const [fullName, setFullName] = useState('');
    const [email, setEmail] = useState('');
    const [profileMessage, setProfileMessage] = useState('');
    const [profileError, setProfileError] = useState('');
    const [profilePending, setProfilePending] = useState(false);

    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [passwordMessage, setPasswordMessage] = useState('');
    const [passwordError, setPasswordError] = useState('');
    const [passwordPending, setPasswordPending] = useState(false);

    const [deletePassword, setDeletePassword] = useState('');
    const [deleteError, setDeleteError] = useState('');
    const [deletePending, setDeletePending] = useState(false);

    useEffect(() => {
        let cancelled = false;

        async function bootstrap() {
            try {
                const response = await getCurrentUser();
                if (cancelled) {
                    return;
                }

                setCurrentUser(response.user);
                setFullName(response.user.full_name);
                setEmail(response.user.email);
                setPageState('ready');
            } catch (error) {
                if (cancelled) {
                    return;
                }

                setPageState('error');
                setPageError(getErrorMessage(error));
            }
        }

        bootstrap();

        return () => {
            cancelled = true;
        };
    }, []);

    async function handleProfileSubmit(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setProfileMessage('');
        setProfileError('');

        if (!fullName.trim() || !email.trim()) {
            setProfileError('Ad soyad ve e-posta alanları zorunlu.');
            return;
        }

        setProfilePending(true);
        try {
            const response = await updateProfile(fullName.trim(), email.trim());
            if (response.user) {
                setCurrentUser(response.user);
                setFullName(response.user.full_name);
                setEmail(response.user.email);
                window.dispatchEvent(new CustomEvent('auth:user-updated', { detail: response.user }));
            }
            setProfileMessage(response.message);
        } catch (error) {
            setProfileError(getErrorMessage(error));
        } finally {
            setProfilePending(false);
        }
    }

    async function handlePasswordSubmit(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setPasswordMessage('');
        setPasswordError('');

        if (!currentPassword.trim() || !newPassword.trim()) {
            setPasswordError('Mevcut parola ve yeni parola zorunlu.');
            return;
        }

        setPasswordPending(true);
        try {
            const response = await changePassword(currentPassword, newPassword);
            setPasswordMessage(response.message);
            setCurrentPassword('');
            setNewPassword('');
        } catch (error) {
            setPasswordError(getErrorMessage(error));
        } finally {
            setPasswordPending(false);
        }
    }

    async function handleDeleteAccount(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setDeleteError('');

        if (!deletePassword.trim()) {
            setDeleteError('Hesabı silmek için parolanızı girin.');
            return;
        }

        if (!window.confirm('Hesabınızı silmek istediğinize emin misiniz? Bu işlem geri alınamaz.')) {
            return;
        }

        setDeletePending(true);
        try {
            const response = await deleteAccount(deletePassword);
            router.push(response.requires_setup ? '/signup' : '/login');
            router.refresh();
        } catch (error) {
            setDeleteError(getErrorMessage(error));
        } finally {
            setDeletePending(false);
        }
    }

    return (
        <div className="min-h-screen">
            <Sidebar
                isCollapsed={sidebarCollapsed}
                onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
            />

            <div
                className="transition-all duration-300"
                style={{
                    marginLeft: sidebarCollapsed ? '80px' : '288px',
                }}
            >
                <Header
                    title="Ayarlar"
                    subtitle="Profil bilgilerinizi yönetin, parolanızı değiştirin veya hesabınızı kapatın."
                />

                <main className="space-y-8 p-6">
                    <section
                        className="rounded-2xl border border-white/10 p-6"
                        style={{
                            background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.75) 0%, rgba(31, 41, 55, 0.35) 100%)',
                        }}
                    >
                        <div className="flex flex-wrap items-center gap-3">
                            <div className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-2 text-sm font-medium text-cyan-100">
                                <UserCircle2 className="h-4 w-4" />
                                Profil
                            </div>
                            {currentUser && (
                                <p className="text-sm text-slate-400">
                                    Aktif hesap: <span className="text-slate-200">{currentUser.full_name}</span>
                                </p>
                            )}
                        </div>
                    </section>

                    {pageState === 'bootstrap' && (
                        <section className="grid gap-6 xl:grid-cols-2">
                            <div className="h-72 animate-pulse rounded-2xl bg-white/5" />
                            <div className="h-72 animate-pulse rounded-2xl bg-white/5" />
                            <div className="h-56 animate-pulse rounded-2xl bg-white/5 xl:col-span-2" />
                        </section>
                    )}

                    {pageState === 'error' && (
                        <section className="rounded-2xl border border-red-400/25 bg-red-500/10 p-5 text-sm text-red-100">
                            {pageError}
                        </section>
                    )}

                    {pageState === 'ready' && (
                        <section className="grid gap-6 xl:grid-cols-2">
                            <form
                                onSubmit={handleProfileSubmit}
                                className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl"
                            >
                                <div className="mb-6 flex items-center gap-3">
                                    <div className="rounded-xl bg-cyan-400/10 p-3 text-cyan-200">
                                        <UserCircle2 className="h-5 w-5" />
                                    </div>
                                    <div>
                                        <h2 className="text-xl font-semibold text-white">Profil bilgileri</h2>
                                        <p className="mt-1 text-sm text-slate-400">Adınızı ve e-posta adresinizi güncelleyin.</p>
                                    </div>
                                </div>

                                {profileError && (
                                    <div className="mb-4 rounded-xl border border-red-400/25 bg-red-500/10 p-4 text-sm text-red-100">
                                        {profileError}
                                    </div>
                                )}

                                {profileMessage && (
                                    <div className="mb-4 rounded-xl border border-emerald-400/25 bg-emerald-500/10 p-4 text-sm text-emerald-100">
                                        {profileMessage}
                                    </div>
                                )}

                                <div className="space-y-4">
                                    <label className="block">
                                        <span className="mb-2 block text-sm text-slate-300">Ad soyad</span>
                                        <input
                                            value={fullName}
                                            onChange={(event) => setFullName(event.target.value)}
                                            disabled={profilePending}
                                            minLength={2}
                                            className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-white outline-none transition focus:border-cyan-300/50 focus:ring-2 focus:ring-cyan-400/20 disabled:cursor-not-allowed disabled:opacity-60"
                                        />
                                    </label>

                                    <label className="block">
                                        <span className="mb-2 block text-sm text-slate-300">E-posta</span>
                                        <input
                                            type="email"
                                            value={email}
                                            onChange={(event) => setEmail(event.target.value)}
                                            disabled={profilePending}
                                            className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-white outline-none transition focus:border-cyan-300/50 focus:ring-2 focus:ring-cyan-400/20 disabled:cursor-not-allowed disabled:opacity-60"
                                        />
                                    </label>
                                </div>

                                <button
                                    type="submit"
                                    disabled={profilePending}
                                    className="mt-6 inline-flex cursor-pointer items-center justify-center rounded-full bg-[linear-gradient(135deg,#00D9FF_0%,#00FF88_100%)] px-6 py-3 text-sm font-semibold text-slate-950 transition-transform duration-300 hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
                                >
                                    {profilePending ? 'Kaydediliyor...' : 'Bilgileri kaydet'}
                                </button>
                            </form>

                            <form
                                onSubmit={handlePasswordSubmit}
                                className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl"
                            >
                                <div className="mb-6 flex items-center gap-3">
                                    <div className="rounded-xl bg-cyan-400/10 p-3 text-cyan-200">
                                        <KeyRound className="h-5 w-5" />
                                    </div>
                                    <div>
                                        <h2 className="text-xl font-semibold text-white">Şifre değiştir</h2>
                                        <p className="mt-1 text-sm text-slate-400">Güvenlik için yeni bir parola belirleyin.</p>
                                    </div>
                                </div>

                                {passwordError && (
                                    <div className="mb-4 rounded-xl border border-red-400/25 bg-red-500/10 p-4 text-sm text-red-100">
                                        {passwordError}
                                    </div>
                                )}

                                {passwordMessage && (
                                    <div className="mb-4 rounded-xl border border-emerald-400/25 bg-emerald-500/10 p-4 text-sm text-emerald-100">
                                        {passwordMessage}
                                    </div>
                                )}

                                <div className="space-y-4">
                                    <label className="block">
                                        <span className="mb-2 block text-sm text-slate-300">Mevcut parola</span>
                                        <input
                                            type="password"
                                            value={currentPassword}
                                            onChange={(event) => setCurrentPassword(event.target.value)}
                                            disabled={passwordPending}
                                            className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-white outline-none transition focus:border-cyan-300/50 focus:ring-2 focus:ring-cyan-400/20 disabled:cursor-not-allowed disabled:opacity-60"
                                        />
                                    </label>

                                    <label className="block">
                                        <span className="mb-2 block text-sm text-slate-300">Yeni parola</span>
                                        <input
                                            type="password"
                                            value={newPassword}
                                            onChange={(event) => setNewPassword(event.target.value)}
                                            disabled={passwordPending}
                                            minLength={3}
                                            className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-white outline-none transition focus:border-cyan-300/50 focus:ring-2 focus:ring-cyan-400/20 disabled:cursor-not-allowed disabled:opacity-60"
                                        />
                                    </label>
                                </div>

                                <button
                                    type="submit"
                                    disabled={passwordPending}
                                    className="mt-6 inline-flex cursor-pointer items-center justify-center rounded-full border border-white/15 bg-white/5 px-6 py-3 text-sm font-semibold text-white transition-colors duration-300 hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-60"
                                >
                                    {passwordPending ? 'Güncelleniyor...' : 'Parolayı değiştir'}
                                </button>
                            </form>

                            <form
                                onSubmit={handleDeleteAccount}
                                className="rounded-2xl border border-rose-400/15 bg-rose-500/5 p-6 xl:col-span-2"
                            >
                                <div className="mb-6 flex items-center gap-3">
                                    <div className="rounded-xl bg-rose-500/10 p-3 text-rose-200">
                                        <ShieldAlert className="h-5 w-5" />
                                    </div>
                                    <div>
                                        <h2 className="text-xl font-semibold text-white">Hesabı sil</h2>
                                        <p className="mt-1 text-sm text-slate-400">Bu işlem hesabınızı ve oturumunuzu kalıcı olarak kaldırır.</p>
                                    </div>
                                </div>

                                {deleteError && (
                                    <div className="mb-4 rounded-xl border border-red-400/25 bg-red-500/10 p-4 text-sm text-red-100">
                                        {deleteError}
                                    </div>
                                )}

                                <div className="grid gap-4 lg:grid-cols-[minmax(0,360px)_auto] lg:items-end">
                                    <label className="block">
                                        <span className="mb-2 block text-sm text-slate-300">Parolanızı doğrulayın</span>
                                        <input
                                            type="password"
                                            value={deletePassword}
                                            onChange={(event) => setDeletePassword(event.target.value)}
                                            disabled={deletePending}
                                            className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-white outline-none transition focus:border-rose-300/50 focus:ring-2 focus:ring-rose-400/20 disabled:cursor-not-allowed disabled:opacity-60"
                                        />
                                    </label>

                                    <button
                                        type="submit"
                                        disabled={deletePending}
                                        className="inline-flex cursor-pointer items-center justify-center rounded-full bg-rose-500 px-6 py-3 text-sm font-semibold text-white transition-colors duration-300 hover:bg-rose-400 disabled:cursor-not-allowed disabled:opacity-60"
                                    >
                                        {deletePending ? 'Hesap siliniyor...' : 'Hesabı sil'}
                                    </button>
                                </div>
                            </form>
                        </section>
                    )}
                </main>
            </div>
        </div>
    );
}
