'use client';

import { Check } from 'lucide-react';
import { ModelInfo } from '@/types/model-selection';
import { cn } from '@/lib/utils';

interface ModelCardProps {
    model: ModelInfo;
    isSelected: boolean;
    onToggle: () => void;
    disabled?: boolean;
}

export function ModelCard({ model, isSelected, onToggle, disabled = false }: ModelCardProps) {
    const categoryColors = {
        linear: { bg: 'bg-blue-500/10', text: 'text-blue-400' },
        tree: { bg: 'bg-green-500/10', text: 'text-green-400' },
        svm: { bg: 'bg-purple-500/10', text: 'text-purple-400' },
        ensemble: { bg: 'bg-orange-500/10', text: 'text-orange-400' },
    };

    const categoryLabels = {
        linear: 'Lineer',
        tree: 'Ağaç',
        svm: 'SVM',
        ensemble: 'Topluluk',
    };

    const colors = categoryColors[model.category];

    return (
        <button
            onClick={onToggle}
            disabled={disabled}
            className={cn(
                'relative rounded-xl border-2 p-5 text-left transition-all duration-300',
                'hover:scale-[1.02] hover:shadow-lg',
                isSelected
                    ? 'border-cyan-500 bg-cyan-500/10'
                    : 'border-white/10 bg-white/5 hover:border-cyan-500/30',
                disabled && 'cursor-not-allowed opacity-50',
                !disabled && 'cursor-pointer'
            )}
            style={isSelected ? { boxShadow: '0 0 20px rgba(0, 217, 255, 0.2)' } : undefined}
        >
            {isSelected && (
                <div className="absolute right-3 top-3 flex h-6 w-6 items-center justify-center rounded-full bg-cyan-500">
                    <Check className="h-4 w-4 text-white" />
                </div>
            )}

            <div className="mb-3 flex items-center gap-3">
                <span className="text-3xl">{model.icon}</span>
                <div>
                    <h3 className={cn('font-semibold', isSelected ? 'text-cyan-400' : 'text-white')}>
                        {model.name}
                    </h3>
                    <span className={cn('rounded-full px-2 py-0.5 text-xs', colors.bg, colors.text)}>
                        {categoryLabels[model.category]}
                    </span>
                </div>
            </div>

            <p className="line-clamp-2 text-sm text-gray-400">{model.description}</p>

            {model.params.length > 0 && (
                <p className="mt-3 text-xs text-gray-500">⚙️ {model.params.length} ayarlanabilir parametre</p>
            )}
        </button>
    );
}
