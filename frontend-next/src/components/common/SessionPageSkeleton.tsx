'use client';

type SessionPageSkeletonVariant = 'analytics' | 'wizard' | 'upload';

interface SessionPageSkeletonProps {
    variant?: SessionPageSkeletonVariant;
}

function SkeletonBlock({ className }: { className: string }) {
    return <div className={`animate-pulse rounded-2xl border border-white/10 bg-white/5 ${className}`} />;
}

export function SessionPageSkeleton({
    variant = 'analytics',
}: SessionPageSkeletonProps) {
    if (variant === 'upload') {
        return (
            <div className="space-y-8">
                <SkeletonBlock className="h-72 w-full" />
                <SkeletonBlock className="h-56 w-full" />
            </div>
        );
    }

    if (variant === 'wizard') {
        return (
            <div className="space-y-6">
                <div className="grid grid-cols-5 gap-4">
                    {Array.from({ length: 5 }).map((_, index) => (
                        <SkeletonBlock key={index} className="h-20 w-full rounded-xl" />
                    ))}
                </div>
                <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
                    <SkeletonBlock className="h-[560px] w-full lg:col-span-2" />
                    <SkeletonBlock className="h-[560px] w-full lg:col-span-1" />
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-4 gap-4">
                {Array.from({ length: 4 }).map((_, index) => (
                    <SkeletonBlock key={index} className="h-20 w-full rounded-xl" />
                ))}
            </div>
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <SkeletonBlock className="h-72 w-full" />
                <SkeletonBlock className="h-72 w-full" />
            </div>
            <SkeletonBlock className="h-96 w-full" />
        </div>
    );
}
