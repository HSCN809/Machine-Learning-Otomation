interface FullPageLoadingProps {
    label?: string;
    description?: string;
}

export function FullPageLoading({
    label = 'Sayfa yükleniyor',
    description = 'Veriler hazırlanıyor.',
}: FullPageLoadingProps) {
    return (
        <div className="flex min-h-screen items-center justify-center overflow-hidden bg-[#07101f] px-6">
            <div className="w-full max-w-md text-center">
                <div className="mx-auto mb-8 grid h-24 w-24 place-items-center rounded-full border border-cyan-300/20 bg-white/[0.03] shadow-[0_0_40px_rgba(0,217,255,0.16)]">
                    <div className="relative h-16 w-16">
                        <div className="absolute inset-0 rounded-full border-2 border-cyan-300/20" />
                        <div className="absolute inset-0 animate-spin rounded-full border-2 border-transparent border-t-cyan-300 border-r-emerald-300" />
                        <div className="absolute inset-4 rounded-full bg-cyan-300/10 shadow-[0_0_24px_rgba(0,217,255,0.22)]" />
                    </div>
                </div>

                <div className="space-y-3">
                    <p className="text-base font-semibold text-white">{label}</p>
                    <p className="text-sm text-slate-400">{description}</p>
                </div>

                <div className="mt-8 grid grid-cols-4 gap-2">
                    {Array.from({ length: 4 }).map((_, index) => (
                        <div
                            key={index}
                            className="h-1.5 animate-pulse rounded-full bg-cyan-300/40"
                            style={{ animationDelay: `${index * 160}ms` }}
                        />
                    ))}
                </div>
            </div>
        </div>
    );
}

