'use client';

import { cn } from '@/lib/utils';
import { theme } from '@/styles/theme';

interface MethodOption {
    value: string;
    label: string;
    description?: string;
    icon?: string;
}

interface MethodSelectorProps {
    label: string;
    options: MethodOption[];
    value: string;
    onChange: (value: string) => void;
    disabled?: boolean;
}

export function MethodSelector({ label, options, value, onChange, disabled = false }: MethodSelectorProps) {
    return (
        <div className="space-y-3">
            <label className="text-sm font-medium text-gray-300">{label}</label>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {options.map((option) => {
                    const isSelected = value === option.value;
                    return (
                        <button
                            key={option.value}
                            onClick={() => onChange(option.value)}
                            disabled={disabled}
                            className={cn(
                                'p-4 rounded-xl border text-left transition-all duration-200',
                                isSelected
                                    ? 'border-cyan-500/50 bg-cyan-500/10'
                                    : 'border-white/10 bg-white/5 hover:border-cyan-500/30 hover:bg-white/10',
                                disabled && 'opacity-50 cursor-not-allowed'
                            )}
                            style={
                                isSelected
                                    ? { boxShadow: `inset 0 0 20px ${theme.colors.primary.cyan}10` }
                                    : undefined
                            }
                        >
                            <div className="flex items-start gap-3">
                                {option.icon && (
                                    <span className="text-xl">{option.icon}</span>
                                )}
                                <div className="flex-1 min-w-0">
                                    <p className={cn(
                                        'font-medium',
                                        isSelected ? 'text-cyan-400' : 'text-white'
                                    )}>
                                        {option.label}
                                    </p>
                                    {option.description && (
                                        <p className="text-sm text-gray-400 mt-1">{option.description}</p>
                                    )}
                                </div>
                                {isSelected && (
                                    <div
                                        className="w-5 h-5 rounded-full flex items-center justify-center"
                                        style={{ background: theme.colors.primary.cyan }}
                                    >
                                        <span className="text-xs text-white">✓</span>
                                    </div>
                                )}
                            </div>
                        </button>
                    );
                })}
            </div>
        </div>
    );
}
