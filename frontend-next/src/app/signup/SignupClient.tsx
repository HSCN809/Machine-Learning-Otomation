'use client';

import { useEffect, useMemo, useState, useTransition } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { JetBrains_Mono, Space_Grotesk } from 'next/font/google';
import { ArrowRight, BrainCircuit, ShieldCheck } from 'lucide-react';

import { getAuthStatus, setupFirstUser } from '@/lib/api';
import { logger } from '@/lib/logger';
import { notify } from '@/lib/notify';
import { buildLoginHref, HOMEPAGE_PATH } from '@/lib/routing';

const spaceGrotesk = Space_Grotesk({
    subsets: ['latin'],
    variable: '--font-space-grotesk',
});

const jetBrainsMono = JetBrains_Mono({
    subsets: ['latin'],
    variable: '--font-jetbrains-mono',
});

type LoadState = 'bootstrap' | 'ready' | 'success' | 'error';

interface SignupClientProps {
    nextPath: string;
}

function getErrorMessage(error: unknown): string {
    if (error instanceof Error && error.message) {
        return error.message;
    }
    return 'İşlem tamamlanamadı. Lütfen tekrar deneyin.';
}

export default function SignupClient({ nextPath }: SignupClientProps) {
    const router = useRouter();
    const [isPending, startTransition] = useTransition();

    const [pageState, setPageState] = useState<LoadState>('bootstrap');
    const [requiresSetup, setRequiresSetup] = useState(false);

    const [fullName, setFullName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        let cancelled = false;

        async function bootstrap() {
            try {
                const status = await getAuthStatus();
                if (cancelled) {
                    return;
                }

                setRequiresSetup(status.requires_setup);

                if (status.user && status.authenticated) {
                    startTransition(() => {
                        router.replace(nextPath);
                    });
                    return;
                }

                setPageState('ready');
            } catch (error) {
                if (cancelled) {
                    return;
                }

                logger.error('Signup page bootstrap failed', error);
                notify.error(error, 'Sayfa yüklenirken hata oluştu');
            }
        }

        bootstrap();

        return () => {
            cancelled = true;
        };
    }, [nextPath, router, startTransition]);

    const modeLabel = useMemo(() => {
        return 'Kayıt ol';
    }, []);

    const isFormDisabled = isSubmitting || isPending || pageState === 'bootstrap';

    async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
        event.preventDefault();

        if (!fullName.trim() || !email.trim() || !password.trim()) {
            notify.warning('Ad soyad, e-posta ve parola zorunlu.');
            return;
        }

        setIsSubmitting(true);

        try {
            await setupFirstUser(fullName.trim(), email.trim(), password);
            notify.success('Hesap oluşturuldu');

            startTransition(() => {
                router.replace(`${buildLoginHref(nextPath)}&registered=1`);
            });
        } catch (error) {
            logger.error('Signup submit failed', error, { email: email.trim() });
            setPageState('ready');
            notify.error(error, 'Kayıt sırasında hata oluştu');
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <div
            className={`${spaceGrotesk.variable} ${jetBrainsMono.variable} min-h-screen overflow-hidden bg-[#07101f] text-white`}
            style={{
                background:
                    'radial-gradient(circle at top left, rgba(0, 217, 255, 0.16), transparent 28%), radial-gradient(circle at 88% 14%, rgba(0, 255, 136, 0.12), transparent 22%), linear-gradient(180deg, #07101f 0%, #0b1324 52%, #050914 100%)',
            }}
        >
            <div className="pointer-events-none absolute inset-0 opacity-35">
                <div
                    className="absolute inset-0"
                    style={{
                        backgroundImage:
                            'linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px)',
                        backgroundSize: '64px 64px',
                        maskImage: 'linear-gradient(to bottom, rgba(0,0,0,1), transparent 82%)',
                    }}
                />
            </div>

            <div className="relative mx-auto grid min-h-screen max-w-7xl gap-12 px-6 py-8 lg:grid-cols-[minmax(0,1.05fr)_minmax(420px,0.95fr)] lg:px-10 lg:py-10">
                <section className="flex flex-col justify-between">
                    <div>
                        <Link href={HOMEPAGE_PATH} className="inline-flex cursor-pointer items-center gap-3">
                            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,#00D9FF_0%,#00FF88_100%)] shadow-[0_0_28px_rgba(0,217,255,0.28)]">
                                <BrainCircuit className="h-6 w-6 text-slate-950" />
                            </div>
                            <div>
                                <p className="text-lg font-semibold">ML Automation</p>
                                <p className="text-sm text-slate-400">Secure access layer</p>
                            </div>
                        </Link>

                        <div className="mt-16 max-w-2xl">
                            <p
                                className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs uppercase tracking-[0.24em] text-slate-300"
                                style={{ fontFamily: 'var(--font-jetbrains-mono)' }}
                            >
                                <ShieldCheck className="h-3.5 w-3.5 text-cyan-300" />
                                İlk hesap
                            </p>

                            <h1
                                className="mt-8 text-5xl font-semibold tracking-[-0.05em] text-white sm:text-6xl"
                                style={{ fontFamily: 'var(--font-space-grotesk)' }}
                            >
                                <span className="block">İlk hesabını</span>
                                <span className="block text-gradient-primary">kolayca ve güvenle</span>
                                <span className="block">oluştur.</span>
                            </h1>

                            <p className="mt-8 max-w-xl text-base leading-8 text-slate-300 sm:text-lg">
                                Ad soyad, e-posta ve parola bilgilerini gir. Hesabın oluşturulduktan
                                sonra doğrudan panele geçebilirsin.
                            </p>
                        </div>
                    </div>
                </section>

                <section className="flex items-center justify-center">
                    <div className="w-full max-w-xl overflow-hidden rounded-[2rem] border border-white/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.12),rgba(255,255,255,0.04))] p-6 shadow-[0_40px_100px_rgba(3,7,18,0.58)] backdrop-blur-2xl sm:p-8">
                        <div className="border-b border-white/10 pb-6">
                            <div>
                                <p
                                    className="text-xs uppercase tracking-[0.24em] text-cyan-200"
                                    style={{ fontFamily: 'var(--font-jetbrains-mono)' }}
                                >
                                    {modeLabel}
                                </p>
                                <h2 className="mt-3 text-3xl font-semibold text-white">
                                    Yönetici hesabını oluştur
                                </h2>
                            </div>
                        </div>

                        {pageState === 'bootstrap' && (
                            <div className="space-y-4 py-8">
                                <div className="h-12 animate-pulse rounded-2xl bg-white/8" />
                                <div className="h-12 animate-pulse rounded-2xl bg-white/8" />
                                <div className="h-12 animate-pulse rounded-2xl bg-white/8" />
                            </div>
                        )}

                        {pageState === 'ready' && (
                            <div className="mt-6">
                                {requiresSetup ? (
                                    <form className="space-y-4" onSubmit={handleSubmit}>
                                        <label className="block">
                                            <span className="mb-2 block text-sm text-slate-300">Ad soyad</span>
                                            <input
                                                value={fullName}
                                                onChange={(event) => setFullName(event.target.value)}
                                                disabled={isFormDisabled}
                                                className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-white outline-none transition focus:border-cyan-300/50 focus:ring-2 focus:ring-cyan-400/20 disabled:cursor-not-allowed disabled:opacity-60"
                                                placeholder="Örnek: Çağrı Öztürk"
                                                minLength={2}
                                            />
                                        </label>

                                        <label className="block">
                                            <span className="mb-2 block text-sm text-slate-300">E-posta</span>
                                            <input
                                                type="email"
                                                value={email}
                                                onChange={(event) => setEmail(event.target.value)}
                                                disabled={isFormDisabled}
                                                className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-white outline-none transition focus:border-cyan-300/50 focus:ring-2 focus:ring-cyan-400/20 disabled:cursor-not-allowed disabled:opacity-60"
                                                placeholder="ornek@mlautomation.dev"
                                            />
                                        </label>

                                        <label className="block">
                                            <span className="mb-2 block text-sm text-slate-300">Parola</span>
                                            <input
                                                type="password"
                                                value={password}
                                                onChange={(event) => setPassword(event.target.value)}
                                                disabled={isFormDisabled}
                                                minLength={3}
                                                className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-white outline-none transition focus:border-cyan-300/50 focus:ring-2 focus:ring-cyan-400/20 disabled:cursor-not-allowed disabled:opacity-60"
                                                placeholder="En az 3 karakter, büyük/küçük harf ve rakam"
                                            />
                                        </label>

                                        <button
                                            type="submit"
                                            disabled={isFormDisabled}
                                            className="inline-flex w-full cursor-pointer items-center justify-center gap-3 rounded-full bg-[linear-gradient(135deg,#00D9FF_0%,#00FF88_100%)] px-5 py-3.5 text-sm font-semibold text-slate-950 transition-transform duration-300 hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
                                        >
                                            {isSubmitting ? 'İşleniyor...' : 'Kayıt ol'}
                                            <ArrowRight className="h-4 w-4" />
                                        </button>

                                        <p className="text-sm text-slate-400">
                                            Zaten hesabın var mı?{' '}
                                            <Link
                                                href={buildLoginHref(nextPath)}
                                                className="cursor-pointer font-medium text-cyan-200 underline underline-offset-4 transition hover:text-cyan-100"
                                            >
                                                Giriş yap
                                            </Link>
                                        </p>
                                    </form>
                                ) : (
                                    <div className="space-y-5 rounded-[1.5rem] border border-white/10 bg-white/5 p-6">
                                        <h3 className="text-xl font-semibold text-white">
                                            Kayıt kapalı
                                        </h3>
                                        <p className="text-sm leading-7 text-slate-300">
                                            İlk kurulum tamamlanmış. Yeni kayıt yerine giriş ekranını kullanın.
                                        </p>
                                        <Link
                                            href={buildLoginHref(nextPath)}
                                            className="inline-flex cursor-pointer items-center gap-2 text-sm font-medium text-cyan-200 underline underline-offset-4 transition hover:text-cyan-100"
                                        >
                                            Giriş ekranına dön
                                        </Link>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </section>
            </div>
        </div>
    );
}
