'use client';

import { ModelInfo } from '@/types/model-selection';
import { cn } from '@/lib/utils';
import { Check } from 'lucide-react';

interface ModelCardProps {
    model: ModelInfo;
    isSelected: boolean;
    onToggle: () => void;
    disabled?: boolean;
}

export function ModelCard({ model, isSelected, onToggle, disabled = false }: ModelCardProps) {
    const categoryColors = {
        linear: { bg: 'bg-blue-500/10', border: 'border-blue-500/30', text: 'text-blue-400' },
        tree: { bg: 'bg-green-500/10', border: 'border-green-500/30', text: 'text-green-400' },
        svm: { bg: 'bg-purple-500/10', border: 'border-purple-500/30', text: 'text-purple-400' },
        ensemble: { bg: 'bg-orange-500/10', border: 'border-orange-500/30', text: 'text-orange-400' },
    };

    const categoryLabels = {
        linear: 'Linear',
        tree: 'Tree-based',
        svm: 'SVM',
        ensemble: 'Ensemble',
    };

    const colors = categoryColors[model.category];

    return (
        <button
            onClick={onToggle}
            disabled={disabled}
            className={cn(
                'relative cursor-pointer p-5 rounded-xl border-2 text-left transition-all duration-300',
                'hover:scale-[1.02] hover:shadow-lg',
                isSelected
                    ? 'border-cyan-500 bg-cyan-500/10'
                    : 'border-white/10 bg-white/5 hover:border-cyan-500/30',
                disabled && 'opacity-50 cursor-not-allowed'
            )}
            style={
                isSelected
                    ? { boxShadow: `0 0 20px rgba(0, 217, 255, 0.2)` }
                    : undefined
            }
        >
            {/* Selection indicator */}
            {isSelected && (
                <div className="absolute top-3 right-3 w-6 h-6 rounded-full bg-cyan-500 flex items-center justify-center">
                    <Check className="w-4 h-4 text-white" />
                </div>
            )}

            {/* Icon and title */}
            <div className="flex items-center gap-3 mb-3">
                <span className="text-3xl">{model.icon}</span>
                <div>
                    <h3 className={cn(
                        'font-semibold',
                        isSelected ? 'text-cyan-400' : 'text-white'
                    )}>
                        {model.name}
                    </h3>
                    <span className={cn(
                        'text-xs px-2 py-0.5 rounded-full',
                        colors.bg,
                        colors.text
                    )}>
                        {categoryLabels[model.category]}
                    </span>
                </div>
            </div>

            {/* Description */}
            <p className="text-sm text-gray-400 line-clamp-2">
                {model.description}
            </p>

            {/* Params count */}
            {model.params.length > 0 && (
                <p className="text-xs text-gray-500 mt-3">
                    ⚙️ {model.params.length} ayarlanabilir parametre
                </p>
            )}
        </button>
    );
}
