'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { ModelInfo, ModelParameter } from '@/types/model-selection';

interface HyperparameterFormProps {
    models: ModelInfo[];
    selectedModels: string[];
    params: Record<string, Record<string, unknown>>;
    onUpdateParams: (modelId: string, params: Record<string, unknown>) => void;
}

import React from 'react';

export const HyperparameterForm = React.memo(function HyperparameterForm({
    models,
    selectedModels,
    params,
    onUpdateParams,
}: HyperparameterFormProps) {
    const [expandedModel, setExpandedModel] = useState<string | null>(selectedModels[0] || null);
    const selectedModelInfos = models.filter((model) => selectedModels.includes(model.id));

    const renderParamInput = (model: ModelInfo, param: ModelParameter) => {
        const currentValue = params[model.id]?.[param.name] ?? param.default;

        switch (param.type) {
            case 'number':
            case 'range':
                return (
                    <input
                        type="number"
                        value={currentValue as number}
                        onChange={(e) => onUpdateParams(model.id, { [param.name]: parseFloat(e.target.value) })}
                        min={param.min}
                        max={param.max}
                        step={param.step}
                        className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white outline-none focus:border-cyan-500/50"
                    />
                );
            case 'select':
                return (
                    <select
                        value={currentValue as string}
                        onChange={(e) => onUpdateParams(model.id, { [param.name]: e.target.value })}
                        className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white outline-none focus:border-cyan-500/50"
                    >
                        {param.options?.map((option) => (
                            <option key={option.value} value={option.value} className="bg-gray-800">
                                {option.label}
                            </option>
                        ))}
                    </select>
                );
            case 'boolean':
                return (
                    <label className="flex cursor-pointer items-center gap-2">
                        <input
                            type="checkbox"
                            checked={currentValue as boolean}
                            onChange={(e) => onUpdateParams(model.id, { [param.name]: e.target.checked })}
                            className="h-4 w-4 rounded border-white/30 bg-white/5"
                        />
                        <span className="text-sm text-gray-400">Aktif</span>
                    </label>
                );
            default:
                return null;
        }
    };

    if (selectedModelInfos.length === 0) {
        return (
            <div className="rounded-xl border border-white/10 bg-white/5 p-6 text-center">
                <p className="text-gray-400">Hiçbir model seçilmedi</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <p className="text-sm text-gray-400">
                Parametreleri varsayılan değerlerde bırakabilir veya özelleştirebilirsiniz.
            </p>

            {selectedModelInfos.map((model) => {
                const isExpanded = expandedModel === model.id;
                const hasParams = model.params.length > 0;

                return (
                    <div key={model.id} className="overflow-hidden rounded-xl border border-white/10">
                        <button
                            onClick={() => setExpandedModel(isExpanded ? null : model.id)}
                            className="flex w-full cursor-pointer items-center justify-between bg-white/5 px-4 py-3 transition-colors hover:bg-white/10"
                        >
                            <div className="flex items-center gap-3">
                                <span className="text-xl">{model.icon}</span>
                                <span className="font-medium text-white">{model.name}</span>
                                {!hasParams && (
                                    <span className="rounded bg-gray-500/20 px-2 py-0.5 text-xs text-gray-400">
                                        Parametre yok
                                    </span>
                                )}
                            </div>
                            {hasParams &&
                                (isExpanded ? (
                                    <ChevronUp className="h-5 w-5 text-gray-400" />
                                ) : (
                                    <ChevronDown className="h-5 w-5 text-gray-400" />
                                ))}
                        </button>

                        {isExpanded && hasParams && (
                            <div className="space-y-4 border-t border-white/10 p-4">
                                {model.params.map((param) => (
                                    <div key={param.name} className="space-y-2">
                                        <div className="flex items-center justify-between">
                                            <label className="text-sm font-medium text-gray-300">
                                                {param.label}
                                            </label>
                                            {param.min !== undefined && param.max !== undefined && (
                                                <span className="text-xs text-gray-500">
                                                    {param.min} - {param.max}
                                                </span>
                                            )}
                                        </div>
                                        {renderParamInput(model, param)}
                                        {param.description && (
                                            <p className="text-xs text-gray-500">{param.description}</p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                );
            })}
        </div>
    );
});
