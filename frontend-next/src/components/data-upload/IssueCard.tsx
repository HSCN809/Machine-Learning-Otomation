'use client';

import { ChevronDown, ChevronUp, Lightbulb } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';
import { ValidationIssue } from '@/types/data-upload';

interface IssueCardProps {
    issue: ValidationIssue;
}

export function IssueCard({ issue }: IssueCardProps) {
    const [isExpanded, setIsExpanded] = useState(false);

    const hasLLMSuggestion = !!issue.llmSuggestion;

    return (
        <div
            className={cn(
                'rounded-lg border border-white/10 bg-white/5 overflow-hidden transition-all duration-200',
                isExpanded && 'bg-white/10'
            )}
        >
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full px-4 py-3 flex items-center justify-between text-left cursor-pointer hover:bg-white/5"
            >
                <div className="flex-1 min-w-0">
                    <p className="text-sm text-white">
                        {issue.description}
                    </p>
                    {issue.column && (
                        <span className="inline-flex items-center px-2 py-0.5 mt-1 rounded text-xs bg-white/10 text-gray-400">
                            📍 {issue.column}
                        </span>
                    )}
                </div>

                <div className="flex items-center gap-2 ml-3">
                    {hasLLMSuggestion ? (
                        <Lightbulb className="w-4 h-4 text-yellow-400" />
                    ) : (
                        <Lightbulb className="w-4 h-4 text-gray-500" />
                    )}
                    {isExpanded ? (
                        <ChevronUp className="w-4 h-4 text-gray-400" />
                    ) : (
                        <ChevronDown className="w-4 h-4 text-gray-400" />
                    )}
                </div>
            </button>

            {/* Expanded content */}
            {isExpanded && (
                <div className="px-4 pb-3 pt-0 border-t border-white/10">
                    {hasLLMSuggestion ? (
                        <div className="mt-3 p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
                            <p className="text-xs text-cyan-400 mb-1">🤖 AI Önerisi:</p>
                            <p className="text-sm text-gray-300">{issue.llmSuggestion}</p>
                        </div>
                    ) : (
                        <div className="mt-3 p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
                            <p className="text-sm text-cyan-300">
                                ✨ Detaylı AI önerileri almak için yukarıdaki butona tıklayın
                            </p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
