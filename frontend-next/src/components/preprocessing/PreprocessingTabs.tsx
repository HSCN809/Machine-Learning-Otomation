'use client';

import { cn } from '@/lib/utils';
import { theme } from '@/styles/theme';

interface TabItem<T extends string> {
    id: T;
    label: string;
    description?: string;
    icon?: string;
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
    return (
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
                                    <p className={cn('font-medium', isActive ? 'text-cyan-400' : 'text-white')}>
                                        {tab.label}
                                    </p>
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
    );
}
