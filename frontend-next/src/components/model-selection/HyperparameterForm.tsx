'use client';

import { useState } from 'react';
import { ModelInfo, ModelParameter } from '@/types/model-selection';
import { theme } from '@/styles/theme';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';

interface HyperparameterFormProps {
    models: ModelInfo[];
    selectedModels: string[];
    params: Record<string, Record<string, unknown>>;
    onUpdateParams: (modelId: string, params: Record<string, unknown>) => void;
}

export function HyperparameterForm({
    models,
    selectedModels,
    params,
    onUpdateParams,
}: HyperparameterFormProps) {
    const [expandedModel, setExpandedModel] = useState<string | null>(
        selectedModels[0] || null
    );

    const selectedModelInfos = models.filter(m => selectedModels.includes(m.id));

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
                        className="w-full px-3 py-2 rounded-lg border border-white/10 bg-white/5 text-white outline-none focus:border-cyan-500/50"
                    />
                );
            case 'select':
                return (
                    <select
                        value={currentValue as string}
                        onChange={(e) => onUpdateParams(model.id, { [param.name]: e.target.value })}
                        className="w-full px-3 py-2 rounded-lg border border-white/10 bg-white/5 text-white outline-none focus:border-cyan-500/50"
                    >
                        {param.options?.map(opt => (
                            <option key={opt.value} value={opt.value} className="bg-gray-800">
                                {opt.label}
                            </option>
                        ))}
                    </select>
                );
            case 'boolean':
                return (
                    <label className="flex items-center gap-2 cursor-pointer">
                        <input
                            type="checkbox"
                            checked={currentValue as boolean}
                            onChange={(e) => onUpdateParams(model.id, { [param.name]: e.target.checked })}
                            className="w-4 h-4 rounded border-white/30 bg-white/5"
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
            <div className="p-6 rounded-xl border border-white/10 bg-white/5 text-center">
                <p className="text-gray-400">Hiçbir model seçilmedi</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <p className="text-sm text-gray-400">
                💡 Parametreleri varsayılan değerlerde bırakabilir veya özelleştirebilirsiniz.
            </p>

            {selectedModelInfos.map((model) => {
                const isExpanded = expandedModel === model.id;
                const hasParams = model.params.length > 0;

                return (
                    <div
                        key={model.id}
                        className="rounded-xl border border-white/10 overflow-hidden"
                    >
                        {/* Header */}
                        <button
                            onClick={() => setExpandedModel(isExpanded ? null : model.id)}
                            className="w-full flex items-center justify-between px-4 py-3 bg-white/5 hover:bg-white/10 transition-colors"
                        >
                            <div className="flex items-center gap-3">
                                <span className="text-xl">{model.icon}</span>
                                <span className="font-medium text-white">{model.name}</span>
                                {!hasParams && (
                                    <span className="text-xs px-2 py-0.5 rounded bg-gray-500/20 text-gray-400">
                                        Parametre yok
                                    </span>
                                )}
                            </div>
                            {hasParams && (
                                isExpanded ? (
                                    <ChevronUp className="w-5 h-5 text-gray-400" />
                                ) : (
                                    <ChevronDown className="w-5 h-5 text-gray-400" />
                                )
                            )}
                        </button>

                        {/* Parameters */}
                        {isExpanded && hasParams && (
                            <div className="p-4 border-t border-white/10 space-y-4">
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
}
