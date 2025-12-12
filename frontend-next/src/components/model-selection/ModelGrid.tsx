'use client';

import { ModelInfo } from '@/types/model-selection';
import { ModelCard } from './ModelCard';

interface ModelGridProps {
    models: ModelInfo[];
    selectedModels: string[];
    onToggle: (modelId: string) => void;
    disabled?: boolean;
}

export function ModelGrid({ models, selectedModels, onToggle, disabled = false }: ModelGridProps) {
    // Group models by category
    const modelsByCategory = models.reduce((acc, model) => {
        if (!acc[model.category]) acc[model.category] = [];
        acc[model.category].push(model);
        return acc;
    }, {} as Record<string, ModelInfo[]>);

    const categoryLabels = {
        linear: { label: 'Linear Modeller', icon: '📈' },
        tree: { label: 'Tree-based Modeller', icon: '🌲' },
        svm: { label: 'SVM Modeller', icon: '🎯' },
        ensemble: { label: 'Ensemble Modeller', icon: '🔗' },
    };

    const categoryOrder = ['linear', 'tree', 'svm', 'ensemble'];

    return (
        <div className="space-y-6">
            {/* Selection summary */}
            <div className="flex items-center justify-between py-3 px-4 rounded-lg bg-white/5 border border-white/10">
                <span className="text-gray-400">Seçilen model sayısı:</span>
                <span className="font-bold text-cyan-400 text-xl">
                    {selectedModels.length}
                </span>
            </div>

            {/* Models by category */}
            {categoryOrder.map(category => {
                const categoryModels = modelsByCategory[category];
                if (!categoryModels || categoryModels.length === 0) return null;

                const categoryInfo = categoryLabels[category as keyof typeof categoryLabels];

                return (
                    <div key={category}>
                        <h3 className="text-sm font-medium text-gray-400 mb-3 flex items-center gap-2">
                            <span>{categoryInfo.icon}</span>
                            {categoryInfo.label}
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {categoryModels.map(model => (
                                <ModelCard
                                    key={model.id}
                                    model={model}
                                    isSelected={selectedModels.includes(model.id)}
                                    onToggle={() => onToggle(model.id)}
                                    disabled={disabled}
                                />
                            ))}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
