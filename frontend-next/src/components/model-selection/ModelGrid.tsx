'use client';

import { ModelInfo } from '@/types/model-selection';
import { ModelCard } from './ModelCard';

interface ModelGridProps {
    models: ModelInfo[];
    selectedModels: string[];
    onToggle: (modelId: string) => void;
    disabled?: boolean;
}

import React from 'react';

export const ModelGrid = React.memo(function ModelGrid({ models, selectedModels, onToggle, disabled = false }: ModelGridProps) {
    const modelsByCategory = models.reduce((acc, model) => {
        if (!acc[model.category]) acc[model.category] = [];
        acc[model.category].push(model);
        return acc;
    }, {} as Record<string, ModelInfo[]>);

    const categoryLabels = {
        linear: { label: 'Lineer Modeller', icon: '📈' },
        tree: { label: 'Ağaç Tabanlı Modeller', icon: '🌲' },
        svm: { label: 'SVM Modelleri', icon: '🎯' },
        ensemble: { label: 'Topluluk Modelleri', icon: '🔗' },
    };

    const categoryOrder = ['linear', 'tree', 'svm', 'ensemble'];

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between rounded-lg border border-white/10 bg-white/5 px-4 py-3">
                <span className="text-gray-400">Seçilen model sayısı:</span>
                <span className="text-xl font-bold text-cyan-400">{selectedModels.length}</span>
            </div>

            {categoryOrder.map((category) => {
                const categoryModels = modelsByCategory[category];
                if (!categoryModels || categoryModels.length === 0) return null;

                const categoryInfo = categoryLabels[category as keyof typeof categoryLabels];

                return (
                    <div key={category}>
                        <h3 className="mb-3 flex items-center gap-2 text-sm font-medium text-gray-400">
                            <span>{categoryInfo.icon}</span>
                            {categoryInfo.label}
                        </h3>
                        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                            {categoryModels.map((model) => (
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
});
