'use client';

import { useState } from 'react';
import { cn } from '@/lib/utils';
import { theme } from '@/styles/theme';
import { Info, X } from 'lucide-react';

interface TabItem<T extends string> {
    id: T;
    label: string;
    description?: string;
    icon?: string;
    details?: string;
}

interface PreprocessingTabsProps<T extends string> {
    tabs: TabItem<T>[];
    value: T;
    onChange: (value: T) => void;
    disabled?: boolean;
}

export function PreprocessingTabs<T extends string>({
    tabs,
    value,
    onChange,
    disabled = false,
}: PreprocessingTabsProps<T>) {
    const [activeInfo, setActiveInfo] = useState<TabItem<T> | null>(null);

    const renderInlineMarkdown = (text: string) => {
        const parts = text.split(/(\*\*.*?\*\*)/g);

        return parts.map((part, index) => {
            if (part.startsWith('**') && part.endsWith('**')) {
                return (
                    <strong key={`${part}-${index}`} className="font-semibold text-white">
                        {part.slice(2, -2)}
                    </strong>
                );
            }

            return <span key={`${part}-${index}`}>{part}</span>;
        });
    };

    const renderMarkdown = (content: string) =>
        content.split(/\n\s*\n/).map((paragraph, index) => (
            <p key={`${paragraph}-${index}`} className="text-sm leading-6 text-gray-300">
                {renderInlineMarkdown(paragraph)}
            </p>
        ));

    return (
        <>
            <div className="space-y-3">
                <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-hide">
                {tabs.map((tab) => {
                    const isActive = tab.id === value;

                    return (
                        <button
                            key={tab.id}
                            type="button"
                            onClick={() => onChange(tab.id)}
                            disabled={disabled}
                            className={cn(
                                'min-w-[180px] rounded-2xl border px-4 py-3 text-left transition-all duration-200',
                                isActive
                                    ? 'border-cyan-500/60 bg-cyan-500/10'
                                    : 'border-white/10 bg-white/5 hover:border-cyan-500/30 hover:bg-white/10',
                                disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'
                            )}
                            style={isActive ? { boxShadow: theme.glow.cyan } : undefined}
                        >
                            <div className="flex items-start gap-3">
                                {tab.icon && <span className="text-xl leading-none">{tab.icon}</span>}
                                <div className="min-w-0">
                                    <div className="flex items-center gap-2">
                                        <p className={cn('font-medium', isActive ? 'text-cyan-400' : 'text-white')}>
                                            {tab.label}
                                        </p>
                                        {tab.details && (
                                            <div className="group relative flex items-center">
                                                <button
                                                    type="button"
                                                    aria-label={`${tab.label} hakkında bilgi`}
                                                    onClick={(event) => {
                                                        event.preventDefault();
                                                        event.stopPropagation();
                                                        setActiveInfo(tab);
                                                    }}
                                                    disabled={disabled}
                                                    className={cn(
                                                        'flex h-5 w-5 items-center justify-center rounded-full border transition-all duration-200',
                                                        disabled
                                                            ? 'cursor-not-allowed border-white/10 text-gray-600'
                                                            : 'cursor-pointer border-cyan-400/20 bg-cyan-400/10 text-cyan-300 hover:border-cyan-400/40 hover:bg-cyan-400/15 hover:text-cyan-200'
                                                    )}
                                                >
                                                    <Info className="h-3 w-3" />
                                                </button>
                                                <span className="pointer-events-none absolute bottom-full left-1/2 z-10 mb-2 -translate-x-1/2 whitespace-nowrap rounded-full border border-cyan-400/20 bg-slate-950/95 px-3 py-1 text-[11px] font-medium text-cyan-200 opacity-0 shadow-lg shadow-cyan-500/10 transition-all duration-200 group-hover:opacity-100">
                                                    Bilgi almak için tıklayın
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                    {tab.description && (
                                        <p className="mt-1 text-xs text-gray-400">{tab.description}</p>
                                    )}
                                </div>
                            </div>
                        </button>
                    );
                })}
                </div>
            </div>

            {activeInfo && (
                <div
                    className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 px-4 backdrop-blur-sm"
                    onClick={() => setActiveInfo(null)}
                >
                    <div
                        className="w-full max-w-md rounded-2xl border border-cyan-400/20 bg-[#0D1528]/95 p-6 shadow-2xl"
                        style={{ boxShadow: theme.glow.cyanStrong }}
                        onClick={(event) => event.stopPropagation()}
                    >
                        <div className="flex items-start justify-between gap-4">
                            <div className="flex items-start gap-3">
                                <div className="mt-0.5 flex h-10 w-10 items-center justify-center rounded-xl border border-cyan-400/20 bg-cyan-400/10 text-cyan-300">
                                    <Info className="h-5 w-5" />
                                </div>
                                <div>
                                    <p className="text-xs font-medium uppercase tracking-[0.2em] text-cyan-400/80">
                                        Yöntem Bilgisi
                                    </p>
                                    <h3 className="mt-1 text-lg font-semibold text-white">
                                        {activeInfo.label}
                                    </h3>
                                </div>
                            </div>
                            <button
                                type="button"
                                onClick={() => setActiveInfo(null)}
                                className="flex h-9 w-9 cursor-pointer items-center justify-center rounded-full border border-white/10 bg-white/5 text-gray-300 transition-colors hover:bg-white/10 hover:text-white"
                                aria-label="Bilgi penceresini kapat"
                            >
                                <X className="h-4 w-4" />
                            </button>
                        </div>

                        <div className="mt-5 space-y-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                            {renderMarkdown(activeInfo.details ?? '')}
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
