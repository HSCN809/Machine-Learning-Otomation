'use client';

import { type ReactNode, useState } from 'react';
import { Info, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { theme } from '@/styles/theme';

interface MethodOption {
    value: string;
    label: string;
    description?: string;
    icon?: string;
    details?: string;
    badgeLabel?: string;
    badgeTone?: 'numeric' | 'categorical' | 'mixed';
}

interface MethodSelectorProps {
    label: string;
    options: MethodOption[];
    value: string;
    onChange: (value: string) => void;
    disabled?: boolean;
    headerContent?: ReactNode;
}

function renderInlineMarkdown(text: string) {
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
}

function renderMarkdown(content: string) {
    return content.split(/\n\s*\n/).map((paragraph, index) => (
        <p key={`${paragraph}-${index}`} className="text-sm leading-6 text-gray-300">
            {renderInlineMarkdown(paragraph)}
        </p>
    ));
}

export function MethodSelector({
    label,
    options,
    value,
    onChange,
    disabled = false,
    headerContent,
}: MethodSelectorProps) {
    const [activeInfo, setActiveInfo] = useState<MethodOption | null>(null);

    return (
        <>
            <div className="space-y-3">
                <label className="text-lg font-semibold text-white">{label}</label>
                {headerContent}
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {options.map((option) => {
                    const isSelected = value === option.value;
                    const badgeClassName =
                        option.badgeTone === 'numeric'
                            ? 'border-cyan-400/30 bg-cyan-400/10 text-cyan-200'
                            : option.badgeTone === 'categorical'
                              ? 'border-violet-400/30 bg-violet-400/10 text-violet-200'
                              : 'border-emerald-400/30 bg-emerald-400/10 text-emerald-200';
                    return (
                        <div
                            key={option.value}
                            role="button"
                            tabIndex={disabled ? -1 : 0}
                            onClick={() => {
                                if (!disabled) {
                                    onChange(option.value);
                                }
                            }}
                            onKeyDown={(event) => {
                                if (disabled) return;
                                if (event.key === 'Enter' || event.key === ' ') {
                                    event.preventDefault();
                                    onChange(option.value);
                                }
                            }}
                            aria-disabled={disabled}
                            className={cn(
                                'relative rounded-xl border p-4 text-left transition-all duration-200',
                                isSelected
                                    ? 'border-cyan-500/50 bg-cyan-500/10'
                                    : 'border-white/10 bg-white/5 hover:border-cyan-500/30 hover:bg-white/10',
                                disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer',
                                option.badgeLabel ? 'pr-24' : undefined
                            )}
                            style={
                                isSelected
                                    ? { boxShadow: `inset 0 0 20px ${theme.colors.primary.cyan}10` }
                                    : undefined
                            }
                        >
                            {option.badgeLabel && (
                                <span
                                    className={cn(
                                        'absolute right-3 top-3 rounded-full border px-2.5 py-1 text-[11px] font-medium tracking-[0.02em]',
                                        badgeClassName
                                    )}
                                >
                                    {option.badgeLabel}
                                </span>
                            )}
                            <div className="flex items-start gap-3">
                                {option.icon && (
                                    <span className="text-xl">{option.icon}</span>
                                )}
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                        <p className={cn(
                                            'font-medium',
                                            isSelected ? 'text-cyan-400' : 'text-white'
                                        )}>
                                            {option.label}
                                        </p>
                                        {isSelected && (
                                            <span
                                                className="flex h-5 w-5 items-center justify-center rounded-full text-xs text-white"
                                                style={{ background: theme.colors.primary.cyan }}
                                            >
                                                ✓
                                            </span>
                                        )}
                                        {option.details && (
                                            <div className="group relative flex items-center">
                                                <button
                                                    type="button"
                                                    aria-label={`${option.label} hakkında bilgi`}
                                                    onClick={(event) => {
                                                        event.preventDefault();
                                                        event.stopPropagation();
                                                        setActiveInfo(option);
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
                                    {option.description && (
                                        <p className="text-sm text-gray-400 mt-1">{option.description}</p>
                                    )}
                                </div>
                                {isSelected && (
                                    <div
                                        className="hidden"
                                        style={{ background: theme.colors.primary.cyan }}
                                    >
                                        <span className="text-xs text-white">✓</span>
                                    </div>
                                )}
                            </div>
                        </div>
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
